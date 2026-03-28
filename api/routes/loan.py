"""
Loan API routes - CORRECTED
Matches actual model features
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.loan_service import LoanService
from loguru import logger

router = APIRouter(prefix="/loan", tags=["Loan"])
loan_service = LoanService()


# ==================== REQUEST/RESPONSE MODELS ==================== #

class LoanRequest(BaseModel):
    """
    Loan eligibility request matching actual model features
    """
    # Feature 1: Dependents
    no_of_dependents: int = Field(..., ge=0, description="Number of dependents (0, 1, 2, 3, 4...)")
    
    # Feature 2: Education
    education: str = Field(..., description="Graduate or Not Graduate")
    
    # Feature 3: Self Employed
    self_employed: str = Field(..., description="Yes or No")
    
    # Feature 4: Annual Income
    income_annum: float = Field(..., gt=0, description="Annual income in rupees")
    
    # Feature 5: Loan Amount
    loan_amount: float = Field(..., gt=0, description="Requested loan amount in rupees")
    
    # Feature 6: Loan Term
    loan_term: int = Field(..., gt=0, description="Loan term in months (e.g., 120, 180, 240, 360)")
    
    # Feature 7: CIBIL Score
    cibil_score: int = Field(..., ge=300, le=900, description="CIBIL/Credit score (300-900)")
    
    # Feature 8: Residential Assets
    residential_assets_value: float = Field(default=0, ge=0, description="Home/plot value in rupees")
    
    # Feature 9: Commercial Assets
    commercial_assets_value: float = Field(default=0, ge=0, description="Shop/office value in rupees")
    
    # Feature 10: Luxury Assets
    luxury_assets_value: float = Field(default=0, ge=0, description="Car/bike/jewelry value in rupees")
    
    # Feature 11: Bank Assets
    bank_asset_value: float = Field(default=0, ge=0, description="Savings/FD/deposits in rupees")
    
    class Config:
        schema_extra = {
            "example": {
                "no_of_dependents": 2,
                "education": "Graduate",
                "self_employed": "Yes",
                "income_annum": 600000,
                "loan_amount": 4000000,
                "loan_term": 240,
                "cibil_score": 800,
                "residential_assets_value": 2000000,
                "commercial_assets_value": 500000,
                "luxury_assets_value": 300000,
                "bank_asset_value": 100000
            }
        }


class LoanResponse(BaseModel):
    """Loan eligibility response"""
    eligible: bool
    confidence: float
    recommended_amount: float
    emi: float
    interest_rate: float
    tenure_months: int
    message_hindi: str
    message_english: str


# ==================== API ENDPOINTS ==================== #

@router.post("/check-eligibility", response_model=LoanResponse)
async def check_loan_eligibility(request: LoanRequest):
    """
    Check loan eligibility using the trained ML model
    
    Takes 11 features that match the actual model:
    1. no_of_dependents
    2. education
    3. self_employed
    4. income_annum
    5. loan_amount
    6. loan_term
    7. cibil_score
    8. residential_assets_value
    9. commercial_assets_value
    10. luxury_assets_value
    11. bank_asset_value
    """
    try:
        user_data = request.dict()
        
        logger.info(f"Loan eligibility request received:")
        logger.info(f"  Dependents: {user_data['no_of_dependents']}")
        logger.info(f"  Education: {user_data['education']}")
        logger.info(f"  Self Employed: {user_data['self_employed']}")
        logger.info(f"  Annual Income: ₹{user_data['income_annum']:,.0f}")
        logger.info(f"  Loan Amount: ₹{user_data['loan_amount']:,.0f}")
        logger.info(f"  Loan Term: {user_data['loan_term']} months")
        logger.info(f"  CIBIL Score: {user_data['cibil_score']}")
        
        result = loan_service.predict_eligibility(user_data)
        
        logger.info(f"Prediction result: Eligible={result['eligible']}, Confidence={result['confidence']}")
        
        return LoanResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Loan API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemes")
async def get_government_schemes():
    """
    Get list of verified government loan schemes
    """
    schemes = [
        {
            "name": "प्रधानमंत्री मुद्रा योजना (PM MUDRA)",
            "name_english": "Pradhan Mantri MUDRA Yojana",
            "max_amount": 1000000,
            "purpose": "Business/Micro Enterprises",
            "interest_rate": "8-12%",
            "features": [
                "No collateral required for loans up to ₹10 lakh",
                "Three categories: Shishu (up to ₹50,000), Kishore (₹50,000-₹5 lakh), Tarun (₹5-₹10 lakh)"
            ],
            "verified": True,
            "website": "https://www.mudra.org.in"
        },
        {
            "name": "किसान क्रेडिट कार्ड (KCC)",
            "name_english": "Kisan Credit Card",
            "max_amount": 300000,
            "purpose": "Agriculture/Farming",
            "interest_rate": "4-7% (subsidized)",
            "features": [
                "Interest subvention of 2%",
                "Additional 3% incentive for timely repayment",
                "Effective rate: 4% per annum"
            ],
            "verified": True,
            "website": "https://pmkisan.gov.in"
        },
        {
            "name": "Stand Up India",
            "name_english": "Stand Up India",
            "max_amount": 10000000,
            "purpose": "SC/ST/Women entrepreneurs",
            "interest_rate": "Base rate + margin (typically 9-12%)",
            "features": [
                "For setting up greenfield enterprises",
                "Manufacturing, services, or trading sector",
                "Repayment period: 7 years with moratorium"
            ],
            "verified": True,
            "website": "https://www.standupmitra.in"
        },
        {
            "name": "PM-KISAN योजना",
            "name_english": "PM-KISAN Scheme",
            "max_amount": 6000,
            "purpose": "Direct income support to farmers",
            "interest_rate": "N/A (Direct Benefit Transfer)",
            "features": [
                "₹6,000 per year in 3 installments",
                "Direct to bank account",
                "For all landholding farmers"
            ],
            "verified": True,
            "website": "https://pmkisan.gov.in"
        },
        {
            "name": "प्रधानमंत्री आवास योजना (PMAY)",
            "name_english": "Pradhan Mantri Awas Yojana",
            "max_amount": 1200000,
            "purpose": "Home loan subsidy",
            "interest_rate": "Interest subsidy up to 2.67 lakh",
            "features": [
                "For EWS, LIG, and MIG categories",
                "Credit-linked subsidy on home loans",
                "Repayment period: up to 20 years"
            ],
            "verified": True,
            "website": "https://pmaymis.gov.in"
        }
    ]
    
    return {
        "schemes": schemes,
        "count": len(schemes),
        "disclaimer": "ये सभी सरकारी योजनाएं हैं। कृपया आधिकारिक वेबसाइट पर जाकर सत्यापित करें।"
    }


@router.get("/requirements")
async def get_loan_requirements():
    """
    Get standard loan requirements and documents needed
    """
    return {
        "documents_required": {
            "identity_proof": [
                "Aadhaar Card",
                "PAN Card",
                "Voter ID",
                "Passport"
            ],
            "address_proof": [
                "Aadhaar Card",
                "Utility bills (electricity/water)",
                "Ration card",
                "Rent agreement"
            ],
            "income_proof": [
                "Salary slips (last 3 months)",
                "Bank statements (last 6 months)",
                "Income Tax Returns",
                "Form 16"
            ],
            "business_documents": [
                "Business registration certificate",
                "GST registration",
                "Business bank statements",
                "Profit & Loss statement"
            ],
            "property_documents": [
                "Property papers (if applying for secured loan)",
                "Sale deed",
                "Encumbrance certificate"
            ]
        },
        "eligibility_criteria": {
            "age": "21-65 years",
            "minimum_income": "₹15,000 per month (varies by bank)",
            "minimum_cibil": "650+ (700+ preferred)",
            "employment": "Salaried/Self-employed/Business owner"
        },
        "tips": [
            "Maintain good credit score (750+)",
            "Keep debt-to-income ratio below 40%",
            "Ensure all documents are up-to-date",
            "Compare interest rates from multiple banks",
            "Read all terms and conditions carefully"
        ]
    }


@router.get("/emi-calculator")
async def calculate_emi(
    loan_amount: float,
    interest_rate: float,
    tenure_months: int
):
    """
    Calculate EMI for given loan parameters
    
    Args:
        loan_amount: Principal loan amount
        interest_rate: Annual interest rate (percentage)
        tenure_months: Loan tenure in months
    """
    try:
        r = interest_rate / (12 * 100)  # Monthly interest rate
        n = tenure_months
        
        if r > 0:
            # EMI formula: P × r × (1 + r)^n / ((1 + r)^n - 1)
            emi = loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)
        else:
            emi = loan_amount / n
        
        total_payment = emi * n
        total_interest = total_payment - loan_amount
        
        return {
            "loan_amount": round(loan_amount, 2),
            "interest_rate": interest_rate,
            "tenure_months": tenure_months,
            "monthly_emi": round(emi, 2),
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
            "principal_percentage": round((loan_amount / total_payment) * 100, 2),
            "interest_percentage": round((total_interest / total_payment) * 100, 2)
        }
        
    except Exception as e:
        logger.error(f"EMI calculation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== HEALTH CHECK ==================== #

@router.get("/health")
async def health_check():
    """Check if loan service is operational"""
    
    if loan_service.model is None:
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "message": "Loan model not loaded"
        }
    
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_features": loan_service.model.n_features_in_,
        "message": "Loan service operational"
    }