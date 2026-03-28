"""
OCR Service - Extract text from PDFs and images
"""

import pdfplumber
import easyocr
from PIL import Image
from typing import Optional
from loguru import logger
import io


class OCRService:
    """Extract text from documents using OCR"""
    
    def __init__(self):
        """Initialize EasyOCR reader for English and Hindi"""
        try:
            self.reader = easyocr.Reader(['en', 'hi'], gpu=False)
            logger.success("✅ OCR Service initialized (en, hi)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCR: {e}")
            self.reader = None
    
    def extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF using pdfplumber
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        logger.info(f"Extracted {len(page_text)} chars from page {page_num}")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def extract_from_image(self, file_path: str) -> str:
        """
        Extract text from image using EasyOCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text
        """
        if not self.reader:
            raise Exception("OCR reader not initialized")
        
        try:
            result = self.reader.readtext(file_path)
            text = " ".join([detection[1] for detection in result])
            
            logger.info(f"Extracted {len(text)} chars from image")
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ Image OCR failed: {e}")
            raise Exception(f"Image OCR failed: {str(e)}")
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Main extraction method - routes to appropriate extractor
        
        Args:
            file_path: Path to file
            file_type: File extension (pdf, jpg, png, etc.)
            
        Returns:
            Extracted text
        """
        file_type = file_type.lower().strip()
        
        if file_type == 'pdf':
            return self.extract_from_pdf(file_path)
        elif file_type in ['jpg', 'jpeg', 'png', 'webp', 'bmp']:
            return self.extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")