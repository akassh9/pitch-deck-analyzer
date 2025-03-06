import re
import os
import datetime
import requests
import pytesseract
from pdf2image import convert_from_path
import pdfplumber
from .config import Config
from .utils.text_processing import refine_text  # Import refine_text from text_processing

DEBUG_LOGGING = Config.DEBUG_LOGGING

def is_noise_page(text):
    if not text:
        return True
    lower_text = text.lower()
    noise_keywords = ['intro', 'introduction', 'thank you', 'thanks', 'acknowledgement', 'closing', 'end of presentation']
    for keyword in noise_keywords:
        if keyword in lower_text:
            return True
    return False

def advanced_fix_spaced_text(text):
    pattern = r'(?<!\S)((?:\w\s){2,}\w)(?!\S)'
    def repl(match):
        return match.group(1).replace(" ", "")
    return re.sub(pattern, repl, text)

def fix_spaced_text(text):
    text = advanced_fix_spaced_text(text)
    def fix_line(line):
        words = line.split()
        if words and (sum(len(w) for w in words)) < 2:
            return ''.join(words)
        return line
    return "\n".join(fix_line(line) for line in text.splitlines())

def remove_noise(text):
    lines = text.split('\n')
    freq = {}
    for line in lines:
        stripped = line.strip()
        if stripped:
            freq[stripped] = freq.get(stripped, 0) + 1
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            if freq.get(stripped, 0) > 2 and len(stripped) < 50:
                continue
            if re.match(r'^\d+(\s*/\s*\d+)?$', stripped):
                continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def insert_line_breaks(text, max_length=150):
    sentences = re.split(r'(?<=[.])\s+', text)
    new_sentences = []
    for sentence in sentences:
        if len(sentence) > max_length:
            mid = len(sentence) // 2
            break_point = sentence.rfind(" ", 0, mid) or mid
            new_sentences.append(sentence[:break_point].strip())
            new_sentences.append(sentence[break_point:].strip())
        else:
            new_sentences.append(sentence)
    return "\n".join(new_sentences)

def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = fix_spaced_text(text)
    text = text.strip()
    text = remove_noise(text)
    text = insert_line_breaks(text)
    return text

def needs_ocr(text):
    if not text or len(text.strip()) < 20:
        return True
    words = text.split()
    if words and (sum(len(w) for w in words)) < 2:
        return True
    non_alpha = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if len(text) > 0 and non_alpha / len(text) > 0.5:
        return True
    return False

def ocr_page(image):
    custom_config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(image, config=custom_config)

def prepare_text(raw_text, refine=False):
    cleaned = clean_text(raw_text)
    if refine:
        return refine_text(cleaned)
    return cleaned
