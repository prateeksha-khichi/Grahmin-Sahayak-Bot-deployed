"""
Translation Service - Translate text between languages
"""

from deep_translator import GoogleTranslator
from langdetect import detect
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()


class TranslationService:
    """Multi-provider translation service"""
    
    def __init__(self):
        self.service = os.getenv("TRANSLATION_SERVICE", "google")
        self.libretranslate_url = os.getenv("LIBRETRANSLATE_URL", "")
        logger.info(f"✅ TranslationService initialized - Provider: {self.service}")

    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        
        Args:
            text: Text to detect
            
        Returns:
            Language code (en, hi, etc.)
        """
        try:
            return detect(text)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"

    def translate_google(self, text: str, target_lang: str) -> str:
        """
        Translate using Google Translate (via deep-translator)
        
        Args:
            text: Text to translate
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        try:
            translator = GoogleTranslator(source="auto", target=target_lang)
            translated = translator.translate(text)
            logger.info(f"✅ Translated to {target_lang}")
            return translated
            
        except Exception as e:
            logger.error(f"❌ Google translation error: {e}")
            return text

    def translate_libretranslate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        """
        Translate using LibreTranslate
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        try:
            import requests
            
            if not self.libretranslate_url:
                logger.warning("LibreTranslate URL not configured")
                return text
            
            url = f"{self.libretranslate_url}/translate"
            
            payload = {
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            translated = response.json()["translatedText"]
            logger.info(f"✅ Translated via LibreTranslate to {target_lang}")
            return translated
            
        except Exception as e:
            logger.error(f"❌ LibreTranslate error: {e}")
            return text

    def translate(self, text: str, target_lang: str = "hi") -> str:
        """
        Main translation method - routes to configured provider
        
        Args:
            text: Text to translate
            target_lang: Target language code (default: hi)
            
        Returns:
            Translated text
        """
        # Detect source language
        source_lang = self.detect_language(text)
        
        # Skip if already in target language
        if source_lang == target_lang:
            logger.info(f"Text already in {target_lang}, skipping translation")
            return text
        
        # Route to provider
        if self.service == "google":
            return self.translate_google(text, target_lang)
        elif self.service == "libretranslate":
            return self.translate_libretranslate(text, source_lang, target_lang)
        else:
            logger.warning(f"Unknown translation service: {self.service}")
            return text