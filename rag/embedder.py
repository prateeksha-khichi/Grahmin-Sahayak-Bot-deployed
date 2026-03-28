"""
Embedder - Converts text chunks to vector embeddings
Uses multilingual sentence-transformers (FREE, offline)
"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
import os


class Embedder:
    def __init__(self, model_name: str = None):
        """
        Initialize multilingual embedding model
        Supports Hindi, English, and 50+ languages
        """
        if model_name is None:
            model_name = os.getenv(
                'EMBEDDING_MODEL',
                'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
            )
        
        logger.info(f"🔄 Loading embedding model: {model_name}")
        
        # Cache directory
        cache_dir = "models/embeddings/sentence_transformer"
        os.makedirs(cache_dir, exist_ok=True)
        
        self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"✅ Model loaded - Dimension: {self.dimension}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_chunks(self, chunks: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple chunks efficiently
        
        Returns:
            numpy array of shape (n_chunks, embedding_dim)
        """
        logger.info(f"🔄 Embedding {len(chunks)} chunks...")
        
        embeddings = self.model.encode(
            chunks,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        logger.info(f"✅ Embeddings created: {embeddings.shape}")
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed user query (same as embed_text, but explicit for clarity)
        """
        return self.embed_text(query)


# Test function
if __name__ == "__main__":
    embedder = Embedder()
    
    # Test Hindi and English
    texts = [
        "प्रधानमंत्री मुद्रा योजना क्या है?",
        "What is Kisan Credit Card?",
        "ऋण के लिए पात्रता मानदंड"
    ]
    
    for text in texts:
        embedding = embedder.embed_text(text)
        print(f"Text: {text}")
        print(f"Embedding shape: {embedding.shape}")
        print(f"First 5 values: {embedding[:5]}\n")