"""
Text processing utilities for cleaning and preparing text extracted from PDFs.
This module provides functions to clean, format, and refine text.
"""

import re
import os
import datetime
import logging
import requests
import pytesseract
from pdf2image import convert_from_path
import json
from ..prompts import build_text_refinement_prompt  # Import the consolidated prompt builder

logger = logging.getLogger(__name__)

def is_noise_page(text):
    """
    Determine if a page contains only noise (e.g., page numbers, headers).
    
    Args:
        text (str): The text to check
        
    Returns:
        bool: True if the page is noise, False otherwise
    """
    if not text:
        return True
        
    lower_text = text.lower()
    noise_keywords = [
        'intro', 'introduction', 'thank you', 'thanks', 
        'acknowledgement', 'closing', 'end of presentation',
        'confidential', 'proprietary', 'all rights reserved'
    ]
    
    for keyword in noise_keywords:
        if keyword in lower_text:
            return True
            
    # Check if page is mostly numbers or symbols
    alpha_count = sum(c.isalpha() for c in text)
    if len(text) > 0 and alpha_count / len(text) < 0.3:
        return True
        
    return False

def advanced_fix_spaced_text(text):
    """
    Fix text where characters are separated by spaces.
    
    Args:
        text (str): The text to fix
        
    Returns:
        str: The fixed text
    """
    pattern = r'(?<!\S)((?:\w\s){2,}\w)(?!\S)'
    
    def repl(match):
        return match.group(1).replace(" ", "")
        
    return re.sub(pattern, repl, text)

def fix_spaced_text(text):
    """
    Fix text with spacing issues.
    
    Args:
        text (str): The text to fix
        
    Returns:
        str: The fixed text
    """
    text = advanced_fix_spaced_text(text)
    
    def fix_line(line):
        words = line.split()
        if words and (sum(len(w) for w in words)) < 2:
            return ''.join(words)
        return line
        
    return "\n".join(fix_line(line) for line in text.splitlines())

def remove_noise(text):
    """
    Remove noise from text (repeated lines, page numbers, etc.).
    
    Args:
        text (str): The text to clean
        
    Returns:
        str: The cleaned text
    """
    lines = text.split('\n')
    freq = {}
    
    # Count frequency of each line
    for line in lines:
        stripped = line.strip()
        if stripped:
            freq[stripped] = freq.get(stripped, 0) + 1
    
    # Filter out noise lines
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            cleaned_lines.append(line)
            continue
            
        # Skip repeated short lines
        if freq.get(stripped, 0) > 2 and len(stripped) < 50:
            continue
            
        # Skip page numbers
        if re.match(r'^\d+(\s*/\s*\d+)?$', stripped):
            continue
            
        # Skip lines with only special characters
        if all(not c.isalnum() and not c.isspace() for c in stripped):
            continue
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def insert_line_breaks(text, max_length=150):
    """
    Insert line breaks to improve readability.
    
    Args:
        text (str): The text to format
        max_length (int): Maximum line length
        
    Returns:
        str: The formatted text
    """
    sentences = re.split(r'(?<=[.])\s+', text)
    new_sentences = []
    
    for sentence in sentences:
        if len(sentence) > max_length:
            # Find a good break point near the middle
            mid = len(sentence) // 2
            break_point = sentence.rfind(" ", 0, mid) or mid
            
            new_sentences.append(sentence[:break_point].strip())
            new_sentences.append(sentence[break_point:].strip())
        else:
            new_sentences.append(sentence)
            
    return "\n".join(new_sentences)

