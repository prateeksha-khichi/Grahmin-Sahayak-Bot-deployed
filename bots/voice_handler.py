"""
Voice Handler - AssemblyAI Integration
FIXED: Proper handling of transcription results
"""

import os
import assemblyai as aai
from loguru import logger
from pathlib import Path


class VoiceHandler:
    """
    Handles voice-to-text conversion using AssemblyAI
    """
    
    def __init__(self):
        """Initialize AssemblyAI client"""
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️ ASSEMBLYAI_API_KEY not found in environment")
            self.enabled = False
        else:
            aai.settings.api_key = self.api_key
            self.enabled = True
            logger.info("✅ AssemblyAI initialized")
    
    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech to text using AssemblyAI
        
        Args:
            audio_path: Path to audio file (.ogg, .mp3, .wav, etc.)
            
        Returns:
            Transcribed text string, or None if failed
        """
        if not self.enabled:
            logger.error("❌ AssemblyAI not enabled - missing API key")
            return None
        
        try:
            # Verify file exists
            if not os.path.exists(audio_path):
                logger.error(f"❌ Audio file not found: {audio_path}")
                return None
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            logger.info(f"📁 Audio file: {audio_path} ({file_size} bytes)")
            
            if file_size == 0:
                logger.error("❌ Audio file is empty")
                return None
            
            # Configure transcription settings
            config = aai.TranscriptionConfig(
                language_code="hi",  # Hindi
                speech_model=aai.SpeechModel.best,  # Use best model
                punctuate=True,
                format_text=True,
            )
            
            logger.info("🎙️ Starting AssemblyAI transcription...")
            
            # Create transcriber and transcribe
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_path)
            
            # CRITICAL: Check transcript status
            logger.info(f"📊 Transcript status: {transcript.status}")
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"❌ Transcription error: {transcript.error}")
                return None
            
            # CRITICAL: Check if text exists and is not empty
            if not transcript.text:
                logger.warning("⚠️ No text in transcript - audio may be unclear or silent")
                return None
            
            # Clean and validate text
            text = transcript.text.strip()
            
            if len(text) == 0:
                logger.warning("⚠️ Transcript text is empty after stripping")
                return None
            
            logger.success(f"✅ Transcription successful: '{text}' ({len(text)} chars)")
            
            # Optional: Log confidence if available
            if hasattr(transcript, 'confidence') and transcript.confidence:
                logger.info(f"📈 Confidence: {transcript.confidence:.2%}")
            
            return text
            
        except FileNotFoundError as e:
            logger.error(f"❌ File not found: {e}")
            return None
            
        except aai.types.TranscriptError as e:
            logger.error(f"❌ AssemblyAI transcript error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in speech_to_text: {e}")
            logger.exception("Full traceback:")
            return None
    
    def speech_to_text_with_fallback(self, audio_path: str) -> dict:
        """
        Transcribe with detailed result information
        
        Returns:
            dict with 'text', 'success', 'error', 'confidence'
        """
        result = {
            'text': None,
            'success': False,
            'error': None,
            'confidence': None
        }
        
        try:
            if not self.enabled:
                result['error'] = "AssemblyAI not configured"
                return result
            
            config = aai.TranscriptionConfig(
                language_code="hi",
                speech_model=aai.SpeechModel.best,
                punctuate=True,
                format_text=True,
            )
            
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                result['error'] = transcript.error
                return result
            
            if transcript.text and len(transcript.text.strip()) > 0:
                result['text'] = transcript.text.strip()
                result['success'] = True
                
                if hasattr(transcript, 'confidence'):
                    result['confidence'] = transcript.confidence
            else:
                result['error'] = "No speech detected in audio"
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Transcription failed: {e}")
            return result


# Utility function for quick testing
def test_transcription(audio_path: str):
    """Test transcription of an audio file"""
    handler = VoiceHandler()
    
    if not handler.enabled:
        print("❌ AssemblyAI not configured")
        return
    
    print(f"Testing: {audio_path}")
    result = handler.speech_to_text_with_fallback(audio_path)
    
    print(f"Success: {result['success']}")
    print(f"Text: {result['text']}")
    print(f"Error: {result['error']}")
    print(f"Confidence: {result['confidence']}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_transcription(sys.argv[1])
    else:
        print("Usage: python voice_handler.py <audio_file>")