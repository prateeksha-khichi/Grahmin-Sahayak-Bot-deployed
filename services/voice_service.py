"""
Voice Service — Gramin Sahayak Bot
====================================
Handles:
  • Speech-to-Text  : Google SpeechRecognition (primary) + OpenAI Whisper (fallback)
  • Language detection : auto-detect from recognised text via langdetect
  • Text-to-Speech  : Google gTTS (reuses GTTsService under the hood)

Supports: Hindi, English, Gujarati, Marathi, Punjabi, Rajasthani (treated as Hindi)
"""

import os
import uuid
import asyncio
from pathlib import Path
from loguru import logger

# ─── gTTS ────────────────────────────────────────────────────────────────────
from gtts import gTTS

# ─── SpeechRecognition ───────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
    logger.info("✅ SpeechRecognition library loaded")
except ImportError:
    SR_AVAILABLE = False
    logger.warning("⚠️ SpeechRecognition not installed — STT will use Whisper only")

# ─── AssemblyAI (optional, cloud API) ─────────────────────────────────────────
try:
    import assemblyai as aai
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
    if ASSEMBLYAI_API_KEY:
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        ASSEMBLYAI_AVAILABLE = True
        logger.info("✅ AssemblyAI library loaded and key found")
    else:
        ASSEMBLYAI_AVAILABLE = False
        logger.warning("⚠️ AssemblyAI installed but no API key found in .env")
except ImportError:
    ASSEMBLYAI_AVAILABLE = False
    logger.info("ℹ️  AssemblyAI not installed")

# ─── Whisper (optional, local model) ─────────────────────────────────────────
try:
    import whisper as _whisper
    WHISPER_AVAILABLE = True
    logger.info("✅ OpenAI Whisper library loaded")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.info("ℹ️  Whisper not installed — using SpeechRecognition only")

# ─── pydub (OGG → WAV conversion for Google SR) ──────────────────────────────
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    try:
        import imageio_ffmpeg
        AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info(f"✅ pydub loaded (using bundled ffmpeg: {AudioSegment.converter})")
    except ImportError:
        logger.info("✅ pydub loaded (using system ffmpeg)")
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("⚠️  pydub not installed — OGG conversion may fail")

# ─── langdetect ──────────────────────────────────────────────────────────────
try:
    from langdetect import detect as _langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("⚠️  langdetect not installed — defaulting to Hindi")


# ══════════════════════════════════════════════════════════════════════════════
# Language configuration
# ══════════════════════════════════════════════════════════════════════════════

# Maps a langdetect/whisper code → gTTS + Google SR BCP-47 codes
LANGUAGE_CONFIG: dict[str, dict] = {
    "hi": {
        "name": "Hindi",
        "gtts_lang": "hi",
        "sr_lang": "hi-IN",          # for Google SR
        "whisper_lang": "hindi",
    },
    "en": {
        "name": "English",
        "gtts_lang": "en",
        "sr_lang": "en-IN",
        "whisper_lang": "english",
    },
    "gu": {
        "name": "Gujarati",
        "gtts_lang": "gu",
        "sr_lang": "gu-IN",
        "whisper_lang": "gujarati",
    },
    "mr": {
        "name": "Marathi",
        "gtts_lang": "mr",
        "sr_lang": "mr-IN",
        "whisper_lang": "marathi",
    },
    "pa": {
        "name": "Punjabi",
        "gtts_lang": "pa",
        "sr_lang": "pa-IN",
        "whisper_lang": "punjabi",
    },
    "ta": {
        "name": "Tamil",
        "gtts_lang": "ta",
        "sr_lang": "ta-IN",
        "whisper_lang": "tamil",
    },
    "te": {
        "name": "Telugu",
        "gtts_lang": "te",
        "sr_lang": "te-IN",
        "whisper_lang": "telugu",
    },
    "kn": {
        "name": "Kannada",
        "gtts_lang": "kn",
        "sr_lang": "kn-IN",
        "whisper_lang": "kannada",
    },
    "ml": {
        "name": "Malayalam",
        "gtts_lang": "ml",
        "sr_lang": "ml-IN",
        "whisper_lang": "malayalam",
    },
    "bn": {
        "name": "Bengali",
        "gtts_lang": "bn",
        "sr_lang": "bn-IN",
        "whisper_lang": "bengali",
    },
    # Rajasthani has no distinct gTTS code — fall back to Hindi
    "rajasthani": {
        "name": "Rajasthani",
        "gtts_lang": "hi",
        "sr_lang": "hi-IN",
        "whisper_lang": "hindi",
    },
}

