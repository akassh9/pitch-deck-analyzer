"""
Tests for the PDF service.
"""

import unittest
from unittest.mock import patch, MagicMock
from ..core.pdf_service import PDFService
from ..config import Config
from ..utils.error_handling import ProcessingError
from unittest.mock import call

class TestPDFService(unittest.TestCase):
    
    def setUp(self):
        self.config = MagicMock()
        self.config.UPLOAD_FOLDER = "test_uploads"
        self.pdf_service = PDFService(self.config)
        
    @patch('backend.infrastructure.job_manager.update_job')
    @patch('backend.core.pdf_service.PDFService._extract_text')
    @patch('backend.utils.text_processing.prepare_text')
    def test_process_pdf_success(self, mock_prepare_text, mock_extract_text, mock_update_job):
        """Test successful PDF processing."""
        # Setup
        mock_extract_text.return_value = "Raw text from PDF"
        mock_prepare_text.return_value = {
            "cleaned_text": "Prepared text from PDF",
            "startup_stage": "seed"
        }
        
        # Process PDF
        result = self.pdf_service.process_pdf("test.pdf", "job123")
        
        # Verify calls
        mock_extract_text.assert_called_once()
        mock_prepare_text.assert_called_once_with("Raw text from PDF", refine=True)
        
        # Verify job updates
        mock_update_job.assert_has_calls([
            call("job123", {"status": "extracting"}),
            call("job123", {"status": "refining"}),
            call("job123", {
                "status": "completed",
                "result": {
                    "text": "Prepared text from PDF",
                    "startup_stage": "seed"
                }
            })
        ])
        
        # Verify result
        self.assertEqual(result, {
            "success": True,
            "text": "Prepared text from PDF",
            "startup_stage": "seed"
        })
        
    @patch('backend.infrastructure.job_manager.update_job')
    @patch('backend.core.pdf_service.PDFService._extract_text')
    def test_process_pdf_failure(self, mock_extract_text, mock_update_job):
        # Setup mocks
        mock_extract_text.side_effect = Exception("Test error")
        
        # Call the method and check exception
        with self.assertRaises(ProcessingError):
            self.pdf_service.process_pdf("test.pdf", "job123")
        
        # Check job updates
        mock_update_job.assert_any_call("job123", {"status": "processing", "progress": 10})
        mock_update_job.assert_any_call("job123", {"status": "failed", "error": "Test error"})

if __name__ == '__main__':
    unittest.main() 