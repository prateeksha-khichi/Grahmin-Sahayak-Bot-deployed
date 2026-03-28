"""
Reset Database - Drops and recreates all tables
⚠️ WARNING: This deletes ALL data!
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from database.db import engine, init_db
from database.models import Base

def reset_database():
    """Drop all tables and recreate them"""
    
    print("⚠️  WARNING: This will delete ALL data!")
    print("⚠️  Dropping all tables in 3 seconds...")
    
    import time
    time.sleep(3)
    
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    print("✅ All tables dropped")
    
    print("Creating fresh tables...")
    init_db()
    
    print("=" * 60)
    print("✅ Database reset complete!")
    print("=" * 60)
    print("Tables created:")
    print("  - users")
    print("  - loan_queries")
    print("  - fraud_checks")
    print("  - rag_queries")
    print("  - conversations")
    print("  - user_preferences ✨")
    print("  - document_analysis")
    print("  - daily_advisory_logs")

if __name__ == "__main__":
    reset_database()