DEFAULT_LANG = "hi"

# gTTS languages that are reliably supported
GTTS_SUPPORTED = {
    "hi", "en", "gu", "mr", "pa", "ta", "te", "kn", "ml", "bn"
}


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _tmp_path(suffix: str) -> str:
    """Return a unique temp file path inside temp_audio/."""
    d = _ensure_dir(os.path.join(os.path.dirname(__file__), "..", "temp_audio"))
    return os.path.join(d, f"{uuid.uuid4().hex}{suffix}")


def _audio_path(suffix: str) -> str:
    """Return a unique path inside audio/ for outbound voice replies."""
    d = _ensure_dir(os.path.join(os.path.dirname(__file__), "..", "audio"))
    return os.path.join(d, f"{uuid.uuid4().hex}{suffix}")


def _ogg_to_wav(ogg_path: str) -> str:
    """Convert Telegram OGG voice note to WAV for Google SpeechRecognition."""
    wav_path = _tmp_path(".wav")
    if PYDUB_AVAILABLE:
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
    else:
        # Fallback: use ffmpeg directly via subprocess if pydub unavailable
        import subprocess
        ffmpeg_cmd = "ffmpeg"
        try:
            import imageio_ffmpeg
            ffmpeg_cmd = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
            
        subprocess.run(
            [ffmpeg_cmd, "-y", "-i", ogg_path, wav_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    return wav_path


def _detect_language(text: str, fallback: str = DEFAULT_LANG) -> str:
    """Detect language from transcribed text; return ISO 639-1 code."""
    if not LANGDETECT_AVAILABLE or not text.strip():
        return fallback
    try:
        code = _langdetect(text)
        # langdetect sometimes returns zh-cn etc — normalise
        code = code.split("-")[0].lower()
        if code in LANGUAGE_CONFIG:
            return code
        return fallback
    except Exception:
        return fallback


# ══════════════════════════════════════════════════════════════════════════════
# Whisper model cache (loaded lazily, only if needed)
# ══════════════════════════════════════════════════════════════════════════════
_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None and WHISPER_AVAILABLE:
        logger.info("🔄 Loading Whisper 'base' model (first time)…")
        _whisper_model = _whisper.load_model("base")
        logger.success("✅ Whisper model loaded")
    return _whisper_model


# ══════════════════════════════════════════════════════════════════════════════
# Core async functions
# ══════════════════════════════════════════════════════════════════════════════

async def transcribe_audio(ogg_path: str, hint_lang: str = DEFAULT_LANG) -> dict:
    """
    Transcribe a Telegram voice OGG file to text.

    Strategy:
      1. Convert OGG → WAV
      2. Try Google SpeechRecognition (needs internet, no API key required)
      3. On failure, try Whisper (local, offline)
      4. Auto-detect language from transcribed text

    Returns:
        {
            "text": str,           # transcribed text (empty if failed)
            "language": str,       # detected ISO 639-1 code
            "method": str,         # "google_sr" | "whisper" | "failed"
            "success": bool,
        }
    """
    loop = asyncio.get_event_loop()

    # ── 1. Convert OGG → WAV ─────────────────────────────────────────────
    wav_path = None
    try:
        wav_path = await loop.run_in_executor(None, _ogg_to_wav, ogg_path)
    except Exception as e:
        logger.warning(f"[Voice] OGG→WAV conversion failed (skipping Google SR): {e}")

    text = ""
    method = "failed"

    # ── 2. Google SpeechRecognition ───────────────────────────────────────
    if SR_AVAILABLE and wav_path and os.path.exists(wav_path):
        try:
            cfg = LANGUAGE_CONFIG.get(hint_lang, LANGUAGE_CONFIG[DEFAULT_LANG])
            text = await loop.run_in_executor(
                None,
                _google_sr_transcribe,
                wav_path,
                cfg["sr_lang"],
            )
            if text:
                method = "google_sr"
                logger.success(f"[Voice] Google SR: '{text[:60]}…'")
        except Exception as e:
            logger.warning(f"[Voice] Google SR failed: {e}")

    # ── 3. AssemblyAI fallback ───────────────────────────────────────────────
    if not text and ASSEMBLYAI_AVAILABLE:
        try:
            text = await loop.run_in_executor(
                None,
                _assemblyai_transcribe,
                ogg_path,  # AssemblyAI can handle OGG
            )
            if text:
                method = "assemblyai"
                logger.success(f"[Voice] AssemblyAI: '{text[:60]}…'")
        except Exception as e:
            logger.warning(f"[Voice] AssemblyAI failed: {e}")

    # ── 4. Whisper fallback ───────────────────────────────────────────────
    if not text and WHISPER_AVAILABLE:
        try:
            text = await loop.run_in_executor(
                None,
                _whisper_transcribe,
                ogg_path,  # Whisper can handle OGG directly
            )
            if text:
                method = "whisper"
                logger.success(f"[Voice] Whisper: '{text[:60]}…'")
        except Exception as e:
            logger.warning(f"[Voice] Whisper failed: {e}")

    # ── 5. Language detection ─────────────────────────────────────────────
    detected_lang = _detect_language(text, fallback=hint_lang)

    # ── Cleanup temp WAV ──────────────────────────────────────────────────
    try:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
    except Exception:
        pass

    return {
        "text": text.strip(),
        "language": detected_lang,
        "method": method,
        "success": bool(text.strip()),
    }


def _google_sr_transcribe(wav_path: str, lang_code: str) -> str:
    """Synchronous Google SpeechRecognition call (run in executor)."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    with sr.AudioFile(wav_path) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(audio_data, language=lang_code)


def _assemblyai_transcribe(audio_path: str) -> str:
    """Synchronous AssemblyAI transcription call (run in executor)."""
    config = aai.TranscriptionConfig(language_detection=True)
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)
    if transcript.status == aai.TranscriptStatus.error:
        logger.error(f"AssemblyAI Error: {transcript.error}")
        return ""
    return transcript.text or ""


def _whisper_transcribe(audio_path: str) -> str:
    """Synchronous Whisper transcription call (run in executor)."""
    model = _get_whisper_model()
    if model is None:
        return ""
    result = model.transcribe(audio_path)
    return result.get("text", "").strip()


async def text_to_speech_reply(text: str, language_code: str = DEFAULT_LANG) -> str | None:
    """
    Convert bot response text to an MP3 audio file using gTTS.

    Args:
        text: The text to speak
        language_code: ISO 639-1 code (hi, en, gu, mr, pa…)

    Returns:
        Absolute path to MP3 file, or None on failure.
    """
    loop = asyncio.get_event_loop()
    cfg = LANGUAGE_CONFIG.get(language_code, LANGUAGE_CONFIG[DEFAULT_LANG])
    gtts_lang = cfg["gtts_lang"] if cfg["gtts_lang"] in GTTS_SUPPORTED else "hi"

    # Truncate very long text for TTS (keep voice replies concise)
    tts_text = text[:1000] if len(text) > 1000 else text

    mp3_path = _audio_path(".mp3")

    try:
        await loop.run_in_executor(
            None,
            _do_gtts,
            tts_text,
            gtts_lang,
            mp3_path,
        )
        logger.success(f"[Voice] TTS audio → {mp3_path}")
        return mp3_path
    except Exception as e:
        logger.error(f"[Voice] gTTS failed: {e}")
        return None


def _do_gtts(text: str, lang: str, filepath: str) -> None:
    """Synchronous gTTS save (run in executor)."""
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(filepath)


# ══════════════════════════════════════════════════════════════════════════════
# Convenience wrapper
# ══════════════════════════════════════════════════════════════════════════════

def get_language_name(code: str) -> str:
    cfg = LANGUAGE_CONFIG.get(code)
    return cfg["name"] if cfg else "Hindi"
