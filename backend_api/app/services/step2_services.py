from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.step2_models import (
    ProfessionalAvailability, ProfessionalTimeBlock, Appointment,
    AppointmentStatusHistory, ProfessionalPublicProfile
)
from app.models.professional import Professional, OnboardingStatus, ProfessionalStatus

VALID_TRANSITIONS = {
    "pending_confirmation": ["confirmed", "cancelled_by_patient", "cancelled_by_professional"],
    "confirmed": ["completed", "cancelled_by_patient", "cancelled_by_professional", "no_show_patient", "no_show_professional"],
}

class SlotService:
    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        professional_id: str,
        date: str,
        modality_code: str
    ) -> List[dict]:
        weekday = datetime.strptime(date, "%Y-%m-%d").weekday()
        
        avail_result = await db.execute(
            select(ProfessionalAvailability).where(
                and_(
                    ProfessionalAvailability.professional_id == professional_id,
                    ProfessionalAvailability.weekday == weekday,
                    ProfessionalAvailability.modality_code == modality_code,
                    ProfessionalAvailability.status == "active",
                    ProfessionalAvailability.deleted_at.is_(None)
                )
            )
        )
        avail = avail_result.scalar_one_or_none()
        if not avail:
            return []
        
        blocks_result = await db.execute(
            select(ProfessionalTimeBlock).where(
                and_(
                    ProfessionalTimeBlock.professional_id == professional_id,
                    ProfessionalTimeBlock.starts_at <= datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S"),
                    ProfessionalTimeBlock.ends_at >= datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S"),
                    ProfessionalTimeBlock.deleted_at.is_(None)
                )
            )
        )
        blocks = blocks_result.scalars().all()
        
        appointments_result = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.professional_id == professional_id,
                    Appointment.scheduled_start >= datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S"),
                    Appointment.scheduled_end <= datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S"),
                    Appointment.status.in_(["pending_confirmation", "confirmed"]),
                    Appointment.deleted_at.is_(None)
                )
            )
        )
        booked = appointments_result.scalars().all()
        
        slots = []
        start_dt = datetime.strptime(f"{date} {avail.start_time}", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{date} {avail.end_time}", "%Y-%m-%d %H:%M:%S")
        
        while start_dt + timedelta(minutes=avail.slot_minutes) <= end_dt:
            slot_end = start_dt + timedelta(minutes=avail.slot_minutes)
            
            blocked = any(b.starts_at <= start_dt and b.ends_at >= slot_end for b in blocks)
            occupied = any(a.scheduled_start <= start_dt and a.scheduled_end >= slot_end for a in booked)
            
            slots.append({
                "start": start_dt,
                "end": slot_end,
                "is_available": not blocked and not occupied
            })
            start_dt = slot_end
        
        return slots

class AppointmentService:
    @staticmethod
    async def create_appointment(
        db: AsyncSession,
        patient_id: str,
        professional_id: str,
        modality_code: str,
        scheduled_start: datetime,
        patient_note: Optional[str] = None
    ) -> Appointment:
        prof_result = await db.execute(
            select(Professional).where(Professional.id == professional_id)
        )
        prof = prof_result.scalar_one_or_none()
        if not prof or prof.status != ProfessionalStatus.ACTIVE or prof.onboarding_status != OnboardingStatus.APPROVED:
            raise ValueError("Professional not available for booking")
        
        avail_result = await db.execute(
            select(ProfessionalAvailability).where(
                and_(
                    ProfessionalAvailability.professional_id == professional_id,
                    ProfessionalAvailability.modality_code == modality_code,
                    ProfessionalAvailability.status == "active",
                    ProfessionalAvailability.deleted_at.is_(None)
                )
            )
        )
        avail = avail_result.scalar_one_or_none()
        if not avail:
            raise ValueError("No availability for this modality")
        
        scheduled_end = scheduled_start + timedelta(minutes=avail.slot_minutes)
        
        existing = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.professional_id == professional_id,
                    Appointment.scheduled_start == scheduled_start,
                    Appointment.status.in_(["pending_confirmation", "confirmed"]),
                    Appointment.deleted_at.is_(None)
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Slot already taken")
        
        appointment = Appointment(
            public_code=f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            patient_id=patient_id,
            professional_id=professional_id,
            modality_code=modality_code,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            status="pending_confirmation",
            patient_note=patient_note,
            created_from="patient_app"
        )
        db.add(appointment)
        await db.flush()
        
        history = AppointmentStatusHistory(
            appointment_id=appointment.id,
            old_status=None,
            new_status="pending_confirmation",
            changed_by_user_id=patient_id
        )
        db.add(history)
        await db.commit()
        
        return appointment
    
    @staticmethod
    async def transition_appointment(
        db: AsyncSession,
        appointment_id: str,
        new_status: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> Appointment:
        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        apt = result.scalar_one_or_none()
        if not apt:
            raise ValueError("Appointment not found")
        
        allowed = VALID_TRANSITIONS.get(apt.status, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid transition from {apt.status} to {new_status}")
        
        old_status = apt.status
        apt.status = new_status
        
        if new_status == "cancelled_by_patient":
            apt.cancellation_reason = reason
        elif new_status == "cancelled_by_professional":
            apt.cancellation_reason = reason
        
        history = AppointmentStatusHistory(
            appointment_id=apt.id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=user_id,
            reason=reason
        )
        db.add(history)
        await db.commit()
        
        return apt