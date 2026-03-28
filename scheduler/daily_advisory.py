"""
Daily Advisory Scheduler
Sends automated advisories to users at scheduled time
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import UserPreference
from services.advisory_service import AdvisoryService
from services.translation_service import TranslationService
from services.gtts_service import GTTsService
from services.telegram_service import TelegramService
from loguru import logger
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize services
advisory_service = AdvisoryService()
translation_service = TranslationService()
gtts_service = GTTsService()
telegram_service = TelegramService()


async def send_daily_advisories():
    """
    Feature 2: Automated daily advisory sender
    Runs every day at configured time
    """
    logger.info("🌅 Starting daily advisory broadcast...")
    
    db = SessionLocal()
    
    try:
        # Get all users with advisory enabled
        users = db.query(UserPreference).filter(
            UserPreference.advisory_enabled == True
        ).all()
        
        logger.info(f"📊 Sending advisories to {len(users)} users...")
        
        for user in users:
            try:
                # Generate personalized advisory
                location = user.location or "Delhi"
                advisory_text = await advisory_service.generate_daily_advisory(
                    user.telegram_user_id,
                    location
                )
                
                # Translate to user's preferred language
                target_lang = user.preferred_language or "hi"
                translated = translation_service.translate(
                    advisory_text,
                    target_lang
                )
                
                # Generate audio
                audio_path = gtts_service.text_to_speech(
                    translated,
                    lang=target_lang
                )
                
                # Send to Telegram
                await telegram_service.send_audio(
                    user.telegram_user_id,
                    audio_path,
                    "🌅 आज की सलाह"
                )
                
                logger.success(f"✅ Sent advisory to {user.telegram_user_id}")
                
                # Rate limit - avoid Telegram API limits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed for {user.telegram_user_id}: {e}")
                continue
        
        logger.success("✅ Daily advisory broadcast complete!")
        
    except Exception as e:
        logger.error(f"❌ Broadcast error: {e}")
    
    finally:
        db.close()


def start_scheduler():
    """
    Initialize and start the APScheduler
    
    Returns:
        AsyncIOScheduler instance
    """
    try:
        scheduler = AsyncIOScheduler()
        
        # Get time from environment (format: "HH:MM")
        advisory_time = os.getenv("DAILY_ADVISORY_TIME", "07:00")
        hour, minute = map(int, advisory_time.split(":"))
        
        # Schedule daily job
        scheduler.add_job(
            send_daily_advisories,
            trigger='cron',
            hour=hour,
            minute=minute,
            id='daily_advisory',
            replace_existing=True
        )
        
        scheduler.start()
        logger.success(f"✅ Scheduler started - Daily advisory at {advisory_time}")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        return None