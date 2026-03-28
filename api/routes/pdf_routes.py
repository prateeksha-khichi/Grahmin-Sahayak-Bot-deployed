from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from services.ocr_service import OCRService
from services.translation_service import TranslationService
from services.gtts_service import GTTsService
from services.telegram_service import TelegramService

from utils.llm_client import get_llm
from utils.file_utils import FileUtils

router = APIRouter(prefix="/pdf", tags=["PDF Explainer"])

ocr_service = OCRService()
translation_service = TranslationService()
gtts_service = GTTsService()
telegram_service = TelegramService()
llm = get_llm()


@router.post("/explain")
async def explain_document(
    file: UploadFile = File(...),
    telegram_user_id: str = "",
    target_lang: str = "hi"
):

    file_path = None

    try:
        # Validate file
        allowed_types = ['.pdf', '.jpg', '.jpeg', '.png']
        if not FileUtils.validate_file_type(file.filename, allowed_types):
            raise HTTPException(status_code=400, detail="Only PDF and image files allowed")

        # Save upload
        file_path = await FileUtils.save_upload(file)
        file_type = Path(file.filename).suffix[1:]

        # OCR
        extracted_text = ocr_service.extract_text(file_path, file_type)

        if not extracted_text:
            raise HTTPException(status_code=400, detail="No text found")

        # Simplify via Groq
        simplified_text = simplify_with_llm(extracted_text)

        # Translate
        translated_text = translation_service.translate(simplified_text, target_lang)

        # Action steps via Groq
        action_steps = generate_action_steps(extracted_text)
        action_steps_translated = translation_service.translate(action_steps, target_lang)

        # Full voice text
        full_text = f"{translated_text}\n\nआगे के कदम:\n{action_steps_translated}"

        # Generate gTTS audio
        audio_path = gtts_service.text_to_speech(full_text)

        # Telegram
        if telegram_user_id:
            await telegram_service.send_message(telegram_user_id, translated_text)
            await telegram_service.send_audio(telegram_user_id, audio_path, "🎧 आवाज़ में सुनें")
            await telegram_service.send_message(
                telegram_user_id,
                f"📋 आगे के कदम:\n{action_steps_translated}"
            )

        return {
            "success": True,
            "simplified_text": translated_text,
            "action_steps": action_steps_translated,
            "audio_path": audio_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if file_path:
            FileUtils.cleanup_file(file_path)


# ================= GROQ LLM FUNCTIONS =================


def simplify_with_llm(text: str) -> str:

    prompt = f"""
You are helping rural farmers.

Simplify this banking document in very simple Hindi:

{text}
"""

    try:
        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        print(e)
        return text[:400]


def generate_action_steps(text: str) -> str:

    prompt = f"""
Create a simple Hindi checklist:

1. Required documents
2. Next steps
3. Deadlines

{text}
"""

    try:
        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        print(e)
        return "कृपया बैंक से संपर्क करें।"
