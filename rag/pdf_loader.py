"""
PDF Loader - Extracts text from government/bank PDFs
Handles Hindi and English text
"""

import os
from typing import List, Dict
from pypdf import PdfReader
from loguru import logger
import re


class PDFLoader:
    def __init__(self, pdf_directory: str = "data/pdfs"):
        self.pdf_directory = pdf_directory
        
    def load_single_pdf(self, filepath: str) -> Dict[str, str]:
        """
        Load a single PDF and extract text
        
        Returns:
            Dict with 'filename', 'text', 'pages'
        """
        try:
            reader = PdfReader(filepath)
            text = ""
            
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num} ---\n{page_text}"
            
            # Clean text
            text = self._clean_text(text)
            
            filename = os.path.basename(filepath)
            logger.info(f"✅ Loaded {filename}: {len(text)} characters")
            
            return {
                'filename': filename,
                'text': text,
                'pages': len(reader.pages),
                'source': filepath
            }
            
        except Exception as e:
            logger.error(f"❌ Error loading {filepath}: {e}")
            return None
    
    def load_all_pdfs(self) -> List[Dict[str, str]]:
        """
        Load all PDFs from the directory
        """
        documents = []
        
        if not os.path.exists(self.pdf_directory):
            logger.warning(f"📁 PDF directory not found: {self.pdf_directory}")
            return documents
        
        pdf_files = [f for f in os.listdir(self.pdf_directory) if f.endswith('.pdf')]
        
        logger.info(f"📚 Found {len(pdf_files)} PDFs to load")
        
        for pdf_file in pdf_files:
            filepath = os.path.join(self.pdf_directory, pdf_file)
            doc = self.load_single_pdf(filepath)
            if doc:
                documents.append(doc)
        
        logger.info(f"✅ Successfully loaded {len(documents)} documents")
        return documents
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text - handle Hindi/English mixed content
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Hindi/English
        text = re.sub(r'[^\w\s\u0900-\u097F.,;:!?()\-\'\"\/]', '', text)
        
        # Remove page numbers pattern
        text = re.sub(r'Page \d+', '', text)
        
        return text.strip()


# Test function
if __name__ == "__main__":
    loader = PDFLoader()
    docs = loader.load_all_pdfs()
    for doc in docs:
        print(f"📄 {doc['filename']}: {doc['pages']} pages, {len(doc['text'])} chars")