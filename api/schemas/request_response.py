"""
Pydantic schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Loan Schemas
class LoanRequest(BaseModel):
    income: float = Field(..., gt=0, description="Monthly income in INR")
    age: int = Field(..., ge=18, le=70, description="Age of applicant")
    employment_type: str = Field(..., description="salaried/self_employed/farmer")
    credit_score: int = Field(650, ge=300, le=900, description="Credit score")
    existing_loan: float = Field(0, ge=0, description="Existing loan amount")
    loan_amount_requested: float = Field(..., gt=0, description="Requested loan amount")
    loan_purpose: str = Field(..., description="Purpose of loan")


class LoanResponse(BaseModel):
    eligible: bool
    confidence: float
    recommended_amount: float
    emi: float
    interest_rate: float
    tenure_months: int
    message_hindi: str
    message_english: str


# Fraud Schemas
class FraudRequest(BaseModel):
    scheme_name: str = Field(..., min_length=1)
    description: str = Field("", description="Scheme description")
    source: str = Field("", description="Source of scheme")
    contact: str = Field("", description="Contact information")


class FraudResponse(BaseModel):
    is_fraud: bool
    confidence: float
    fraud_signals: List[str]
    warning_message_hindi: str
    warning_message_english: str
    verified: bool


# RAG Schemas
class RAGRequest(BaseModel):
    question: str = Field(..., min_length=1)
    language: str = Field("hindi", description="Response language")
    include_sources: bool = Field(True)


class RAGResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float


# General
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: dict