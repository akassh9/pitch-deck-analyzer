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

def refine_text(text, api_key=None):
    """
    Refine text using an LLM API.
    
    Args:
        text (str): The text to refine
        api_key (str): API key for the LLM service
        
    Returns:
        str: The refined text
    """
    from ..infrastructure.config import Config
    
    # Use provided API key or fall back to config
    api_key = api_key or Config.HF_API_KEY
    
    if not api_key:
        logger.warning("No API key provided for text refinement, skipping")
        return text
    
    # Log raw text if debug logging is enabled
    if Config.DEBUG_LOGGING:
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'raw_text_{timestamp}.txt')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== Raw Text ===\n\n")
            f.write(text)
            f.write("\n\n=== End Raw Text ===")
        logger.debug(f"Logged raw text to {log_file}")
    
    # Split text into chunks to avoid token limits
    max_chunk_size = 2000
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    refined_chunks = []
    
    logger.info(f"Refining text in {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
        
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
                    "content": (
                        "Remove only unnecessary whitespace, extra newlines, and redundant paragraph breaks. "
                        "Return the text with improved formatting without altering its content. "
                        "Only return the improved text, do not add any instructions/confirmations/comments."
                    )
                },
                {
                    "role": "user",
                    "content": f"{chunk}"
                }
            ],
            "temperature": 0.5,
            "max_tokens": 130000,
            "top_p": 1.0
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    refined_chunk = result["choices"][0]["message"]["content"].strip()
                    refined_chunks.append(refined_chunk)
                    logger.debug(f"Successfully refined chunk {i+1}")
                else:
                    logger.warning(f"Unexpected API response format for chunk {i+1}")
                    refined_chunks.append(chunk)
            else:
                logger.warning(f"API request failed with status {response.status_code} for chunk {i+1}")
                refined_chunks.append(chunk)
                
        except Exception as e:
            logger.error(f"Error refining chunk {i+1}: {str(e)}")
            refined_chunks.append(chunk)
    
    return "\n".join(refined_chunks)

def prepare_text(raw_text, refine=False):
    """
    Prepare text for analysis.
    
    Args:
        raw_text (str): The raw text to prepare
        refine (bool): Whether to refine the text using an LLM
        
    Returns:
        str: The prepared text
    """
    logger.info(f"Preparing text ({len(raw_text)} chars, refine={refine})")
    
    # Clean the text
    cleaned = clean_text(raw_text)
    logger.debug(f"Cleaned text ({len(cleaned)} chars)")
    
    # Refine if requested
    if refine:
        logger.info("Refining text with LLM")
        return refine_text(cleaned)
    
    return cleaned 