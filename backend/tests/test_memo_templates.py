"""Tests for memo templates functionality."""

import pytest
from ..utils.memo_templates import TEMPLATES

def test_template_structure():
    """Test that all templates have the required structure."""
    required_keys = {"sections_order", "instructions"}
    
    for template_name, template in TEMPLATES.items():
        # Check that template has all required keys
        assert set(template.keys()) == required_keys, \
            f"Template '{template_name}' missing required keys"
        
        # Check that sections_order is a non-empty list
        assert isinstance(template["sections_order"], list), \
            f"Template '{template_name}' sections_order must be a list"
        assert len(template["sections_order"]) > 0, \
            f"Template '{template_name}' sections_order cannot be empty"
        
        # Check that instructions is a non-empty string
        assert isinstance(template["instructions"], str), \
            f"Template '{template_name}' instructions must be a string"
        assert len(template["instructions"]) > 0, \
            f"Template '{template_name}' instructions cannot be empty"

def test_default_template_exists():
    """Test that the default template exists."""
    assert "default" in TEMPLATES, "Default template must exist"

def test_template_sections_are_strings():
    """Test that all section names are strings."""
    for template_name, template in TEMPLATES.items():
        for section in template["sections_order"]:
            assert isinstance(section, str), \
                f"Template '{template_name}' contains non-string section name"
            assert len(section) > 0, \
                f"Template '{template_name}' contains empty section name"

def test_unique_sections_per_template():
    """Test that sections are unique within each template."""
    for template_name, template in TEMPLATES.items():
        sections = template["sections_order"]
        assert len(sections) == len(set(sections)), \
            f"Template '{template_name}' contains duplicate sections"
