"""
Tests for the memo service.
"""

import unittest
from unittest.mock import patch, MagicMock
from ..core.memo_service import MemoService
from ..utils.error_handling import ProcessingError

class TestMemoService(unittest.TestCase):
    
    def setUp(self):
        self.config = MagicMock()
        self.config.GROQ_API_KEY = "test_groq_key"
        self.config.HF_API_KEY = "test_hf_key"
        self.config.GOOGLE_API_KEY = "test_google_key"
        self.config.GOOGLE_CSE_ID = "test_cse_id"
        self.memo_service = MemoService(self.config)
        
    @patch('backend.utils.text_processing.prepare_text')
    @patch('backend.core.memo_service.MemoService._call_groq_api')
    def test_generate_memo_with_groq(self, mock_call_groq, mock_prepare_text):
        # Setup mocks
        mock_prepare_text.return_value = "Prepared text"
        mock_call_groq.return_value = "Generated memo"
        
        # Call the method
        result = self.memo_service.generate_memo("Raw text", refine=False)
        
        # Assertions
        self.assertEqual(result, "Generated memo")
        mock_prepare_text.assert_called_once_with("Raw text", refine=False)
        mock_call_groq.assert_called_once_with("Prepared text")
        
    @patch('backend.utils.text_processing.prepare_text')
    @patch('backend.core.memo_service.MemoService._call_groq_api')
    @patch('backend.core.memo_service.MemoService._call_openrouter_api')
    def test_generate_memo_fallback(self, mock_call_openrouter, mock_call_groq, mock_prepare_text):
        # Setup mocks
        mock_prepare_text.return_value = "Prepared text"
        mock_call_groq.side_effect = Exception("Groq API error")
        mock_call_openrouter.return_value = "Fallback memo"
        
        # Call the method
        result = self.memo_service.generate_memo("Raw text", refine=False)
        
        # Assertions
        self.assertEqual(result, "Fallback memo")
        mock_prepare_text.assert_called_once_with("Raw text", refine=False)
        mock_call_groq.assert_called_once_with("Prepared text")
        mock_call_openrouter.assert_called_once_with("Prepared text")
        
    @patch('backend.utils.text_processing.prepare_text')
    @patch('backend.core.memo_service.MemoService._call_groq_api')
    @patch('backend.core.memo_service.MemoService._call_openrouter_api')
    def test_generate_memo_failure(self, mock_call_openrouter, mock_call_groq, mock_prepare_text):
        # Setup mocks
        mock_prepare_text.return_value = "Prepared text"
        mock_call_groq.side_effect = Exception("Groq API error")
        mock_call_openrouter.side_effect = Exception("OpenRouter API error")
        
        # Call the method and check exception
        with self.assertRaises(ProcessingError):
            self.memo_service.generate_memo("Raw text", refine=False)
        
        # Assertions
        mock_prepare_text.assert_called_once_with("Raw text", refine=False)
        mock_call_groq.assert_called_once_with("Prepared text")
        mock_call_openrouter.assert_called_once_with("Prepared text")
        
    @patch('backend.core.memo_service.MemoService._google_custom_search')
    @patch('backend.core.memo_service.MemoService._extract_key_claims')
    def test_validate_memo(self, mock_extract_claims, mock_google_search):
        # Setup mocks
        mock_extract_claims.return_value = "Key claims"
        mock_google_search.return_value = [{"title": "Result", "snippet": "Snippet", "link": "Link"}]
        
        # Call the method
        result = self.memo_service.validate_memo("Memo text")
        
        # Assertions
        self.assertEqual(result, [{"title": "Result", "snippet": "Snippet", "link": "Link"}])
        mock_extract_claims.assert_called_once_with("Memo text")
        mock_google_search.assert_called_once_with("Key claims")
        
    def test_extract_key_claims(self):
        # Test with a sample memo
        memo = """
        # Executive Summary
        
        This is a summary of the pitch deck.
        
        # Market Opportunity
        
        The market size is $10B with a 15% annual growth rate.
        
        # Competitive Landscape
        
        The main competitors are Company A, Company B, and Company C.
        
        # Financial Highlights
        
        The company projects $5M in revenue by 2025.
        """
        
        # Call the method
        result = self.memo_service._extract_key_claims(memo)
        
        # Assertions
        self.assertIn("market size is $10B with a 15% annual growth rate", result)
        self.assertIn("main competitors are Company A, Company B, and Company C", result)
        self.assertIn("company projects $5M in revenue by 2025", result)

if __name__ == '__main__':
    unittest.main() 