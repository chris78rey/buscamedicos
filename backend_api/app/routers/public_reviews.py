from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.professional import Professional
from app.models.step6_models import ReviewVisibility, ReviewStatus
from app.services.step6_services import ReviewService, ReputationService, ModerationAuditService

router = APIRouter()


@router.get("/professionals/{public_slug}/reviews", response_model=List[dict])
async def get_public_reviews(
    public_slug: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Professional).where(Professional.public_slug == public_slug)
    )
    professional = result.scalar_one_or_none()
    if not professional:
        return []

    service = ReviewService(db)
    reviews = await service.get_public_reviews(str(professional.id))

    person_result = await db.execute(
        select(Professional).where(Professional.id == str(professional.id))
    )

    return [
        {
            "id": r.id,
            "rating_overall": r.rating_overall,
            "rating_punctuality": r.rating_punctuality,
            "rating_communication": r.rating_communication,
            "rating_respect": r.rating_respect,
            "comment_text": r.comment_text,
            "reviewer_name_abbrev": "P.",  # simplified, real impl would fetch person name
            "created_at": r.created_at
        }
        for r in reviews
    ]


@router.get("/professionals/{public_slug}/rating-summary")
async def get_rating_summary(
    public_slug: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Professional).where(Professional.public_slug == public_slug)
    )
    professional = result.scalar_one_or_none()
    if not professional:
        return {
            "professional_id": None,
            "public_reviews_count": 0,
            "avg_overall": 0.0,
            "avg_punctuality": None,
            "avg_communication": None,
            "avg_respect": None
        }

    rep_service = ReputationService(db)
    stats = await rep_service.get_reputation(str(professional.id))

    if not stats:
        return {
            "professional_id": str(professional.id),
            "public_reviews_count": 0,
            "avg_overall": 0.0,
            "avg_punctuality": None,
            "avg_communication": None,
            "avg_respect": None
        }

    return {
        "professional_id": str(professional.id),
        "public_reviews_count": stats.public_reviews_count,
        "avg_overall": float(stats.avg_overall or 0),
        "avg_punctuality": float(stats.avg_punctuality) if stats.avg_punctuality else None,
        "avg_communication": float(stats.avg_communication) if stats.avg_communication else None,
        "avg_respect": float(stats.avg_respect) if stats.avg_respect else None
    }
