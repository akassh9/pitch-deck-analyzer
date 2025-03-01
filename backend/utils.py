import re
import os
import datetime
import requests
import pytesseract
from pdf2image import convert_from_path
import pdfplumber
from config import Config

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

def refine_text(text):
    # Use the central configuration to access the API key.
    if not Config.HF_API_KEY:
        return text
    if DEBUG_LOGGING:
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'raw_text_{timestamp}.txt')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== Raw Text ===\n\n")
            f.write(text)
            f.write("\n\n=== End Raw Text ===")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {Config.HF_API_KEY}",
        "Content-Type": "application/json",
    }
    max_chunk_size = 2000
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    refined_chunks = []
    for chunk in chunks:
        data = {
            "model": "nvidia/llama-3.1-nemotron-70b-instruct:free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Remove only unnecessary whitespace, extra newlines, and redundant paragraph breaks. "
                        "Return the text with improved formatting without altering its content."
                    )
                },
                {
                    "role": "user",
                    "content": f"{chunk}"
                }
            ],
            "temperature": 0.5,
            "max_tokens": 130000,
            "top_p": 1.0,
            "top_k": 0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "repetition_penalty": 1.0,
            "min_p": 0.0,
            "top_a": 0.0
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    refined_chunk = result["choices"][0]["message"]["content"].strip()
                    refined_chunks.append(refined_chunk)
                else:
                    refined_chunks.append(chunk)
            else:
                refined_chunks.append(chunk)
        except Exception as e:
            refined_chunks.append(chunk)
    return "\n".join(refined_chunks)

def prepare_text(raw_text, refine=False):
    cleaned = clean_text(raw_text)
    if refine:
        return refine_text(cleaned)
    return cleaned
