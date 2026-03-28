from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.db_manager import get_db

from database.models import UserPreference


router = APIRouter(prefix="/language", tags=["Language Settings"])

class LanguageRequest(BaseModel):
    telegram_user_id: str
    language: str  # hi, en, pa, bn, etc.

class LocationRequest(BaseModel):
    telegram_user_id: str
    location: str

@router.post("/set-language")
async def set_language(request: LanguageRequest, db: Session = Depends(get_db)):
    """
    Feature 3: Set user's preferred language
    """
    
    # Check if user exists
    user_pref = db.query(UserPreference).filter(
        UserPreference.telegram_user_id == request.telegram_user_id
    ).first()
    
    if user_pref:
        # Update existing
        user_pref.preferred_language = request.language
    else:
        # Create new
        user_pref = UserPreference(
            telegram_user_id=request.telegram_user_id,
            preferred_language=request.language
        )
        db.add(user_pref)
    
    db.commit()
    db.refresh(user_pref)
    
    return {
        "success": True,
        "message": f"Language set to {request.language}",
        "user_id": request.telegram_user_id
    }

@router.post("/set-location")
async def set_location(request: LocationRequest, db: Session = Depends(get_db)):
    """Set user location for weather"""
    
    user_pref = db.query(UserPreference).filter(
        UserPreference.telegram_user_id == request.telegram_user_id
    ).first()
    
    if user_pref:
        user_pref.location = request.location
    else:
        user_pref = UserPreference(
            telegram_user_id=request.telegram_user_id,
            location=request.location
        )
        db.add(user_pref)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Location set to {request.location}"
    }

@router.get("/preferences/{telegram_user_id}")
async def get_preferences(telegram_user_id: str, db: Session = Depends(get_db)):
    """Get user preferences"""
    
    user_pref = db.query(UserPreference).filter(
        UserPreference.telegram_user_id == telegram_user_id
    ).first()
    
    if not user_pref:
        raise HTTPException(404, "User preferences not found")
    
    return {
        "telegram_user_id": user_pref.telegram_user_id,
        "language": user_pref.preferred_language,
        "location": user_pref.location,
        "advisory_enabled": user_pref.advisory_enabled
    }