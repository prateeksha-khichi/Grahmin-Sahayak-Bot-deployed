"""
Google Text-to-Speech Service
"""

from gtts import gTTS
import os
import uuid
from loguru import logger


class GTTsService:
    """Text-to-Speech using Google TTS"""
    
    def __init__(self):
        # Create audio directory if it doesn't exist
        self.audio_dir = "audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        logger.info(f"✅ GTTsService initialized - Audio dir: {self.audio_dir}")

    def text_to_speech(self, text: str, lang: str = "hi") -> str:
        """
        Convert text to speech and save as MP3
        
        Args:
            text: Text to convert
            lang: Language code (hi, en, etc.)
            
        Returns:
            Path to generated audio file
        """
        try:
            # Generate unique filename
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filepath)
            
            logger.info(f"✅ Generated TTS audio: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            raise
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old audio files
        
        Args:
            max_age_hours: Delete files older than this many hours
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.audio_dir):
                filepath = os.path.join(self.audio_dir, filename)
                
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logger.info(f"🗑️  Cleaned up old audio: {filename}")
                        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")