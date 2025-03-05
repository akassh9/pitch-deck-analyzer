"""
Tests for the memo controller.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from ..api.memo_controller import generate_memo, validate_selection
from ..core.memo_service import MemoService

class TestMemoController(unittest.TestCase):
    
    def setUp(self):
        # Mock memo service
        self.memo_service = MagicMock(spec=MemoService)
        
        # Mock Flask's g object
        self.g = MagicMock()
        self.g.memo_service = self.memo_service
    
    @patch('backend.api.memo_controller.request')
    @patch('backend.api.memo_controller.g', new_callable=MagicMock)
    @patch('backend.api.memo_controller.jsonify')
    def test_generate_memo_success(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.memo_service = self.memo_service
        
        # Mock request data
        request_data = {'text': 'Sample pitch deck text'}
        mock_request.json = request_data
        
        # Mock memo generation
        generated_memo = "# Investment Memo\n\nThis is a sample investment memo."
        self.memo_service.generate_memo.return_value = generated_memo
        
        # Mock jsonify response
        mock_jsonify.return_value = {'memo': generated_memo}
        
        # Call the function
        result = generate_memo()
        
        # Assertions
        self.memo_service.generate_memo.assert_called_once_with(request_data['text'])
        mock_jsonify.assert_called_once_with({'memo': generated_memo})
    
    @patch('backend.api.memo_controller.request')
    @patch('backend.api.memo_controller.g', new_callable=MagicMock)
    @patch('backend.api.memo_controller.jsonify')
    def test_generate_memo_missing_text(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.memo_service = self.memo_service
        
        # Mock empty request data
        mock_request.json = {}
        
        # Mock jsonify response
        mock_jsonify.return_value = {'error': 'Missing required field: text'}
        mock_jsonify.return_value.status_code = 400
        
        # Call the function
        result = generate_memo()
        
        # Assertions
        self.memo_service.generate_memo.assert_not_called()
        mock_jsonify.assert_called_once_with({'error': 'Missing required field: text'})
    
    @patch('backend.api.memo_controller.request')
    @patch('backend.api.memo_controller.g', new_callable=MagicMock)
    @patch('backend.api.memo_controller.jsonify')
    def test_generate_memo_error(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.memo_service = self.memo_service
        
        # Mock request data
        request_data = {'text': 'Sample pitch deck text'}
        mock_request.json = request_data
        
        # Mock memo generation error
        error_message = "API error"
        self.memo_service.generate_memo.side_effect = Exception(error_message)
        
        # Mock jsonify response
        mock_jsonify.return_value = {'error': f'Failed to generate memo: {error_message}'}
        mock_jsonify.return_value.status_code = 500
        
        # Call the function
        result = generate_memo()
        
        # Assertions
        self.memo_service.generate_memo.assert_called_once_with(request_data['text'])
        mock_jsonify.assert_called_once_with({'error': f'Failed to generate memo: {error_message}'})
    
    @patch('backend.api.memo_controller.request')
    @patch('backend.api.memo_controller.g', new_callable=MagicMock)
    @patch('backend.api.memo_controller.jsonify')
    def test_validate_selection_success(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.memo_service = self.memo_service
        
        # Mock request data
        request_data = {'text': 'Sample claim from pitch deck'}
        mock_request.json = request_data
        
        # Mock validation results
        validation_results = [
            {'title': 'Source 1', 'snippet': 'Supporting evidence', 'link': 'https://example.com/1'},
            {'title': 'Source 2', 'snippet': 'More evidence', 'link': 'https://example.com/2'}
        ]
        self.memo_service.validate_memo.return_value = validation_results
        
        # Mock jsonify response
        mock_jsonify.return_value = {'results': validation_results}
        
        # Call the function
        result = validate_selection()
        
        # Assertions
        self.memo_service.validate_memo.assert_called_once_with(request_data['text'])
        mock_jsonify.assert_called_once_with({'results': validation_results})
    
    @patch('backend.api.memo_controller.request')
    @patch('backend.api.memo_controller.g', new_callable=MagicMock)
    @patch('backend.api.memo_controller.jsonify')
    def test_validate_selection_missing_text(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.memo_service = self.memo_service
        
        # Mock empty request data
        mock_request.json = {}
        
        # Mock jsonify response
        mock_jsonify.return_value = {'error': 'Missing required field: text'}
        mock_jsonify.return_value.status_code = 400
        
        # Call the function
        result = validate_selection()
        
        # Assertions
        self.memo_service.validate_memo.assert_not_called()
        mock_jsonify.assert_called_once_with({'error': 'Missing required field: text'})
    
    @patch('backend.api.memo_controller.request')
    @patch('backend.api.memo_controller.g', new_callable=MagicMock)
    @patch('backend.api.memo_controller.jsonify')
    def test_validate_selection_error(self, mock_jsonify, mock_g, mock_request):
        # Setup mocks
        mock_g.memo_service = self.memo_service
        
        # Mock request data
        request_data = {'text': 'Sample claim from pitch deck'}
        mock_request.json = request_data
        
        # Mock validation error
        error_message = "Search API error"
        self.memo_service.validate_memo.side_effect = Exception(error_message)
        
        # Mock jsonify response
        mock_jsonify.return_value = {'error': f'Failed to validate selection: {error_message}'}
        mock_jsonify.return_value.status_code = 500
        
        # Call the function
        result = validate_selection()
        
        # Assertions
        self.memo_service.validate_memo.assert_called_once_with(request_data['text'])
        mock_jsonify.assert_called_once_with({'error': f'Failed to validate selection: {error_message}'})

if __name__ == '__main__':
    unittest.main() 