import os
import re
import datetime
import threading
import uuid
import requests
import json
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

from utils import prepare_text, is_noise_page, needs_ocr, ocr_page

load_dotenv()

# Environment keys
HF_API_KEY = os.getenv("HF_API_KEY")
GOOGLE_AI_STUDIO_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

genai.configure(api_key=GOOGLE_AI_STUDIO_API_KEY)

app = Flask(__name__)
# Rely solely on Flask-CORS with proper configuration.
CORS(app, resources={
    r"/*": {
        "origins": "http://localhost:3000",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Directory for uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max file size

# Global in-memory job store (for development use)
jobs = {}  # { job_id: {"status": "pending"/"complete"/"error", "result": <text or error>} }

# Background processing function for the uploaded PDF
def process_pdf_job(file_path, job_id):
    try:
        extracted_text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            for i in range(total_pages):
                page = reader.pages[i]
                page_text = page.extract_text()
                if needs_ocr(page_text):
                    try:
                        with pdfplumber.open(file_path) as pdf:
                            page_plumber = pdf.pages[i]
                            page_text_alt = page_plumber.extract_text()
                            if page_text_alt and len(page_text_alt.strip()) > len(page_text.strip()):
                                page_text = page_text_alt
                    except Exception as e:
                        app.logger.error(f"pdfplumber error on page {i+1}: {e}")
                    if needs_ocr(page_text):
                        try:
                            images = convert_from_path(file_path, dpi=300, first_page=i+1, last_page=i+1)
                            if images:
                                page_text = ocr_page(images[0])
                        except Exception as e:
                            app.logger.error(f"OCR error on page {i+1}: {e}")
                if not is_noise_page(page_text):
                    extracted_text += page_text + "\n"
        # Process the extracted text with AI refinement enabled
        processed_text = prepare_text(extracted_text, refine=True)
        jobs[job_id]["result"] = processed_text
        jobs[job_id]["status"] = "complete"
    except Exception as e:
        jobs[job_id]["result"] = str(e)
        jobs[job_id]["status"] = "error"
    finally:
        try:
            os.remove(file_path)
        except Exception:
            pass

@app.route('/')
def health_check():
    return jsonify({"status": "healthy"})

def google_custom_search(query, api_key, cse_id):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cse_id, "q": query}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json()
        items = results.get("items", [])
        return [{"title": item["title"], "snippet": item["snippet"], "link": item["link"]} for item in items[:3]]
    else:
        app.logger.error(f"Google Custom Search error {response.status_code}: {response.text}")
        return None

def validate_investment_memo(memo, google_api_key, cse_id):
    validation_summary = "\n\n### Validation Summary:\n"
    queries = {
        "Market Opportunity": "current market size and growth trends for the industry mentioned in a startup pitch deck",
        "Competitive Landscape": "major competitors for startups in [industry] and their competitive advantages",
        "Financial Highlights": "typical financial metrics and growth projections for startups in [industry]"
    }
    for section, query in queries.items():
        validation_summary += f"\n**{section}:**\n"
        results = google_custom_search(query, google_api_key, cse_id)
        if results:
            for res in results:
                validation_summary += f"- [{res['title']}]({res['link']}): {res['snippet']}\n"
        else:
            validation_summary += "- No validation results found.\n"
    return memo + validation_summary

def generate_investment_memo(text, is_prepared=False):
    if not is_prepared:
        text = prepare_text(text, refine=False)
    if GROQ_API_KEY:
        input_text = text
        max_completion_tokens = 16384
    else:
        input_text = text[:3000]
        max_completion_tokens = 4096

    if GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-r1-distill-llama-70b",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert venture capital analyst specializing in creating detailed investment memos."
                    },
                    {
                        "role": "user",
                        "content": (
                            "Generate a detailed investment memo based on the following pitch deck content. "
                            "This memo is intended as a first-level analysis to help determine whether the startup is worth pursuing for further due diligence. "
                            "Your memo should include these sections:\n\n"
                            "1. Executive Summary\n2. Market Opportunity\n3. Competitive Landscape\n4. Financial Highlights\n\n"
                            f"Pitch Deck Content: {input_text}"
                        )
                    }
                ],
                "temperature": 0.7,
                "max_tokens": max_completion_tokens
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    app.logger.error("Unexpected Groq API response structure")
            else:
                app.logger.error(f"Groq API error {response.status_code}: {response.text}")
        except Exception as e:
            app.logger.error(f"Exception in Groq API call: {str(e)}")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Generate a detailed investment memo based on the following pitch deck content. "
                    "This memo is intended as a first-level analysis to help determine whether the startup is worth pursuing for further due diligence. "
                    "Your memo should include these sections:\n\n"
                    "1. Executive Summary\n2. Market Opportunity\n3. Competitive Landscape\n4. Financial Highlights\n\n"
                    f"Pitch Deck Content: {input_text}"
                )
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"].strip()
        else:
            app.logger.error(f"OpenRouter API error {response.status_code}: {response.text}")
    except Exception as e:
        app.logger.error(f"Exception in OpenRouter API call: {str(e)}")
    
    return "Failed to generate investment memo using both services."

