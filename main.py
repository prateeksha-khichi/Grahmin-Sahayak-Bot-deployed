"""
Main Entry Point - Choose what to run
"""

import sys
import os
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.file_utils import init_project_directories


def main():
    """Main entry point"""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           🌾 GRAMIN SAHAYAK BOT 🌾                      ║
║        Rural Financial Literacy Assistant               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Choose what to run:

1️⃣  Build RAG Index (First time setup)
2️⃣  Run Telegram Bot
3️⃣  Run FastAPI Server
4️⃣  Run Both (Bot + API)
5️⃣  Test Services
6️⃣  Exit

""")
    
    choice = input("Enter your choice (1-6): ").strip()
    
    # Initialize directories
    init_project_directories()
    
    if choice == "1":
        logger.info("🔨 Building RAG Index...")
        from rag.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline()
        pipeline.build_index(force_rebuild=True)
        logger.info("✅ Index built! You can now run the bot or API.")
        
    elif choice == "2":
        logger.info("🤖 Starting Telegram Bot...")
        from bots.telegram_bot import GraminSahayakBot
        bot = GraminSahayakBot()
        bot.run()
        
    elif choice == "3":
        logger.info("🌐 Starting FastAPI Server...")
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
        
    elif choice == "4":
        logger.info("🚀 Starting Both Bot and API...")
        import asyncio
        import uvicorn
        from bots.telegram_bot import GraminSahayakBot
        
        async def run_both():
            # Start API in background
            config = uvicorn.Config("api.main:app", host="0.0.0.0", port=8000)
            server = uvicorn.Server(config)
            
            # Start bot
            bot = GraminSahayakBot()
            
            await asyncio.gather(
                server.serve(),
                bot.app.run_polling()
            )
        
        asyncio.run(run_both())
        
    elif choice == "5":
        logger.info("🧪 Running Tests...")
        test_services()
        
    elif choice == "6":
        logger.info("👋 Goodbye!")
        sys.exit(0)
        
    else:
        logger.error("❌ Invalid choice!")
        main()


def test_services():
    """Test all services"""
    print("\n" + "="*60)
    print("🧪 Testing Services")
    print("="*60 + "\n")
    
    # Test Loan Service
    print("1️⃣ Testing Loan Service...")
    from services.loan_service import LoanService
    loan_service = LoanService()
    
    test_user = {
        'income': 30000,
        'age': 28,
        'employment_type': 'salaried',
        'credit_score': 720,
        'existing_loan': 0,
        'loan_amount_requested': 300000,
        'loan_purpose': 'business'
    }
    
    result = loan_service.predict_eligibility(test_user)
    print(f"   ✅ Eligible: {result['eligible']}")
    print(f"   💰 Recommended: ₹{result['recommended_amount']:,.0f}")
    print(f"   📅 EMI: ₹{result['emi']:,.0f}\n")
    
    # Test Fraud Service
    print("2️⃣ Testing Fraud Service...")
    from services.fraud_service import FraudService
    fraud_service = FraudService()
    
    test_scheme = {
        'scheme_name': 'Instant Loan WhatsApp',
        'description': 'Get loan in 10 minutes, pay ₹500 first',
        'source': 'unknown',
        'contact': '9876543210'
    }
    
    fraud_result = fraud_service.detect_fraud(test_scheme)
    print(f"   ⚠️ Is Fraud: {fraud_result['is_fraud']}")
    print(f"   🎯 Confidence: {fraud_result['confidence']:.2f}")
    print(f"   🚩 Signals: {', '.join(fraud_result['fraud_signals'][:3])}\n")
    
    # Test RAG Service
    print("3️⃣ Testing RAG Service...")
    from services.rag_service import RAGService
    rag_service = RAGService()
    
    status = rag_service.get_service_status()
    print(f"   📊 RAG Status: {status['rag_status']}")
    print(f"   🤖 LLM Available: {status['llm_available']}")
    print(f"   📄 Total Documents: {status['total_documents']}\n")
    
    if status['service_healthy']:
        test_query = "मुद्रा योजना क्या है?"
        print(f"   🔍 Testing query: {test_query}")
        answer = rag_service.answer_question(test_query, language='hindi')
        print(f"   ✅ Answer: {answer['answer'][:150]}...\n")
    
    # Test Database
    print("4️⃣ Testing Database...")
    from database.db_manager import db
    
    test_user_db = db.get_or_create_user(
        telegram_id='test_123',
        first_name='Test',
        language_preference='hindi'
    )
    print(f"   ✅ User created: {test_user_db.telegram_id}\n")
    
    print("="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()