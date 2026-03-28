"""
Database Manager - Handles PostgreSQL/SQLite connections
Enhanced version with helper methods for saving data
"""

import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from database.models import (
    Base, 
    User, 
    LoanQuery, 
    FraudCheck, 
    RAGQuery, 
    Conversation,
    UserPreference,
    DocumentAnalysis,
    DailyAdvisoryLog
)


class DatabaseManager:
    """
    Singleton Database Manager with helper methods
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Load database URL
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./gramin_sahayak.db")

        # Create engine
        self.engine = create_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Create tables
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")

        self._initialized = True

    def get_session(self) -> Session:
        """Returns a new SQLAlchemy session"""
        return self.SessionLocal()
    
    # ==================== HELPER METHODS ==================== #
    
    def save_loan_query(self, data: dict):
        """Save loan query to database"""
        session = self.get_session()
        try:
            loan_query = LoanQuery(**data)
            session.add(loan_query)
            session.commit()
            logger.info(f"✅ Saved loan query for user {data.get('user_telegram_id')}")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error saving loan query: {e}")
        finally:
            session.close()
    
    def save_fraud_check(self, data: dict):
        """Save fraud check to database"""
        session = self.get_session()
        try:
            fraud_check = FraudCheck(**data)
            session.add(fraud_check)
            session.commit()
            logger.info(f"✅ Saved fraud check for user {data.get('user_telegram_id')}")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error saving fraud check: {e}")
        finally:
            session.close()
    
    def save_rag_query(self, data: dict):
        """Save RAG query to database"""
        session = self.get_session()
        try:
            rag_query = RAGQuery(**data)
            session.add(rag_query)
            session.commit()
            logger.info(f"✅ Saved RAG query for user {data.get('user_telegram_id')}")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error saving RAG query: {e}")
        finally:
            session.close()


# Global singleton instance
db_manager = DatabaseManager()
db = db_manager


def get_db():
    """
    FastAPI dependency for routes
    
    Usage:
        from database.db_manager import get_db
        from fastapi import Depends
        
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()