"""
Retriever - High-level interface for semantic search
Combines embedder and vector store
"""

from typing import List, Dict, Tuple
from loguru import logger
from .embedder import Embedder
from .vector_store import VectorStore
import os


class Retriever:
    def __init__(self, vector_store: VectorStore, embedder: Embedder):
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = int(os.getenv('TOP_K_RESULTS', 3))
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, any]]:
        """
        Retrieve most relevant chunks for a query
        
        Args:
            query: User question in Hindi/English
            top_k: Number of results (default from env)
        
        Returns:
            List of dicts with 'text', 'source', 'score'
        """
        if top_k is None:
            top_k = self.top_k
        
        logger.info(f"🔍 Retrieving for query: {query[:50]}...")
        
        # Embed query
        query_embedding = self.embedder.embed_query(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, k=top_k)
        
        # Format results
        formatted_results = []
        for chunk, score in results:
            formatted_results.append({
                'text': chunk['text'],
                'source': chunk.get('source', 'unknown'),
                'score': score,
                'chunk_id': chunk.get('chunk_id', -1)
            })
        
        logger.info(f"✅ Retrieved {len(formatted_results)} relevant chunks")
        return formatted_results
    
    def retrieve_with_context(self, query: str, top_k: int = None) -> str:
        """
        Retrieve and format context for LLM
        
        Returns:
            Formatted context string
        """
        results = self.retrieve(query, top_k)
        
        if not results:
            return "कोई प्रासंगिक जानकारी नहीं मिली। (No relevant information found.)"
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"संदर्भ {i} (स्रोत: {result['source']}):\n{result['text']}\n"
            )
        
        return "\n".join(context_parts)


# Test function
if __name__ == "__main__":
    # This requires a built vector store
    embedder = Embedder()
    vector_store = VectorStore()
    
    if vector_store.load():
        retriever = Retriever(vector_store, embedder)
        
        queries = [
            "प्रधानमंत्री मुद्रा योजना क्या है?",
            "What is the eligibility for Kisan Credit Card?",
            "ऋण की ब्याज दर क्या है?"
        ]
        
        for query in queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")
            
            results = retriever.retrieve(query)
            for r in results:
                print(f"\n✓ Score: {r['score']:.4f} | Source: {r['source']}")
                print(f"  {r['text'][:200]}...")
    else:
        print("⚠️ Please build the index first using rag_pipeline.py")