def clean_text(text):
    """
    Clean and format text.
    
    Args:
        text (str): The text to clean
        
    Returns:
        str: The cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Fix spacing issues
    text = fix_spaced_text(text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove noise
    text = remove_noise(text)
    
    # Format for readability
    text = insert_line_breaks(text)
    
    return text

def needs_ocr(text):
    """
    Determine if OCR is needed for a page.
    
    Args:
        text (str): The text to check
        
    Returns:
        bool: True if OCR is needed, False otherwise
    """
    # Empty or very short text
    if not text or len(text.strip()) < 20:
        return True
        
    # Text with very few characters per word
    words = text.split()
    if words and (sum(len(w) for w in words)) / len(words) < 2:
        return True
        
    # Text with high proportion of non-alphanumeric characters
    non_alpha = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if len(text) > 0 and non_alpha / len(text) > 0.5:
        return True
        
    return False

def ocr_page(image):
    """
    Perform OCR on an image.
    
    Args:
        image: The image to process
        
    Returns:
        str: The extracted text
    """
    custom_config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(image, config=custom_config)

def refine_text(text, api_key=None): #no idea what this is doing, but can't remove because it breaks the code
    # ...
    # Use the consolidated prompt builder
    prompt = build_text_refinement_prompt()  # This might be wrong
    
    data = {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct:free",
        "messages": [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]}
        ],

    }

def refine_text_with_stage(text: str, api_key=None) -> dict:
    """
    Refine text and predict startup stage using an LLM API.
    
    Args:
        text (str): The text to refine
        api_key (str): API key for the LLM service
        
    Returns:
        dict: Dictionary containing cleaned text and predicted startup stage
    """
    from ..infrastructure.config import Config
    import requests
    import json
    import re
    
    logger.info("Starting text refinement with stage prediction")
    
    # Use provided API key or fall back to config
    api_key = api_key or Config.HF_API_KEY
    
    if not api_key:
        logger.warning("No API key provided for text refinement, using basic cleaning")
        return {
            "cleaned_text": clean_text(text),
            "startup_stage": "default"
        }
    
    # Define the prompt for text refinement and stage prediction
    prompt = (
        "You are an assistant that processes text data. "
        "Your task is to:\n\n"
        "1. Clean and format the given text by:\n"
        "   - Removing unnecessary whitespace and redundant newlines\n"
        "   - Fixing formatting issues\n"
        "   - Maintaining proper paragraph structure\n\n"
        "2. Analyze the content to determine the startup's stage.\n\n"
        "First output the cleaned text, then on a new line start with 'STAGE:' "
        "followed by one of these exact stages (case sensitive):\n"
        "- seed (for early-stage startups seeking initial funding)\n"
        "- seriesa (for startups with proven business model seeking growth capital)\n"
        "- growth (for established startups scaling rapidly)\n"
        "- default (if unable to determine)\n\n"
        f"{text}"
    )
    
    logger.info("Sending request to LLM API")
    
    # Build the request payload
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct:free",
        "messages": [
            {
                "role": "system",
                "content": "You are a text processing assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": 130000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Extract the markdown response
        output = result["choices"][0]["message"]["content"].strip()
        logger.info(f"LLM Response received, length: {len(output)} characters")
        logger.info(f"LLM Response first 100 chars: {output[:100]}...")
        logger.info(f"LLM Response last 100 chars: {output[-100:] if len(output) > 100 else output}")
        
        # Look for stage pattern anywhere in the text
        stage_pattern = r'\*{0,2}STAGE:\*{0,2}\s*(?:\n\s*)*\*{0,2}([\w]+)\*{0,2}'
        stage_match = re.search(stage_pattern, output, re.IGNORECASE | re.DOTALL)

        
        if stage_match:
            # Extract the stage
            stage_raw = stage_match.group(1).strip()
            logger.info(f"Found stage in output: '{stage_raw}'")
            
            # Normalize stage name
            stage_lower = stage_raw.lower()
            
            # Map to correct case format for frontend
            if 'seed' in stage_lower:
                stage = 'seed'
            elif 'seriesa' in stage_lower or 'series a' in stage_lower or 'series_a' in stage_lower:
                stage = 'seriesa'
            elif 'growth' in stage_lower:
                stage = 'growth'
            else:
                stage = 'default'
            
            logger.info(f"Normalized stage: '{stage}'")
            
            # Remove the stage line from the cleaned text
            cleaned_text = re.sub(r'(?:^|\n)\*{0,2}STAGE:\*{0,2}.*?(?=\n|$)', '', output, flags=re.IGNORECASE).strip()
            logger.info(f"Removed stage line from cleaned text, new length: {len(cleaned_text)}")
            
            # Ensure we're returning the correct stage
            logger.info(f"Final stage being returned: '{stage}'")
            
            return {
                "cleaned_text": cleaned_text,
                "startup_stage": stage
            }
        else:
            logger.warning("No stage found in output, using default")
            return {
                "cleaned_text": output,
                "startup_stage": "default"
            }
            
    except Exception as e:
        logger.error(f"Error in text refinement with stage prediction: {str(e)}")
        return {
            "cleaned_text": clean_text(text),
            "startup_stage": "default"
        }

def prepare_text(raw_text, refine=False):
    """
    Prepare text by cleaning and optionally refining it.
    
    Args:
        raw_text (str): The raw text to process
        refine (bool): Whether to use LLM refinement
        
    Returns:
        dict: Dictionary containing cleaned text and startup stage
    """
    logger.info(f"Preparing text with refinement={'enabled' if refine else 'disabled'}")
    
    # First do basic cleaning to handle major formatting issues
    cleaned_text = clean_text(raw_text)
    
    if refine:
        logger.info("Sending text to LLM for refinement")
        result = refine_text_with_stage(cleaned_text)
        logger.info(f"LLM refinement complete. Stage identified: {result['startup_stage']}")
        return result
    
    logger.info("Skipping LLM refinement")
    return {
        "cleaned_text": cleaned_text,
        "startup_stage": "default"
    }