"""
PDF processing service for extracting and preparing text from PDF files.
This module provides functionality to extract text from PDFs using multiple methods,
including OCR when necessary.
"""

import os
import time
import logging
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from ..utils.error_handling import ProcessingError
from ..infrastructure.job_manager import update_job

logger = logging.getLogger(__name__)

class PDFService:
    """Service for processing PDF files."""
    
    def __init__(self, config):
        """Initialize the PDF service with configuration."""
        self.config = config
        self.upload_folder = config.UPLOAD_FOLDER
        logger.info(f"Initialized PDFService with upload folder: {self.upload_folder}")
    
    def process_pdf(self, file_path: str, job_id: str = None) -> dict:
        """
        Process a PDF file and extract its contents.
        
        Args:
            file_path (str): Path to the PDF file
            job_id (str): Optional job ID for tracking progress
            
        Returns:
            dict: Dictionary containing processed text and metadata
        """
        try:
            if job_id:
                update_job(job_id, {"status": "extracting"})
            
            extracted_text = self._extract_text(file_path, job_id)
            
            if job_id:
                update_job(job_id, {"status": "refining"})
            
            result = self.prepare_text(extracted_text, refine=True)
            
            if job_id:
                update_job(job_id, {
                    "status": "completed",
                    "result": {
                        "cleaned_text": result["cleaned_text"],
                        "startup_stage": result["startup_stage"]
                    }
                })
            
            return {
                "success": True,
                "cleaned_text": result["cleaned_text"],
                "startup_stage": result["startup_stage"]
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            if job_id:
                update_job(job_id, {
                    "status": "error",
                    "error": str(e)
                })
            raise
    
    def _extract_text(self, file_path, job_id):
        """
        Extract text from PDF using multiple methods.
        
        Args:
            file_path (str): Path to the PDF file
            job_id (str): ID of the job to update progress
            
        Returns:
            str: The extracted text
        """
        from ..utils.text_processing import is_noise_page, needs_ocr, ocr_page
        
        extracted_text = ""
        
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            logger.info(f"PDF has {total_pages} pages")
            
            for i in range(total_pages):
                page = reader.pages[i]
                page_text = page.extract_text() or ""
                
                # Try pdfplumber if PyPDF2 result needs OCR
                if needs_ocr(page_text):
                    logger.debug(f"Page {i+1} needs better extraction, trying pdfplumber")
                    try:
                        with pdfplumber.open(file_path) as pdf:
                            page_plumber = pdf.pages[i]
                            page_text_alt = page_plumber.extract_text() or ""
                            if len(page_text_alt.strip()) > len(page_text.strip()):
                                page_text = page_text_alt
                                logger.debug(f"Used pdfplumber for page {i+1}")
                    except Exception as e:
                        logger.warning(f"pdfplumber error on page {i+1}: {str(e)}")
                
                # Try OCR if still needed
                if needs_ocr(page_text):
                    logger.debug(f"Page {i+1} still needs OCR")
                    try:
                        images = convert_from_path(file_path, dpi=300, first_page=i+1, last_page=i+1)
                        if images:
                            page_text = ocr_page(images[0])
                            logger.debug(f"Used OCR for page {i+1}")
                    except Exception as e:
                        logger.warning(f"OCR error on page {i+1}: {str(e)}")
                
                # Add page text if it's not noise
                if not is_noise_page(page_text):
                    extracted_text += page_text + "\n"
                else:
                    logger.debug(f"Skipped noise page {i+1}")
                
                # Update progress
                progress = int(((i + 1) / total_pages) * 80)
                update_job(job_id, {"progress": progress})
                logger.debug(f"Updated progress to {progress}% after processing page {i+1}")
                
                # Small delay to prevent overloading the system
                time.sleep(0.1)
        
        update_job(job_id, {"progress": 90, "status": "refining"})
        logger.info(f"Extraction complete for job {job_id}, extracted {len(extracted_text)} characters")
        
        return extracted_text

    def prepare_text(self, text, refine=True):
        """
        Prepare the extracted text.
        
        Args:
            text (str): The extracted text
            refine (bool): Whether to refine the text
            
        Returns:
            dict: Dictionary containing processed text and metadata
        """
        from ..utils.text_processing import prepare_text
        return prepare_text(text, refine=refine)

# Create a singleton instance
_pdf_service = None

def get_pdf_service(config=None):
    """Get the singleton PDFService instance."""
    global _pdf_service
    
    if _pdf_service is None:
        from ..infrastructure.config import Config
        _pdf_service = PDFService(config or Config)
        
    return _pdf_service 