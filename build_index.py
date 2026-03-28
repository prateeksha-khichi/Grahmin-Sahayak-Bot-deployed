"""
Pre-build RAG index
Run this once to create the index files
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.rag_service import RAGService
from loguru import logger

def main():
    logger.info("🔄 Building RAG index...")
    
    try:
        # Initialize RAG service (will build index if needed)
        rag = RAGService()
        
        # Force initialization
        rag._ensure_initialized()
        
        logger.success("✅ RAG index built successfully!")
        logger.info(f"📁 Index saved in: data/processed/faiss_index/")
        
    except Exception as e:
        logger.error(f"❌ Failed to build index: {e}")
        raise

if __name__ == "__main__":
    main()