from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.professional import Professional, OnboardingStatus, ProfessionalStatus
from app.models.person import Person
from app.models.professional_document import ProfessionalDocument, DocumentType, ReviewStatus

router = APIRouter()

class ProfessionalResponse(BaseModel):
    id: str
    professional_type: Optional[str]
    public_display_name: Optional[str]
    onboarding_status: str
    is_public_profile_enabled: bool
    status: str
    
    class Config:
        from_attributes = True

@router.get("/me", response_model=ProfessionalResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    return professional

@router.patch("/me")
async def update_me(data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    for key, value in data.items():
        if hasattr(professional, key) and key not in ["id", "user_id", "person_id"]:
            setattr(professional, key, value)
    
    await db.commit()
    return professional

@router.post("/me/documents")
async def upload_document(
    document_type: DocumentType,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    import hashlib
    import uuid as uuid_lib
    content = await file.read()
    sha256_hash = hashlib.sha256(content).hexdigest()
    
    file_id = str(uuid_lib.uuid4())
    
    doc = ProfessionalDocument(
        professional_id=professional.id,
        document_type=document_type,
        file_id=file_id,
        original_filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        sha256=sha256_hash
    )
    db.add(doc)
    await db.commit()
    
    return {"id": doc.id, "document_type": document_type, "status": "uploaded"}

@router.get("/me/documents")
async def list_documents(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    docs_result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.professional_id == professional.id,
            ProfessionalDocument.deleted_at.is_(None)
        )
    )
    return docs_result.scalars().all()

@router.delete("/me/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    doc_result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.id == doc_id,
            ProfessionalDocument.professional_id == professional.id
        )
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    from datetime import datetime
    doc.deleted_at = datetime.utcnow()
    doc.deleted_by = current_user.id
    await db.commit()
    
    return {"status": "deleted"}

@router.post("/me/submit-verification")
async def submit_verification(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.verification import VerificationRequest, VerificationRequestStatus
    
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    if professional.onboarding_status not in [OnboardingStatus.DRAFT, OnboardingStatus.NEEDS_CORRECTION]:
        raise HTTPException(status_code=400, detail="Cannot submit from current status")
    
    professional.onboarding_status = OnboardingStatus.SUBMITTED
    professional.status = ProfessionalStatus.PENDING_REVIEW
    
    verification = VerificationRequest(
        professional_id=professional.id,
        status=VerificationRequestStatus.SUBMITTED
    )
    db.add(verification)
    await db.commit()
    
    return {"status": "submitted", "verification_id": verification.id}