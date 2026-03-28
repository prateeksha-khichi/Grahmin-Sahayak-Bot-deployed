"""
RAG Service - High-level service combining RAG + LLM
WITH MULTI-LANGUAGE SUPPORT
"""

from typing import Dict
from loguru import logger

from rag.rag_pipeline import RAGPipeline
from utils.llm_client import LLMClient


class RAGService:
    """Service for RAG-based question answering"""

    def __init__(self):
        self.rag_pipeline = RAGPipeline()
        self.llm_client = LLMClient()
        self._initialized = False

        logger.info("🧠 RAGService created (lazy initialization)")

    def _ensure_initialized(self):
        """Build index only once"""
        if not self._initialized:
            logger.info("🔄 Building RAG index...")
            self.rag_pipeline.build_index()
            self._initialized = True
            logger.info("✅ RAG index ready")

    def answer_question(
        self,
        question: str,
        language: str = "hindi",  # 'hindi', 'english', 'en', 'hi', 'pa', etc.
        include_sources: bool = True
    ) -> Dict:
        """
        Answer a question using RAG + LLM in user's language
        
        Args:
            question: User's question
            language: User's preferred language
            include_sources: Include source citations
            
        Returns:
            Dict with answer, sources, context
        """
        try:
            self._ensure_initialized()

            # Normalize language code
            lang_normalized = self._normalize_language(language)

            rag_result = self.rag_pipeline.query(question, language=lang_normalized)

            if not rag_result.get('context'):
                return self._no_context_response(lang_normalized)

            answer = self.llm_client.generate(
                rag_result['prompt'],
                max_tokens=400,
                temperature=0.3
            )

            avg_score = sum(
                c['score'] for c in rag_result['retrieved_chunks']
            ) / len(rag_result['retrieved_chunks'])

            if include_sources and rag_result.get('sources'):
                source_text = self._format_sources(rag_result['sources'], lang_normalized)
                answer += f"\n\n{source_text}"

            return {
                'answer': answer,
                'sources': rag_result['sources'],
                'context_used': rag_result['context'][:500],
                'confidence': round(float(avg_score), 2)
            }

        except Exception as e:
            logger.error(f"❌ RAG service error: {e}")
            return self._error_response(language)

    def _normalize_language(self, lang: str) -> str:
        """Normalize language code"""
        lang_map = {
            'en': 'english',
            'hi': 'hindi',
            'pa': 'punjabi',
            'ml': 'malayalam',
            'ta': 'tamil',
            'english': 'english',
            'hindi': 'hindi',
            'punjabi': 'punjabi'
        }
        return lang_map.get(lang.lower(), 'hindi')

    def _format_sources(self, sources: list, language: str) -> str:
        """Format source citations in user's language"""
        source_labels = {
            'english': '📚 Sources:',
            'hindi': '📚 स्रोत:',
            'punjabi': '📚 ਸਰੋਤ:',
            'malayalam': '📚 സ്രോതസ്സുകൾ:',
            'tamil': '📚 ஆதாரங்கள்:'
        }
        
        label = source_labels.get(language, source_labels['hindi'])
        return f"{label} {', '.join(sources)}"

    def _no_context_response(self, language: str) -> Dict:
        """Response when no context found"""
        messages = {
            'english': "I don't have enough information to answer this question.",
            'hindi': "क्षमा करें, मुझे इस प्रश्न का उत्तर देने के लिए पर्याप्त जानकारी नहीं है।",
            'punjabi': "ਮਾਫ਼ ਕਰਨਾ, ਮੇਰੇ ਕੋਲ ਇਸ ਸਵਾਲ ਦਾ ਜਵਾਬ ਦੇਣ ਲਈ ਕਾਫ਼ੀ ਜਾਣਕਾਰੀ ਨਹੀਂ ਹੈ।"
        }
        
        return {
            'answer': messages.get(language, messages['hindi']),
            'sources': [],
            'context_used': '',
            'confidence': 0.0
        }

    def _error_response(self, language: str) -> Dict:
        """Error response"""
        messages = {
            'english': "Sorry, answer not available right now.",
            'hindi': "क्षमा करें, अभी उत्तर उपलब्ध नहीं है।",
            'punjabi': "ਮਾਫ਼ ਕਰਨਾ, ਹੁਣ ਜਵਾਬ ਉਪਲਬਧ ਨਹੀਂ ਹੈ।"
        }
        
        return {
            'answer': messages.get(language, messages['hindi']),
            'sources': [],
            'context_used': '',
            'confidence': 0.0
        }

    def explain_scheme(self, scheme_name: str) -> str:
        """Explain a government scheme"""
        try:
            self._ensure_initialized()
            prompt = self.rag_pipeline.explain_scheme(scheme_name)
            return self.llm_client.generate(prompt, max_tokens=600)
        except Exception as e:
            logger.error(f"Error explaining scheme: {e}")
            return "क्षमा करें, योजना की जानकारी नहीं मिली।"

    def explain_term(self, term: str) -> str:
        """Explain a banking/financial term"""
        try:
            self._ensure_initialized()
            prompt = self.rag_pipeline.explain_term(term)
            return self.llm_client.generate(prompt, max_tokens=300)
        except Exception as e:
            logger.error(f"Error explaining term: {e}")
            return "क्षमा करें, शब्द का अर्थ नहीं मिला।"

    def get_service_status(self) -> Dict:
        """Get service status"""
        rag_stats = self.rag_pipeline.get_stats()
        llm_available = self.llm_client.client is not None

        return {
            'rag_status': rag_stats.get('status', 'unknown'),
            'llm_available': llm_available,
            'total_documents': rag_stats.get('total_chunks', 0),
            'service_healthy': rag_stats.get('status') == 'indexed'
        }