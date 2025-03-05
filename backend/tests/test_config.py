"""
Tests for the configuration module.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from ..infrastructure.config import Config, load_config

class TestConfig(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a temporary config file
        self.config_path = os.path.join(self.temp_dir, 'config.json')
        with open(self.config_path, 'w') as f:
            f.write('''
            {
                "app": {
                    "debug": true,
                    "secret_key": "test_secret_key",
                    "upload_folder": "/tmp/uploads",
                    "max_content_length": 10485760
                },
                "api": {
                    "groq_api_key": "test_groq_key",
                    "openrouter_api_key": "test_openrouter_key",
                    "google_api_key": "test_google_key",
                    "google_cse_id": "test_cse_id"
                }
            }
            ''')
    
    def tearDown(self):
        # Remove the temporary config file
        os.remove(self.config_path)
        
        # Remove the temporary directory
        os.rmdir(self.temp_dir)
    
    def test_load_config_from_file(self):
        # Load the config from the file
        config = load_config(self.config_path)
        
        # Check that the config is a Config object
        self.assertIsInstance(config, Config)
        
        # Check that the config values are correct
        self.assertTrue(config.debug)
        self.assertEqual(config.secret_key, 'test_secret_key')
        self.assertEqual(config.upload_folder, '/tmp/uploads')
        self.assertEqual(config.max_content_length, 10485760)
        self.assertEqual(config.groq_api_key, 'test_groq_key')
        self.assertEqual(config.openrouter_api_key, 'test_openrouter_key')
        self.assertEqual(config.google_api_key, 'test_google_key')
        self.assertEqual(config.google_cse_id, 'test_cse_id')
    
    def test_load_config_from_env(self):
        # Set environment variables
        with patch.dict(os.environ, {
            'DEBUG': 'false',
            'SECRET_KEY': 'env_secret_key',
            'UPLOAD_FOLDER': '/env/uploads',
            'MAX_CONTENT_LENGTH': '20971520',
            'GROQ_API_KEY': 'env_groq_key',
            'OPENROUTER_API_KEY': 'env_openrouter_key',
            'GOOGLE_API_KEY': 'env_google_key',
            'GOOGLE_CSE_ID': 'env_cse_id'
        }):
            # Load the config from environment variables
            config = load_config(None)
            
            # Check that the config is a Config object
            self.assertIsInstance(config, Config)
            
            # Check that the config values are correct
            self.assertFalse(config.debug)
            self.assertEqual(config.secret_key, 'env_secret_key')
            self.assertEqual(config.upload_folder, '/env/uploads')
            self.assertEqual(config.max_content_length, 20971520)
            self.assertEqual(config.groq_api_key, 'env_groq_key')
            self.assertEqual(config.openrouter_api_key, 'env_openrouter_key')
            self.assertEqual(config.google_api_key, 'env_google_key')
            self.assertEqual(config.google_cse_id, 'env_cse_id')
    
    def test_load_config_env_overrides_file(self):
        # Set environment variables to override file values
        with patch.dict(os.environ, {
            'DEBUG': 'false',
            'SECRET_KEY': 'env_secret_key'
        }):
            # Load the config from the file with environment overrides
            config = load_config(self.config_path)
            
            # Check that the environment values override the file values
            self.assertFalse(config.debug)
            self.assertEqual(config.secret_key, 'env_secret_key')
            
            # Check that the other values are from the file
            self.assertEqual(config.upload_folder, '/tmp/uploads')
            self.assertEqual(config.max_content_length, 10485760)
            self.assertEqual(config.groq_api_key, 'test_groq_key')
            self.assertEqual(config.openrouter_api_key, 'test_openrouter_key')
            self.assertEqual(config.google_api_key, 'test_google_key')
            self.assertEqual(config.google_cse_id, 'test_cse_id')
    
    def test_config_to_dict(self):
        # Create a config object
        config = Config(
            debug=True,
            secret_key='test_secret_key',
            upload_folder='/tmp/uploads',
            max_content_length=10485760,
            groq_api_key='test_groq_key',
            openrouter_api_key='test_openrouter_key',
            google_api_key='test_google_key',
            google_cse_id='test_cse_id'
        )
        
        # Convert the config to a dictionary
        config_dict = config.to_dict()
        
        # Check that the dictionary contains all the config values
        self.assertEqual(config_dict['debug'], True)
        self.assertEqual(config_dict['secret_key'], 'test_secret_key')
        self.assertEqual(config_dict['upload_folder'], '/tmp/uploads')
        self.assertEqual(config_dict['max_content_length'], 10485760)
        self.assertEqual(config_dict['groq_api_key'], 'test_groq_key')
        self.assertEqual(config_dict['openrouter_api_key'], 'test_openrouter_key')
        self.assertEqual(config_dict['google_api_key'], 'test_google_key')
        self.assertEqual(config_dict['google_cse_id'], 'test_cse_id')
    
    def test_config_from_dict(self):
        # Create a dictionary with config values
        config_dict = {
            'debug': True,
            'secret_key': 'test_secret_key',
            'upload_folder': '/tmp/uploads',
            'max_content_length': 10485760,
            'groq_api_key': 'test_groq_key',
            'openrouter_api_key': 'test_openrouter_key',
            'google_api_key': 'test_google_key',
            'google_cse_id': 'test_cse_id'
        }
        
        # Create a config object from the dictionary
        config = Config.from_dict(config_dict)
        
        # Check that the config values are correct
        self.assertTrue(config.debug)
        self.assertEqual(config.secret_key, 'test_secret_key')
        self.assertEqual(config.upload_folder, '/tmp/uploads')
        self.assertEqual(config.max_content_length, 10485760)
        self.assertEqual(config.groq_api_key, 'test_groq_key')
        self.assertEqual(config.openrouter_api_key, 'test_openrouter_key')
        self.assertEqual(config.google_api_key, 'test_google_key')
        self.assertEqual(config.google_cse_id, 'test_cse_id')

if __name__ == '__main__':
    unittest.main() 