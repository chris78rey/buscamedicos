from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

class UserResponse(BaseModel):
    id: str
    email: str
    is_email_verified: bool
    status: str
    
    class Config:
        from_attributes = True

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me")
async def update_me(data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    for key, value in data.items():
        if hasattr(current_user, key) and key not in ["id", "email", "password_hash"]:
            setattr(current_user, key, value)
    
    await db.commit()
    return current_user