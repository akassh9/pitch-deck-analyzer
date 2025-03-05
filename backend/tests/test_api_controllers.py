"""
Tests for the API controllers.
"""

import unittest
import json
import io
from unittest.mock import patch, MagicMock
from ..app import create_app
from ..infrastructure.config import Config

class TestAPIControllers(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    def test_health_check(self):
        response = self.client.get('/')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['version'], '1.0.0')
        
    @patch('backend.api.pdf_controller.create_job')
    @patch('backend.tasks.process_pdf_task.delay')
    def test_upload_pdf(self, mock_process_task, mock_create_job):
        # Setup mocks
        mock_create_job.return_value = 'test_job_id'
        
        # Create a test file
        test_file = io.BytesIO(b'Test PDF content')
        test_file.name = 'test.pdf'
        
        # Make the request
        response = self.client.post(
            '/api/upload',
            data={'file': (test_file, 'test.pdf')},
            content_type='multipart/form-data'
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 202)
        self.assertEqual(data['job_id'], 'test_job_id')
        self.assertEqual(data['status'], 'processing')
        mock_create_job.assert_called_once()
        mock_process_task.assert_called_once()
        
    @patch('backend.api.memo_controller.create_job')
    @patch('backend.api.memo_controller.update_job')
    @patch('backend.tasks.generate_memo_task.delay')
    def test_generate_memo_api(self, mock_generate_task, mock_update_job, mock_create_job):
        # Setup mocks
        mock_create_job.return_value = 'test_job_id'
        
        # Make the request
        response = self.client.post(
            '/api/generate-memo',
            json={'text': 'Test text for memo generation'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 202)
        self.assertEqual(data['job_id'], 'test_job_id')
        self.assertEqual(data['status'], 'processing')
        mock_create_job.assert_called_once()
        mock_update_job.assert_called_once_with('test_job_id', {'status': 'processing'})
        mock_generate_task.assert_called_once_with('Test text for memo generation', 'test_job_id')
        
    @patch('backend.api.memo_controller.get_memo_service')
    def test_validate_selection(self, mock_get_memo_service):
        # Setup mocks
        mock_memo_service = MagicMock()
        mock_memo_service.validate_memo.return_value = [
            {'title': 'Result 1', 'snippet': 'Snippet 1', 'link': 'Link 1'},
            {'title': 'Result 2', 'snippet': 'Snippet 2', 'link': 'Link 2'}
        ]
        mock_get_memo_service.return_value = mock_memo_service
        
        # Make the request
        response = self.client.post(
            '/api/validate-selection',
            json={'text': 'Test text for validation'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['title'], 'Result 1')
        self.assertEqual(data[1]['title'], 'Result 2')
        mock_memo_service.validate_memo.assert_called_once_with('Test text for validation')
        
    @patch('backend.api.pdf_controller.get_job')
    def test_job_status(self, mock_get_job):
        # Setup mocks
        mock_get_job.return_value = {
            'job_id': 'test_job_id',
            'status': 'completed',
            'progress': 100,
            'result': 'Test result'
        }
        
        # Make the request
        response = self.client.get('/api/status?job_id=test_job_id')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['job_id'], 'test_job_id')
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['progress'], 100)
        self.assertEqual(data['result'], 'Test result')
        mock_get_job.assert_called_once_with('test_job_id')
        
    @patch('backend.api.pdf_controller.delete_job')
    def test_cleanup_job(self, mock_delete_job):
        # Make the request
        response = self.client.post(
            '/api/cleanup',
            json={'job_id': 'test_job_id'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        mock_delete_job.assert_called_once_with('test_job_id')

if __name__ == '__main__':
    unittest.main() 