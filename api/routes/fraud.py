"""
Fraud detection API routes
"""

from fastapi import APIRouter, HTTPException
from api.schemas.request_response import FraudRequest, FraudResponse
from services.fraud_service import FraudService
from database.db_manager import db
from loguru import logger

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])
fraud_service = FraudService()


@router.post("/check-scheme", response_model=FraudResponse)
async def check_scheme_fraud(request: FraudRequest):
    """
    Check if a loan scheme is fraudulent
    """
    try:
        scheme_data = request.dict()
        result = fraud_service.detect_fraud(scheme_data)
        
        # Save to database
        db_data = {
            'user_telegram_id': 'api_user',
            'scheme_name': request.scheme_name,
            'scheme_description': request.description,
            'is_fraud': result['is_fraud'],
            'confidence': result['confidence'],
            'fraud_signals': result['fraud_signals'],
            'verified': result['verified']
        }
        db.save_fraud_check(db_data)
        
        return FraudResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Fraud API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/common-scams")
async def get_common_scams():
    """
    Get list of common loan scams to watch out for
    """
    scams = [
        {
            "type": "Advance Fee Fraud",
            "description": "Asking for upfront payment before loan approval",
            "red_flags": ["Pay processing fee first", "Send money via UPI", "WhatsApp/Telegram only"]
        },
        {
            "type": "No Document Loan Scam",
            "description": "Promising loans without any verification",
            "red_flags": ["No documents needed", "Instant approval", "100% guaranteed"]
        },
        {
            "type": "Impersonation Scam",
            "description": "Fake agents claiming to be from banks",
            "red_flags": ["Personal mobile numbers", "Unofficial email IDs", "Pressure tactics"]
        }
    ]
    
    return {"scams": scams, "helpline": "1930 (Cyber Crime Helpline)"}