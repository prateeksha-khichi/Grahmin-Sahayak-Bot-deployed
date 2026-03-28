"""
Text Chunker - Memory-safe document chunking
Optimized for Hindi/English mixed content
"""

from typing import List, Dict
from loguru import logger
import os


class TextChunker:
    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        self.chunk_size = int(os.getenv("CHUNK_SIZE", chunk_size))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", chunk_overlap))

        # HARD safety limits
        self.MAX_TEXT_LENGTH = 100_000      # max chars per document
        self.MAX_CHUNKS_PER_DOC = 200       # prevents RAM explosion

    def chunk_document(self, document: Dict[str, str]) -> List[Dict[str, str]]:
        text = document.get("text", "")
        filename = document.get("filename", "unknown")

        if not text or len(text) < 50:
            return []

        # Trim very large documents
        if len(text) > self.MAX_TEXT_LENGTH:
            logger.warning(f"⚠️ Trimming large document: {filename}")
            text = text[:self.MAX_TEXT_LENGTH]

        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text) and chunk_id < self.MAX_CHUNKS_PER_DOC:
            end = start + self.chunk_size

            # Sentence boundary detection (Hindi + English)
            if end < len(text):
                for boundary in ["। ", ". ", "? ", "! ", "\n"]:
                    pos = text.rfind(boundary, start, end)
                    if pos != -1:
                        end = pos + 1
                        break

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "source": filename,
                    "chunk_id": chunk_id,
                    "start_char": start,
                    "end_char": end
                })
                chunk_id += 1

            start = max(end - self.chunk_overlap, start + 1)

        logger.info(f"📝 Chunked {filename}: {len(chunks)} chunks")
        return chunks

    def chunk_documents(self, documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        ⚠️ Use only for SMALL datasets
        """
        all_chunks = []

        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))

        logger.info(f"✅ Total chunks created: {len(all_chunks)}")
        return all_chunks
