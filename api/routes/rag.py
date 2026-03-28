"""
RAG chatbot API routes
"""

from fastapi import APIRouter, HTTPException
from api.schemas.request_response import RAGRequest, RAGResponse
from services.rag_service import RAGService
from database.db_manager import db
from loguru import logger

router = APIRouter(prefix="/rag", tags=["RAG Chatbot"])
rag_service = RAGService()


@router.post("/ask", response_model=RAGResponse)
async def ask_question(request: RAGRequest):
    """
    Ask a question about banking/schemes using RAG
    """
    try:
        result = rag_service.answer_question(
            request.question,
            language=request.language,
            include_sources=request.include_sources
        )
        
        # Save to database
        db_data = {
            'user_telegram_id': 'api_user',
            'question': request.question,
            'answer': result['answer'],
            'sources': result['sources'],
            'confidence': result['confidence'],
            'language': request.language
        }
        db.save_rag_query(db_data)
        
        return RAGResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ RAG API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-scheme")
async def explain_scheme(scheme_name: str):
    """
    Get detailed explanation of a government scheme
    """
    try:
        explanation = rag_service.explain_scheme(scheme_name)
        return {"scheme_name": scheme_name, "explanation": explanation}
        
    except Exception as e:
        logger.error(f"❌ Scheme explanation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-term")
async def explain_banking_term(term: str):
    """
    Explain a banking/financial term in simple language
    """
    try:
        explanation = rag_service.explain_term(term)
        return {"term": term, "explanation": explanation}
        
    except Exception as e:
        logger.error(f"❌ Term explanation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_rag_status():
    """
    Get RAG service status
    """
    try:
        status = rag_service.get_service_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))