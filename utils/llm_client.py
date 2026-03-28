"""
LLM Client - Handles Groq API calls (FREE tier)
Groq provides fast inference with generous free limits
"""

import os
from typing import Optional
from groq import Groq
from loguru import logger
from dotenv import load_dotenv
from pathlib import Path

# ---------------- LOAD ENV (ABSOLUTE PATH FIX) ---------------- #

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

# Debug once (remove later if you want)
print("DEBUG GROQ KEY:", os.getenv("GROQ_API_KEY"))


class LLMClient:
    """
    Groq API client for text generation
    FREE tier: 14,400 requests/day, 20 requests/minute
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            logger.warning("⚠️ GROQ_API_KEY not found! LLM features will not work.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            logger.info("✅ Groq client initialized")

        # Default model
        self.model = "llama-3.1-8b-instant"

    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ) -> str:

        if not self.client:
            return "⚠️ LLM सेवा उपलब्ध नहीं है। कृपया API कुंजी जांचें।"

        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
            )

            answer = response.choices[0].message.content.strip()

            logger.info(f"✅ Generated response ({len(answer)} chars)")
            return answer

        except Exception as e:
            logger.error(f"❌ Groq API error: {e}")
            return "क्षमा करें, कुछ गलती हुई। कृपया फिर से प्रयास करें।"

    def generate_with_retry(self, prompt: str, max_retries: int = 2, **kwargs) -> str:

        for attempt in range(max_retries + 1):
            try:
                return self.generate(prompt, **kwargs)
            except Exception:
                if attempt < max_retries:
                    logger.warning(f"⚠️ Retry {attempt + 1}/{max_retries}")
                else:
                    return "क्षमा करें, सेवा अभी उपलब्ध नहीं है।"


# ---------------- SINGLETON FOR FASTAPI ---------------- #

_llm_instance = None


def get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance


# ---------------- LOCAL TEST ---------------- #

if __name__ == "__main__":
    client = LLMClient()

    test_prompt = "प्रधानमंत्री मुद्रा योजना क्या है? सरल हिंदी में 3 वाक्यों में बताओ।"

    response = client.generate(test_prompt, max_tokens=200)
    print(response)