@app.route('/generate_memo', methods=['POST'])
def generate_memo():
    edited_text = request.form.get('edited_text')
    if not edited_text:
        return "No text provided for memo generation.", 400
    try:
        prepared_text = prepare_text(edited_text, refine=True)
        investment_memo = generate_investment_memo(prepared_text, is_prepared=True)
        return render_template('result.html', text=investment_memo, raw_text=prepared_text)
    except Exception as e:
        app.logger.error(f"Error in generate_memo: {str(e)}")
        return f"An error occurred while processing your request: {str(e)}", 500

@app.route('/validate_selection', methods=['POST'])
def validate_selection():
    data = request.get_json()
    selected_text = data.get("selected_text", "")
    if not selected_text:
        return jsonify({"error": "No text selected."}), 400
    query = "validate: " + selected_text
    results = google_custom_search(query, GOOGLE_API_KEY, GOOGLE_CSE_ID)
    validation_html = '''
    <div class="validation-container p-4 bg-gray-900 rounded-lg shadow-lg">
      <h3 class="text-xl font-bold mb-4 text-blue-300">Validation Results</h3>
    '''
    if results:
        for res in results:
            validation_html += f'''
            <div class="validation-card p-4 bg-gray-800 rounded-lg mb-2">
              <a href="{res["link"]}" target="_blank" class="text-blue-400 font-semibold hover:underline">
                {res["title"]}
              </a>
              <p class="text-gray-300 mt-1">{res["snippet"]}</p>
            </div>
            '''
    else:
        validation_html += '<p class="text-gray-300">No validation results found.</p>'
    validation_html += '</div>'
    return jsonify({"validation_html": validation_html})

# New endpoint for checking job status
@app.route('/api/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"error": "Missing job_id parameter"}), 400
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"]
    })

# Modified upload endpoint to use asynchronous processing
@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_pdf():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['pdf_file']
        if not file or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "File must be a PDF"}), 400

        # Save the file
        job_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Create job record and start background processing thread
        jobs[job_id] = {"status": "pending", "result": None}
        thread = threading.Thread(target=process_pdf_job, args=(file_path, job_id))
        thread.start()

        return jsonify({"success": True, "job_id": job_id})
    except Exception as e:
        app.logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

# IMPORTANT: Modified /api/generate-memo endpoint now allows OPTIONS for preflight requests.
@app.route('/api/generate-memo', methods=['POST', 'OPTIONS'])
def generate_memo_api():
    if request.method == 'OPTIONS':
        # Return an empty response for preflight checks
        return jsonify({}), 200
    data = request.get_json()
    text = data.get('text')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    memo = generate_investment_memo(text, is_prepared=False)
    if memo is None:
        return jsonify({"error": "Memo generation failed"}), 500
    return jsonify({"success": True, "memo": memo})

if __name__ == '__main__':
    app.run(debug=True)
