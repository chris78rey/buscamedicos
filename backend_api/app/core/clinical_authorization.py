from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.step2_models import Appointment


async def get_appointment_with_clinical_check(
    appointment_id: str,
    current_user: User,
    db: AsyncSession,
    require_paid: bool = True
) -> Appointment:
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt or appt.deleted_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    
    await current_user.awaitable_attrs.roles
    role_codes = [r.code for r in current_user.roles]
    
    is_patient = str(current_user.id) == str(appt.patient_id)
    is_professional = str(current_user.id) == str(appt.professional_id)
    is_admin = any(r in role_codes for r in ["super_admin", "admin_validation", "admin_support"])
    
    if not is_patient and not is_professional and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this appointment")
    
    if require_paid:
        if not hasattr(appt, 'financial_status') or appt.financial_status != "paid":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment must be paid")
    
    return appt


async def require_clinical_relationship(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_appointment_with_clinical_check(appointment_id, current_user, db, require_paid=True)


async def require_professional_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await get_appointment_with_clinical_check(appointment_id, current_user, db, require_paid=True)
    await current_user.awaitable_attrs.roles
    role_codes = [r.code for r in current_user.roles]
    if not any(r in role_codes for r in ["professional"]) and str(current_user.id) != str(appt.professional_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the assigned professional can perform this action")
    return appt


async def require_patient_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await get_appointment_with_clinical_check(appointment_id, current_user, db, require_paid=False)
    await current_user.awaitable_attrs.roles
    role_codes = [r.code for r in current_user.roles]
    if not any(r in role_codes for r in ["patient"]) and str(current_user.id) != str(appt.patient_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the assigned patient can perform this action")
    return appt


def forbid_admin_clinical_access(current_user: User):
    async def checker():
        await current_user.awaitable_attrs.roles
        role_codes = [r.code for r in current_user.roles]
        if any(r in role_codes for r in ["super_admin", "admin_validation", "admin_support"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin cannot access clinical content")
        return current_user
    return checker
