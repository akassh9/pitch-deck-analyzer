"""
Tests for the PDF controller.
"""

import unittest
from unittest.mock import patch, MagicMock
import io
import json
from werkzeug.datastructures import FileStorage
from ..api.pdf_controller import upload_pdf, get_job_status, cleanup_job
from ..core.pdf_service import PDFService
from ..infrastructure.job_store import JobStore

class TestPDFController(unittest.TestCase):
    
    def setUp(self):
        self.app = MagicMock()
        self.app.config = {
            'UPLOAD_FOLDER': '/tmp/uploads',
            'MAX_CONTENT_LENGTH': 10 * 1024 * 1024  # 10MB
        }
        
        # Mock request context
        self.request_ctx = MagicMock()
        self.request_ctx.app = self.app
        
        # Mock PDF service
        self.pdf_service = MagicMock(spec=PDFService)
        
        # Mock job store
        self.job_store = MagicMock(spec=JobStore)
        
        # Mock Flask's g object
        self.g = MagicMock()
        self.g.pdf_service = self.pdf_service
        self.g.job_store = self.job_store
    
    @patch('backend.api.pdf_controller.request')
    @patch('backend.api.pdf_controller.g', new_callable=MagicMock)
    @patch('backend.api.pdf_controller.current_app')
    @patch('backend.api.pdf_controller.jsonify')
    def test_upload_pdf_success(self, mock_jsonify, mock_current_app, mock_g, mock_request):
        # Setup mocks
        mock_current_app.config = self.app.config
        mock_g.pdf_service = self.pdf_service
        mock_g.job_store = self.job_store
        
        # Create a mock file
        mock_file = FileStorage(
            stream=io.BytesIO(b'PDF content'),
            filename='test.pdf',
            content_type='application/pdf'
        )
        mock_request.files = {'file': mock_file}
        
        # Mock job creation
        job_id = 'test-job-id'
        self.job_store.create_job.return_value = job_id
        
        # Mock jsonify response
        mock_jsonify.return_value = {'job_id': job_id}
        
        # Call the function
        result = upload_pdf()
        
        # Assertions
        self.job_store.create_job.assert_called_once()
        self.pdf_service.process_pdf_async.assert_called_once()
        mock_jsonify.assert_called_once_with({'job_id': job_id})
        
    @patch('backend.api.pdf_controller.request')
    @patch('backend.api.pdf_controller.g', new_callable=MagicMock)
    @patch('backend.api.pdf_controller.current_app')
    @patch('backend.api.pdf_controller.jsonify')
    def test_upload_pdf_no_file(self, mock_jsonify, mock_current_app, mock_g, mock_request):
        # Setup mocks
        mock_current_app.config = self.app.config
        mock_g.pdf_service = self.pdf_service
        mock_g.job_store = self.job_store
        
        # No file in request
        mock_request.files = {}
        
        # Mock jsonify response
        mock_jsonify.return_value = {'error': 'No file part'}
        mock_jsonify.return_value.status_code = 400
        
        # Call the function
        result = upload_pdf()
        
        # Assertions
        self.job_store.create_job.assert_not_called()
        self.pdf_service.process_pdf_async.assert_not_called()
        mock_jsonify.assert_called_once_with({'error': 'No file part'})
        
    @patch('backend.api.pdf_controller.request')
    @patch('backend.api.pdf_controller.g', new_callable=MagicMock)
    @patch('backend.api.pdf_controller.jsonify')
    def test_get_job_status(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.job_store = self.job_store
        
        # Mock job ID in request
        job_id = 'test-job-id'
        mock_request.args = {'job_id': job_id}
        
        # Mock job status
        job_status = {
            'job_id': job_id,
            'status': 'completed',
            'progress': 100,
            'result': 'Extracted text',
            'error': None
        }
        self.job_store.get_job.return_value = job_status
        
        # Mock jsonify response
        mock_jsonify.return_value = job_status
        
        # Call the function
        result = get_job_status()
        
        # Assertions
        self.job_store.get_job.assert_called_once_with(job_id)
        mock_jsonify.assert_called_once_with(job_status)
        
    @patch('backend.api.pdf_controller.request')
    @patch('backend.api.pdf_controller.g', new_callable=MagicMock)
    @patch('backend.api.pdf_controller.jsonify')
    def test_get_job_status_not_found(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.job_store = self.job_store
        
        # Mock job ID in request
        job_id = 'nonexistent-job-id'
        mock_request.args = {'job_id': job_id}
        
        # Mock job not found
        self.job_store.get_job.return_value = None
        
        # Mock jsonify response
        mock_jsonify.return_value = {'error': f'Job {job_id} not found'}
        mock_jsonify.return_value.status_code = 404
        
        # Call the function
        result = get_job_status()
        
        # Assertions
        self.job_store.get_job.assert_called_once_with(job_id)
        mock_jsonify.assert_called_once_with({'error': f'Job {job_id} not found'})
        
    @patch('backend.api.pdf_controller.request')
    @patch('backend.api.pdf_controller.g', new_callable=MagicMock)
    @patch('backend.api.pdf_controller.jsonify')
    def test_cleanup_job(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.job_store = self.job_store
        
        # Mock job ID in request
        job_id = 'test-job-id'
        mock_request.args = {'job_id': job_id}
        
        # Mock cleanup success
        self.job_store.delete_job.return_value = True
        
        # Mock jsonify response
        mock_jsonify.return_value = {'success': True}
        
        # Call the function
        result = cleanup_job()
        
        # Assertions
        self.job_store.delete_job.assert_called_once_with(job_id)
        mock_jsonify.assert_called_once_with({'success': True})
        
    @patch('backend.api.pdf_controller.request')
    @patch('backend.api.pdf_controller.g', new_callable=MagicMock)
    @patch('backend.api.pdf_controller.jsonify')
    def test_cleanup_job_not_found(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.job_store = self.job_store
        
        # Mock job ID in request
        job_id = 'nonexistent-job-id'
        mock_request.args = {'job_id': job_id}
        
        # Mock cleanup failure
        self.job_store.delete_job.return_value = False
        
        # Mock jsonify response
        mock_jsonify.return_value = {'error': f'Job {job_id} not found or could not be deleted'}
        mock_jsonify.return_value.status_code = 404
        
        # Call the function
        result = cleanup_job()
        
        # Assertions
        self.job_store.delete_job.assert_called_once_with(job_id)
        mock_jsonify.assert_called_once_with({'error': f'Job {job_id} not found or could not be deleted'})

if __name__ == '__main__':
    unittest.main() 