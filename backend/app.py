import os
import re
import datetime
import threading
import uuid
import time  # <-- Added for artificial delay
import requests
import json
import PyPDF2
import pdfplumber
from rq import Queue
from redis import Redis
from .tasks import process_pdf_task
from pdf2image import convert_from_path
import pytesseract
from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
from .utils import prepare_text, is_noise_page, needs_ocr, ocr_page
from backend.services.investment_memo_service import generate_memo
from .config import Config

# Use configuration values from the central Config object.
HF_API_KEY = Config.HF_API_KEY
GOOGLE_API_KEY = Config.GOOGLE_API_KEY
GOOGLE_CSE_ID = Config.GOOGLE_CSE_ID
GROQ_API_KEY = Config.GROQ_API_KEY

# Configure the Redis connection (adjust host, port, and db as needed)
redis_conn = Redis(host='localhost', port=6379, db=0)
# Create a queue named 'pdf_jobs'
queue = Queue('pdf_jobs', connection=redis_conn)

# Import Redis job management functions
from .job_manager import create_job, update_job, get_job, delete_job

app = Flask(__name__)

from flask import jsonify
from werkzeug.exceptions import HTTPException

# Global error handler for unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    # If the error is an HTTPException, use its provided status code and message.
    if isinstance(e, HTTPException):
        response = e.get_response()
        response.data = jsonify({
            "error": e.name,
            "description": e.description,
        }).data
        response.content_type = "application/json"
        app.logger.error(f"HTTP Exception: {e.name} - {e.description}")
        return response

    # Log the error with traceback for debugging.
    app.logger.error("Unhandled Exception", exc_info=True)

    # For non-HTTP exceptions, return a generic error message.
    return jsonify({
        "error": "Internal Server Error",
        "description": "An unexpected error occurred. Please try again later."
    }), 500

import logging

# Configure logging: log to console with detailed formatting.
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Optionally, configure a file handler if persistent logging is needed.
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

class ApplicationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

# Use Flask-CORS with proper configuration only.
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "https://pitch-deck-analyzer-frontend.vercel.app",
            "https://pitch-deck-analyzer-fkl0.onrender.com"
        ],
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
    if Config.GROQ_API_KEY:
        input_text = text
        max_completion_tokens = 16384
    else:
        input_text = text[:3000]
        max_completion_tokens = 4096

    if Config.GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
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
                "Authorization": f"Bearer {Config.HF_API_KEY}",
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
        raise ApplicationError("No text provided for memo generation.", status_code=400)
    prepared_text = prepare_text(edited_text, refine=True)
    investment_memo = generate_investment_memo(prepared_text, is_prepared=True)
    return render_template('result.html', text=investment_memo, raw_text=prepared_text)

@app.route('/api/validate-selection', methods=['POST'])
def validate_selection():
    data = request.get_json()
    selected_text = data.get("selected_text", "")
    if not selected_text:
        return api_response(error="No text selected", status_code=400)
    
    query = "validate: " + selected_text
    results = google_custom_search(query, Config.GOOGLE_API_KEY, Config.GOOGLE_CSE_ID)
    
    return api_response(data={
        "results": results if results else []
    })

# New endpoint for checking job status (using Redis)
@app.route('/api/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return api_response(error="Missing job_id parameter", status_code=400)
        
    job = get_job(job_id)
    if not job:
        return api_response(error="Job not found", status_code=404)
        
    return api_response(data={
        "job_id": job_id,
        "status": job.get("status"),
        "progress": job.get("progress", 0),
        "result": job.get("result")
    })

# Modified upload endpoint to use asynchronous processing with aggressive cleanup
@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_pdf():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['pdf_file']
        if not file or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "File must be a PDF"}), 400

        # Clean up any existing job using the current_job cookie
        current_job_id = request.cookies.get('current_job')
        if current_job_id:
            delete_job(current_job_id)

        # Create a new job record (assumes create_job returns a unique job_id)
        job_id = create_job()

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Enqueue the task with RQ
        job = queue.enqueue(process_pdf_task, file_path, job_id)

        response = make_response(jsonify({"success": True, "job_id": job_id}))
        response.set_cookie("current_job", job_id)
        return response
    except Exception as e:
        app.logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Endpoint to clean up job when user exits the site (to be called from frontend before unload)
@app.route('/api/cleanup', methods=['POST'])
def cleanup_job():
    data = request.get_json()
    job_id = data.get('job_id')
    if job_id:
        delete_job(job_id)
        return jsonify({"success": True})
    return jsonify({"error": "No job ID provided"}), 400

# API endpoint for memo generation
@app.route('/api/generate-memo', methods=['POST'])
def generate_memo_api():
    
    data = request.get_json()
    text = data.get('text')
    if not text:
        return jsonify({"error": "No text provided"}), 400
        
    try:
        memo = generate_investment_memo(text, is_prepared=False)
        return jsonify({
            "success": True,
            "memo": memo
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Web endpoint for HTML rendering
@app.route('/web/generate-memo', methods=['POST'])
def generate_memo_web():
    edited_text = request.form.get('edited_text')
    if not edited_text:
        return jsonify({"error": "No text provided"}), 400
        
    try:
        prepared_text = prepare_text(edited_text, refine=True)
        investment_memo = generate_investment_memo(prepared_text, is_prepared=True)
        return render_template('result.html', text=investment_memo, raw_text=prepared_text)
    except Exception as e:
        return render_template('error.html', error=str(e))

def api_response(data=None, error=None, status_code=200):
    response = {
        "success": error is None,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
        
    return jsonify(response), status_code

if __name__ == '__main__':
    app.run(debug=True)