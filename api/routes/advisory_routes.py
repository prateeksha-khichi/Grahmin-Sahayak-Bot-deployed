from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db_manager import get_db

from database.models import UserPreference


from services.advisory_service import AdvisoryService
from services.gtts_service import GTTsService
from services.translation_service import TranslationService
from services.telegram_service import TelegramService

router = APIRouter(prefix="/advisory", tags=["Daily Advisory"])

advisory_service = AdvisoryService()
translation_service = TranslationService()
gtts_service = GTTsService()
telegram_service = TelegramService()


@router.post("/send/{telegram_user_id}")
async def send_advisory(telegram_user_id: str, db: Session = Depends(get_db)):

    # Get user preferences
    user_pref = db.query(UserPreference).filter(
        UserPreference.telegram_user_id == telegram_user_id
    ).first()

    if not user_pref:
        raise HTTPException(status_code=404, detail="User not found. Set preferences first.")

    if not user_pref.advisory_enabled:
        return {"message": "Advisory disabled for this user"}

    # Generate advisory
    location = user_pref.location or "Delhi"

    advisory_text = await advisory_service.generate_daily_advisory(
        telegram_user_id,
        location
    )

    # Translate
    translated_text = translation_service.translate(
        advisory_text,
        user_pref.preferred_language or "hi"
    )

    # Convert to audio
    audio_path = gtts_service.text_to_speech(translated_text)

    # Send telegram audio
    await telegram_service.send_audio(
        telegram_user_id,
        audio_path,
        "🌅 आज की सलाह"
    )

    return {
        "success": True,
        "message": "Daily advisory sent",
        "user_id": telegram_user_id,
        "audio_path": audio_path
    }


@router.post("/toggle/{telegram_user_id}")
async def toggle_advisory(
    telegram_user_id: str,
    enabled: bool,
    db: Session = Depends(get_db)
):

    user_pref = db.query(UserPreference).filter(
        UserPreference.telegram_user_id == telegram_user_id
    ).first()

    if not user_pref:
        raise HTTPException(status_code=404, detail="User not found")

    user_pref.advisory_enabled = enabled
    db.commit()

    return {
        "success": True,
        "advisory_enabled": enabled
    }
