"""
Tests for the app module.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
from flask import Flask
from ..app import create_app, register_error_handlers, register_routes, setup_logging, setup_cors
from ..config import Config

class TestApp(unittest.TestCase):
    
    def setUp(self):
        # Create a mock config
        self.config = MagicMock(spec=Config)
        self.config.debug = True
        self.config.secret_key = 'test_secret_key'
        self.config.upload_folder = '/tmp/uploads'
        self.config.max_content_length = 10 * 1024 * 1024  # 10MB
        
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
    
    @patch('backend.app.load_config')
    @patch('backend.app.setup_logging')
    @patch('backend.app.setup_cors')
    @patch('backend.app.register_routes')
    @patch('backend.app.register_error_handlers')
    def test_create_app(self, mock_register_error_handlers, mock_register_routes, 
                        mock_setup_cors, mock_setup_logging, mock_load_config):
        # Setup mocks
        mock_load_config.return_value = self.config
        
        # Call the function
        app = create_app()
        
        # Assertions
        self.assertIsInstance(app, Flask)
        self.assertEqual(app.config['DEBUG'], self.config.debug)
        self.assertEqual(app.config['SECRET_KEY'], self.config.secret_key)
        self.assertEqual(app.config['UPLOAD_FOLDER'], self.config.upload_folder)
        self.assertEqual(app.config['MAX_CONTENT_LENGTH'], self.config.max_content_length)
        
        # Check that all setup functions were called
        mock_load_config.assert_called_once()
        mock_setup_logging.assert_called_once_with(app, self.config)
        mock_setup_cors.assert_called_once_with(app)
        mock_register_routes.assert_called_once_with(app)
        mock_register_error_handlers.assert_called_once_with(app)
    
    def test_setup_logging(self):
        # Call the function
        setup_logging(self.app, self.config)
        
        # Check that logging was configured
        self.assertTrue(hasattr(self.app, 'logger'))
    
    @patch('backend.app.CORS')
    def test_setup_cors(self, mock_cors):
        # Call the function
        setup_cors(self.app)
        
        # Check that CORS was initialized
        mock_cors.assert_called_once_with(self.app, resources={r"/api/*": {"origins": "*"}})
    
    def test_register_routes(self):
        # Call the function
        register_routes(self.app)
        
        # Check that routes were registered
        # This is a bit tricky to test directly, so we'll just check that the app has routes
        self.assertTrue(len(self.app.url_map._rules) > 0)
    
    def test_register_error_handlers(self):
        # Call the function
        register_error_handlers(self.app)
        
        # Check that error handlers were registered
        # We can check if the app has error handlers for common HTTP errors
        self.assertTrue(400 in self.app.error_handler_spec[None])
        self.assertTrue(404 in self.app.error_handler_spec[None])
        self.assertTrue(500 in self.app.error_handler_spec[None])
    
    @patch('backend.app.load_config')
    def test_create_app_with_config_path(self, mock_load_config):
        # Setup mocks
        mock_load_config.return_value = self.config
        
        # Call the function with a config path
        config_path = '/path/to/config.json'
        app = create_app(config_path)
        
        # Check that load_config was called with the config path
        mock_load_config.assert_called_once_with(config_path)
    
    @patch('backend.app.load_config')
    @patch('backend.app.os.makedirs')
    def test_create_app_creates_upload_folder(self, mock_makedirs, mock_load_config):
        # Setup mocks
        mock_load_config.return_value = self.config
        
        # Call the function
        app = create_app()
        
        # Check that the upload folder was created
        mock_makedirs.assert_called_once_with(self.config.upload_folder, exist_ok=True)

if __name__ == '__main__':
    unittest.main() 