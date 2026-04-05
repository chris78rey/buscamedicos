from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/me")
async def get_current_file_access(current_user: User = Depends(get_current_user)):
    return {"file_access": "configured"}