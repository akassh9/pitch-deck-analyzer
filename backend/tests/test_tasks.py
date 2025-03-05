"""
Tests for the tasks module.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from ..tasks import process_pdf, generate_memo
from ..core.pdf_service import PDFService
from ..core.memo_service import MemoService
from ..infrastructure.job_store import JobStore

class TestTasks(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock services
        self.pdf_service = MagicMock(spec=PDFService)
        self.memo_service = MagicMock(spec=MemoService)
        self.job_store = MagicMock(spec=JobStore)
        
        # Create a temporary PDF file
        self.pdf_path = os.path.join(self.temp_dir, 'test.pdf')
        with open(self.pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF file')
    
    def tearDown(self):
        # Remove the temporary PDF file
        os.remove(self.pdf_path)
        
        # Remove the temporary directory
        os.rmdir(self.temp_dir)
    
    @patch('backend.tasks.get_pdf_service')
    @patch('backend.tasks.get_job_store')
    def test_process_pdf(self, mock_get_job_store, mock_get_pdf_service):
        # Setup mocks
        mock_get_pdf_service.return_value = self.pdf_service
        mock_get_job_store.return_value = self.job_store
        
        # Mock PDF processing
        extracted_text = "Extracted text from PDF"
        self.pdf_service.process_pdf.return_value = extracted_text
        
        # Call the function
        job_id = 'test-job-id'
        result = process_pdf(job_id, self.pdf_path)
        
        # Assertions
        self.assertEqual(result, extracted_text)
        self.pdf_service.process_pdf.assert_called_once_with(self.pdf_path, job_id)
        mock_get_pdf_service.assert_called_once()
        mock_get_job_store.assert_called_once()
    
    @patch('backend.tasks.get_memo_service')
    @patch('backend.tasks.get_job_store')
    def test_generate_memo(self, mock_get_job_store, mock_get_memo_service):
        # Setup mocks
        mock_get_memo_service.return_value = self.memo_service
        mock_get_job_store.return_value = self.job_store
        
        # Mock memo generation
        generated_memo = "# Investment Memo\n\nThis is a sample investment memo."
        self.memo_service.generate_memo.return_value = generated_memo
        
        # Call the function
        job_id = 'test-job-id'
        text = "Extracted text from PDF"
        result = generate_memo(job_id, text)
        
        # Assertions
        self.assertEqual(result, generated_memo)
        self.memo_service.generate_memo.assert_called_once_with(text)
        mock_get_memo_service.assert_called_once()
        mock_get_job_store.assert_called_once()
    
    @patch('backend.tasks.get_pdf_service')
    @patch('backend.tasks.get_job_store')
    def test_process_pdf_error(self, mock_get_job_store, mock_get_pdf_service):
        # Setup mocks
        mock_get_pdf_service.return_value = self.pdf_service
        mock_get_job_store.return_value = self.job_store
        
        # Mock PDF processing error
        error_message = "PDF processing error"
        self.pdf_service.process_pdf.side_effect = Exception(error_message)
        
        # Call the function
        job_id = 'test-job-id'
        
        # Check that the exception is raised
        with self.assertRaises(Exception) as context:
            process_pdf(job_id, self.pdf_path)
        
        # Check that the error message is correct
        self.assertEqual(str(context.exception), error_message)
        
        # Check that the job was updated with the error
        self.job_store.update_job.assert_called_with(
            job_id,
            status='failed',
            error=error_message
        )
    
    @patch('backend.tasks.get_memo_service')
    @patch('backend.tasks.get_job_store')
    def test_generate_memo_error(self, mock_get_job_store, mock_get_memo_service):
        # Setup mocks
        mock_get_memo_service.return_value = self.memo_service
        mock_get_job_store.return_value = self.job_store
        
        # Mock memo generation error
        error_message = "Memo generation error"
        self.memo_service.generate_memo.side_effect = Exception(error_message)
        
        # Call the function
        job_id = 'test-job-id'
        text = "Extracted text from PDF"
        
        # Check that the exception is raised
        with self.assertRaises(Exception) as context:
            generate_memo(job_id, text)
        
        # Check that the error message is correct
        self.assertEqual(str(context.exception), error_message)
        
        # Check that the job was updated with the error
        self.job_store.update_job.assert_called_with(
            job_id,
            status='failed',
            error=error_message
        )

if __name__ == '__main__':
    unittest.main() 