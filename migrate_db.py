"""
Database Migration - Add telegram_user_id column
Safe migration that preserves existing data
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from database.db import engine

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except:
        return False

def check_table_exists(table_name: str) -> bool:
    """Check if a table exists"""
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except:
        return False

def migrate_user_preferences():
    """Add telegram_user_id column if it doesn't exist"""
    
    print("=" * 60)
    print("🔧 Starting migration for user_preferences table...")
    print("=" * 60)
    
    # Check if table exists
    if not check_table_exists('user_preferences'):
        print("⚠️  Table 'user_preferences' does not exist.")
        print("Creating all tables...")
        from database.db import init_db
        init_db()
        print("✅ All tables created!")
        return
    
    # Check if telegram_user_id already exists
    if check_column_exists('user_preferences', 'telegram_user_id'):
        print("✅ Column 'telegram_user_id' already exists!")
        print("✅ No migration needed. Database is up to date.")
        return
    
    # Perform migration
    with engine.connect() as conn:
        try:
            print("\n📝 Migration steps:")
            print("  1. Adding telegram_user_id column...")
            
            # Add the new column
            conn.execute(text("""
                ALTER TABLE user_preferences 
                ADD COLUMN telegram_user_id VARCHAR(50)
            """))
            print("     ✅ Column added")
            
            # If old telegram_id column exists, copy data
            if check_column_exists('user_preferences', 'telegram_id'):
                print("  2. Copying data from telegram_id to telegram_user_id...")
                conn.execute(text("""
                    UPDATE user_preferences 
                    SET telegram_user_id = telegram_id
                """))
                print("     ✅ Data copied")
                
                print("  3. Dropping old telegram_id column...")
                conn.execute(text("""
                    ALTER TABLE user_preferences 
                    DROP COLUMN telegram_id
                """))
                print("     ✅ Old column removed")
            
            # Add unique constraint
            print("  4. Adding unique constraint...")
            conn.execute(text("""
                ALTER TABLE user_preferences 
                ADD CONSTRAINT user_preferences_telegram_user_id_key 
                UNIQUE (telegram_user_id)
            """))
            print("     ✅ Constraint added")
            
            conn.commit()
            
            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)
            print("\n✨ Database is now ready to use!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            print("\n💡 Suggestion: Try running reset_db.py instead:")
            print("   python reset_db.py")
            raise

if __name__ == "__main__":
    migrate_user_preferences()