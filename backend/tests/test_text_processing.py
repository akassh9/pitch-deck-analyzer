"""
Tests for the text processing utilities.
"""

import unittest
from unittest.mock import patch, MagicMock
from ..utils.text_processing import (
    is_noise_page,
    advanced_fix_spaced_text,
    fix_spaced_text,
    remove_noise,
    insert_line_breaks,
    clean_text,
    needs_ocr,
    prepare_text
)

class TestTextProcessing(unittest.TestCase):
    
    def test_is_noise_page(self):
        # Test empty text
        self.assertTrue(is_noise_page(""))
        self.assertTrue(is_noise_page(None))
        
        # Test noise keywords
        self.assertTrue(is_noise_page("Thank you for your attention"))
        self.assertTrue(is_noise_page("Introduction to our company"))
        self.assertTrue(is_noise_page("CONFIDENTIAL - Do not distribute"))
        
        # Test non-noise text
        self.assertFalse(is_noise_page("Our company has developed a revolutionary product"))
        self.assertFalse(is_noise_page("Market size is estimated at $10B"))
        
    def test_advanced_fix_spaced_text(self):
        # Test spaced text
        self.assertEqual(advanced_fix_spaced_text("T h i s i s a t e s t"), "This is a test")
        self.assertEqual(advanced_fix_spaced_text("N o r m a l text"), "Normal text")
        self.assertEqual(advanced_fix_spaced_text("Mixed t e x t"), "Mixed text")
        
        # Test already fixed text
        self.assertEqual(advanced_fix_spaced_text("Normal text"), "Normal text")
        
    def test_fix_spaced_text(self):
        # Test with advanced spacing issues
        self.assertEqual(fix_spaced_text("T h i s\ni s\na\nt e s t"), "This\nis\na\ntest")
        
        # Test with normal text
        self.assertEqual(fix_spaced_text("Normal\ntext"), "Normal\ntext")
        
    def test_remove_noise(self):
        # Test repeated lines
        text = "Header\nContent\nContent\nContent\nFooter"
        self.assertEqual(remove_noise(text), "Header\nContent\nFooter")
        
        # Test page numbers
        text = "Content\n1\nMore content\n2\nFinal content"
        self.assertEqual(remove_noise(text), "Content\nMore content\nFinal content")
        
        # Test special characters
        text = "Content\n***\nMore content"
        self.assertEqual(remove_noise(text), "Content\nMore content")
        
    def test_insert_line_breaks(self):
        # Test long text
        long_text = "This is a very long sentence that should be broken into multiple lines because it exceeds the maximum length limit and would be difficult to read otherwise."
        result = insert_line_breaks(long_text, max_length=50)
        self.assertLess(max(len(line) for line in result.split('\n')), 60)
        
        # Test short text
        short_text = "This is a short sentence."
        self.assertEqual(insert_line_breaks(short_text), short_text)
        
    def test_clean_text(self):
        # Test with various issues
        text = "  Excess  whitespace  \n\n\nMultiple newlines\n1\n2\nRepeated lines\nRepeated lines\nT h i s i s s p a c e d"
        result = clean_text(text)
        
        # Check whitespace normalization
        self.assertNotIn("  ", result)
        
        # Check newline normalization
        self.assertNotIn("\n\n\n", result)
        
        # Check noise removal
        self.assertNotIn("1\n2", result)
        
        # Check spacing fix
        self.assertIn("This is spaced", result)
        
    def test_needs_ocr(self):
        # Test empty text
        self.assertTrue(needs_ocr(""))
        self.assertTrue(needs_ocr(None))
        
        # Test short text
        self.assertTrue(needs_ocr("Short"))
        
        # Test text with many special characters
        self.assertTrue(needs_ocr("!@#$%^&*()_+{}|:<>?"))
        
        # Test normal text
        self.assertFalse(needs_ocr("This is normal text that should not need OCR processing."))
        
    @patch('backend.utils.text_processing.clean_text')
    @patch('backend.utils.text_processing.refine_text')
    def test_prepare_text(self, mock_refine_text, mock_clean_text):
        # Setup mocks
        mock_clean_text.return_value = "Cleaned text"
        mock_refine_text.return_value = "Refined text"
        
        # Test without refinement
        result = prepare_text("Raw text", refine=False)
        self.assertEqual(result, "Cleaned text")
        mock_clean_text.assert_called_once_with("Raw text")
        mock_refine_text.assert_not_called()
        
        # Reset mocks
        mock_clean_text.reset_mock()
        
        # Test with refinement
        result = prepare_text("Raw text", refine=True)
        self.assertEqual(result, "Refined text")
        mock_clean_text.assert_called_once_with("Raw text")
        mock_refine_text.assert_called_once_with("Cleaned text")

if __name__ == '__main__':
    unittest.main() 