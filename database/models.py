"""
Database Models - PostgreSQL tables using SQLAlchemy
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User information from Telegram"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.telegram_id} - {self.first_name}>"


class LoanQuery(Base):
    """Loan query history"""
    __tablename__ = 'loan_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    income = Column(Float)
    age = Column(Integer)
    employment_type = Column(String(50))
    credit_score = Column(Integer)
    loan_amount_requested = Column(Float)
    loan_purpose = Column(String(100))
    
    # Results
    eligible = Column(Boolean)
    recommended_amount = Column(Float)
    emi = Column(Float)
    interest_rate = Column(Float)
    confidence = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<LoanQuery {self.id} - User {self.user_telegram_id}>"


class FraudCheck(Base):
    """Fraud detection history"""
    __tablename__ = 'fraud_checks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    scheme_name = Column(String(200))
    scheme_description = Column(Text)
    
    # Results
    is_fraud = Column(Boolean)
    confidence = Column(Float)
    fraud_signals = Column(JSON)
    verified = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FraudCheck {self.id} - {self.scheme_name}>"


class RAGQuery(Base):
    """RAG chatbot query history"""
    __tablename__ = 'rag_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    question = Column(Text)
    answer = Column(Text)
    sources = Column(JSON)
    confidence = Column(Float)
    language = Column(String(10))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RAGQuery {self.id} - User {self.user_telegram_id}>"


class Conversation(Base):
    """Conversation history for context"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    message_type = Column(String(20))  # 'user', 'bot'
    message_text = Column(Text)
    message_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation {self.id}>"


class UserPreference(Base):
    """User settings like language and advisory preference"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id = Column(String(50), unique=True, nullable=False)  # Changed from telegram_id
    
    preferred_language = Column(String(10), default="hi")
    location = Column(String(100), default="Delhi")  # Added location field
    advisory_enabled = Column(Boolean, default=True)  # Changed from receive_daily_advisory
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreference {self.telegram_user_id}>"


class DocumentAnalysis(Base):
    """Stores uploaded bank documents / PDFs / images"""
    __tablename__ = "document_analysis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    
    original_text = Column(Text)
    simplified_text = Column(Text)
    detected_language = Column(String(10))
    translated_text = Column(Text)
    
    action_steps = Column(JSON)
    audio_file_path = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DocumentAnalysis {self.id}>"


class DailyAdvisoryLog(Base):
    """Tracks daily voice advisory delivery"""
    __tablename__ = "daily_advisory_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    
    weather_summary = Column(Text)
    mandi_prices = Column(JSON)
    scheme_reminders = Column(JSON)
    emi_alert = Column(Text)
    
    audio_file_path = Column(String(255))
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DailyAdvisoryLog {self.id}>"