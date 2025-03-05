"""Tests for memo generation service."""

import pytest
from unittest.mock import Mock, patch
from ..core.memo_service import MemoService
from ..utils.error_handling import ProcessingError
from ..utils.memo_templates import TEMPLATES

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return Mock(
        GROQ_API_KEY="test_groq_key",
        HF_API_KEY="test_hf_key",
        GOOGLE_API_KEY="test_google_key",
        GOOGLE_CSE_ID="test_cse_id"
    )

@pytest.fixture
def memo_service(mock_config):
    """Create a MemoService instance with mock config."""
    return MemoService(mock_config)

def test_generate_memo_with_default_template(memo_service):
    """Test memo generation with default template."""
    with patch('requests.post') as mock_post:
        # Mock successful API response
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Test memo content"}}]
        }
        
        result = memo_service.generate_memo("Test input")
        
        # Verify API was called with default template
        assert mock_post.call_count == 1
        call_args = mock_post.call_args[1]["json"]
        content = call_args["messages"][1]["content"]
        
        # Check that default template sections are included
        for section in TEMPLATES["default"]["sections_order"]:
            assert section in content
        
        assert result == "Test memo content"

def test_generate_memo_with_custom_template(memo_service):
    """Test memo generation with a custom template."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Test memo content"}}]
        }
        
        result = memo_service.generate_memo("Test input", template_key="seed")
        
        # Verify API was called with seed template
        call_args = mock_post.call_args[1]["json"]
        content = call_args["messages"][1]["content"]
        
        # Check that seed template sections are included
        for section in TEMPLATES["seed"]["sections_order"]:
            assert section in content
        
        assert result == "Test memo content"

def test_generate_memo_with_invalid_template(memo_service):
    """Test memo generation with invalid template falls back to default."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Test memo content"}}]
        }
        
        result = memo_service.generate_memo("Test input", template_key="nonexistent")
        
        # Verify API was called with default template
        call_args = mock_post.call_args[1]["json"]
        content = call_args["messages"][1]["content"]
        
        # Check that default template sections are included
        for section in TEMPLATES["default"]["sections_order"]:
            assert section in content
        
        assert result == "Test memo content"

def test_generate_memo_api_error(memo_service):
    """Test error handling when API call fails."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "API Error"
        
        with pytest.raises(ProcessingError):
            memo_service.generate_memo("Test input")

def test_template_instructions_in_prompt(memo_service):
    """Test that template instructions are included in the prompt."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Test memo content"}}]
        }
        
        template_key = "seriesA"
        memo_service.generate_memo("Test input", template_key=template_key)
        
        # Verify template instructions are in the prompt
        call_args = mock_post.call_args[1]["json"]
        content = call_args["messages"][1]["content"]
        assert TEMPLATES[template_key]["instructions"] in content
