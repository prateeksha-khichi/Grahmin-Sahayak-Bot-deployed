"""
Telegram Service - Send messages, audio, documents via Telegram Bot API
"""

import httpx
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()


class TelegramService:
    """Telegram Bot API client"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        if not self.bot_token:
            logger.warning("⚠️  TELEGRAM_BOT_TOKEN not set in environment")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        logger.info("✅ TelegramService initialized")
    
    async def send_message(self, chat_id: str, text: str):
        """
        Send text message to Telegram user
        
        Args:
            chat_id: Telegram chat/user ID
            text: Message text
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Message sent to {chat_id}")
                else:
                    logger.error(f"❌ Failed to send message: {response.text}")
                    
        except Exception as e:
            logger.error(f"❌ Telegram send_message error: {e}")
    
    async def send_audio(self, chat_id: str, audio_path: str, caption: str = ""):
        """
        Send audio file to Telegram user
        
        Args:
            chat_id: Telegram chat/user ID
            audio_path: Path to audio file
            caption: Audio caption
        """
        try:
            if not os.path.exists(audio_path):
                logger.error(f"❌ Audio file not found: {audio_path}")
                return
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(audio_path, 'rb') as audio:
                    files = {'audio': audio}
                    data = {
                        'chat_id': chat_id,
                        'caption': caption
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/sendAudio",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Audio sent to {chat_id}")
                    else:
                        logger.error(f"❌ Failed to send audio: {response.text}")
                        
        except Exception as e:
            logger.error(f"❌ Telegram send_audio error: {e}")
    
    async def send_document(self, chat_id: str, document_path: str, caption: str = ""):
        """
        Send document file to Telegram user
        
        Args:
            chat_id: Telegram chat/user ID
            document_path: Path to document file
            caption: Document caption
        """
        try:
            if not os.path.exists(document_path):
                logger.error(f"❌ Document not found: {document_path}")
                return
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(document_path, 'rb') as doc:
                    files = {'document': doc}
                    data = {
                        'chat_id': chat_id,
                        'caption': caption
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/sendDocument",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Document sent to {chat_id}")
                    else:
                        logger.error(f"❌ Failed to send document: {response.text}")
                        
        except Exception as e:
            logger.error(f"❌ Telegram send_document error: {e}")