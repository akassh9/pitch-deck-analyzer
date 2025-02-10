import os
import re
from flask import Flask, render_template, request, jsonify
import PyPDF2
from dotenv import load_dotenv
import requests
from pdf2image import convert_from_path
import pytesseract
import pdfplumber
import google.generativeai as genai
import json
from flask_cors import CORS  # Add this import

# --- Helper Functions (existing ones) ---
def is_noise_page(text):
    # ... [existing code] ...
    if not text:
        return True
    lower_text = text.lower()
    noise_keywords = ['intro', 'introduction', 'thank you', 'thanks', 'acknowledgement', 'closing', 'end of presentation']
    for keyword in noise_keywords:
        if keyword in lower_text:
            return True
    return False

def advanced_fix_spaced_text(text):
    # ... [existing code] ...
    pattern = r'(?<!\S)((?:\w\s){2,}\w)(?!\S)'
    def repl(match):
        return match.group(1).replace(" ", "")
    return re.sub(pattern, repl, text)

def fix_spaced_text(text):
    # ... [existing code] ...
    text = advanced_fix_spaced_text(text)
    
    def fix_line(line):
        words = line.split()
        if words and (sum(len(w) for w in words)) < 2:
            return ''.join(words)
        return line
    return "\n".join(fix_line(line) for line in text.splitlines())

def remove_noise(text):
    # ... [existing code] ...
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
            new_sentences.append(sentence[break_point:].strip())  # Fixed: .trip() -> .strip()
        else:
            new_sentences.append(sentence)
    return "\n".join(new_sentences)

def clean_text(text):
    # ... [existing code] ...
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = fix_spaced_text(text)
    text = text.strip()
    text = remove_noise(text)
    text = insert_line_breaks(text)
    return text

def needs_ocr(text):
    # ... [existing code] ...
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
    # ... [existing code] ...
    custom_config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(image, config=custom_config)

# --- New Functions for Data Validation with External APIs ---

def google_custom_search(query, api_key, cse_id):
    """
    Performs a search using Google Custom Search API and returns the top 3 results.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cse_id, "q": query}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json()
        items = results.get("items", [])
        # Return top 3 results as a list of dicts containing title, snippet, and link.
        return [{"title": item["title"], "snippet": item["snippet"], "link": item["link"]} for item in items[:3]]
    else:
        print(f"Google Custom Search error {response.status_code}: {response.text}")
        return None

def validate_investment_memo(memo, google_api_key, cse_id):
    """
    Runs a set of predefined queries to validate key sections of the investment memo.
    Appends a Validation Summary with external sources to the memo.
    """
    validation_summary = "\n\n### Validation Summary:\n"
    
    # Define queries for the different sections.
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
    
    # Append the validation summary to the original memo.
    return memo + validation_summary

# --- End New Functions ---

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY") #openrouter
GOOGLE_AI_STUDIO_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY") #google ai studio
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

genai.configure(api_key=GOOGLE_AI_STUDIO_API_KEY)

print("Loaded API Key:", HF_API_KEY)
print(f"Loaded Groq API Key: {GROQ_API_KEY[:5]}...")  # Print first 5 chars for security

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Add headers manually after each response.
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max file size

def refine_text(text):
    """
    Uses Groq Cloud's llama2-70b-4096 model to improve text readability
    """
    if not GROQ_API_KEY:
        print("Warning: GROQ_API_KEY is not set")
        return text
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Split text into chunks if it's too long
    max_chunk_size = 4000
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    refined_chunks = []
    
    for chunk in chunks:
        data = {
            "model": "llama-3.2-1b-preview",
            "messages": [
                {
                    "role": "system",
                    "content": "Clean and improve this text for readability while strictly preserving all original factual information. Do not add, remove, or summarize any information. Only improve clarity and structure."
                },
                {
                    "role": "user",
                    "content": f"Clean and improve this text while maintaining all factual information:\n\n{chunk}"
                }
            ],
            "temperature": 0.5,
            "max_tokens": 4096
        }
        
        try:
            print(f"Calling Groq API for chunk of length {len(chunk)}...")
            response = requests.post(url, headers=headers, json=data)
            print(f"Groq API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("Response received from Groq")
                print(f"Response structure: {list(result.keys())}")
                
                if "choices" in result and len(result["choices"]) > 0:
                    refined_chunk = result["choices"][0]["message"]["content"].strip()
                    refined_chunks.append(refined_chunk)
                    print(f"Successfully refined chunk of length {len(chunk)} -> {len(refined_chunk)}")
                else:
                    print(f"Unexpected response structure: {result}")
                    refined_chunks.append(chunk)
            else:
                print(f"Error {response.status_code}: {response.text}")
                refined_chunks.append(chunk)
        except Exception as e:
            print(f"Exception in Groq API call: {str(e)}")
            refined_chunks.append(chunk)
    
    # Combine refined chunks
    refined_text = "\n".join(refined_chunks)
    return refined_text

def generate_investment_memo(text, is_refined=False):
    """
    Generates investment memo using Groq's deepseek-r1-distill-llama-70b-specdec model,
    with OpenRouter's DeepSeek R1 as fallback
    """
    if not is_refined:
        text = clean_text(text)
    truncated_text = text[:3000]
    
    # First try with Groq
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
                            "This memo is intended as a first-level analysis to help determine whether the startup is worth pursuing for further due diligence by a venture capitalist. "
                            "It is not a final investment decision, but rather a preliminary assessment of the startup's potential. "
                            "Your memo should include these sections: \n\n"
                            "1. Executive Summary – Summarize what the company does, its unique value proposition, and any standout features.\n"
                            "2. Market Opportunity – Analyze the market size, growth potential, and key trends.\n"
                            "3. Competitive Landscape – Evaluate the competitive environment and the startup's competitive edge.\n"
                            "4. Financial Highlights – Highlight key financial metrics and growth projections.\n\n"
                            "Using your own words and analysis, please provide a comprehensive memo that indicates whether the startup is worth further investigation. "
                            f"Pitch Deck Content: {truncated_text}"
                        )
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4096
            }
            
            print("Calling Groq API for memo generation...")
            response = requests.post(url, headers=headers, json=data)
            print(f"Groq API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    memo = result["choices"][0]["message"]["content"].strip()
                    print("Successfully generated memo using Groq")
                    return memo
                print("Unexpected Groq API response structure:", result)
            else:
                print(f"Groq API error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Exception in Groq API call: {str(e)}")
    
    # Fallback to OpenRouter if Groq fails
    print("Falling back to OpenRouter for memo generation...")
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-site-url.com",
        "X-Title": "Your Site Name"
    }
    
    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Generate a detailed investment memo based on the following pitch deck content. "
                    "This memo is intended as a first-level analysis to help determine whether the startup is worth pursuing for further due diligence by a venture capitalist. "
                    "It is not a final investment decision, but rather a preliminary assessment of the startup's potential. "
                    "Your memo should include these sections: \n\n"
                    "1. Executive Summary – Summarize what the company does, its unique value proposition, and any standout features.\n"
                    "2. Market Opportunity – Analyze the market size, growth potential, and key trends.\n"
                    "3. Competitive Landscape – Evaluate the competitive environment and the startup's competitive edge.\n"
                    "4. Financial Highlights – Highlight key financial metrics and growth projections.\n\n"
                    "Using your own words and analysis, please provide a comprehensive memo that indicates whether the startup is worth further investigation. "
                    f"Pitch Deck Content: {truncated_text}"
                )
            }
        ]
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            if "choices" in response_json and response_json["choices"]:
                print("Successfully generated memo using OpenRouter")
                return response_json["choices"][0]["message"]["content"]
        print(f"OpenRouter API error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Exception in OpenRouter API call: {str(e)}")
    
    return "Failed to generate investment memo using both services."

@app.route('/')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_pdf():
    if request.method == 'OPTIONS':
        # Respond to preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200

    try:
        print("Received upload request")
        print("Files in request:", request.files)
        
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['pdf_file']
        print("File name:", file.filename)
        
        if not file or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "File must be a PDF"}), 400

        print(f"Received file: {file.filename}")
        
        # Your existing PDF processing logic
        extracted_text = process_pdf(file)
        print(f"Extracted text length: {len(extracted_text)}")
        
        refined_text = refine_text(extracted_text)
        print(f"Refined text length: {len(refined_text)}")
        
        return jsonify({
            "success": True,
            "text": refined_text
        })
    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_memo', methods=['POST'])
def generate_memo():
    edited_text = request.form.get('edited_text')
    if not edited_text:
        return "No text provided for memo generation.", 400

    try:
        # Refine the edited text using Groq
        refined_text = refine_text(edited_text)
        if refined_text == edited_text:
            print("Warning: Text refinement may have failed")
        
        # Generate the investment memo
        investment_memo = generate_investment_memo(refined_text, is_refined=True)
        return render_template('result.html', text=investment_memo, raw_text=refined_text)
    except Exception as e:
        print(f"Error in generate_memo: {str(e)}")
        return f"An error occurred while processing your request: {str(e)}", 500

@app.route('/validate_selection', methods=['POST'])
def validate_selection():
    data = request.get_json()
    selected_text = data.get("selected_text", "")
    
    if not selected_text:
        return jsonify({"error": "No text selected."}), 400

    # Build the query (optional: you could add a prefix or context)
    query = "validate: " + selected_text

    results = google_custom_search(query, GOOGLE_API_KEY, GOOGLE_CSE_ID)
    
    # Build a refined HTML layout using Tailwind classes
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

@app.route('/test_groq', methods=['GET'])
def test_groq():
    test_text = "This is a test text to check if Groq API is working properly."
    result = refine_text(test_text)
    return jsonify({
        "original": test_text,
        "refined": result,
        "api_key_present": bool(GROQ_API_KEY),
        "api_key_preview": GROQ_API_KEY[:5] if GROQ_API_KEY else None
    })

@app.route('/test_groq_direct', methods=['GET'])
def test_groq_direct():
    """
    Test route to verify Groq API functionality
    """
    test_text = "This is a test text. Please improve its readability."
    print("Testing Groq API directly...")
    result = refine_text(test_text)
    success = result != test_text
    
    return jsonify({
        "success": success,
        "original": test_text,
        "refined": result,
        "api_key_present": bool(GROQ_API_KEY),
        "api_key_preview": GROQ_API_KEY[:5] if GROQ_API_KEY else None
    })

# Update other routes to return JSON
@app.route('/api/generate-memo', methods=['POST'])
def generate_memo_api():
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Your memo generation logic here
    memo = generate_investment_memo(text)

    # Ensure memo is not None
    if memo is None:
        return jsonify({"error": "Memo generation failed"}), 500

    return jsonify({"success": True, "memo": memo})

def process_pdf(file):
    """
    Process uploaded PDF file and extract text
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
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
                        print(f"pdfplumber error on page {i+1}: {e}")
                    
                    if needs_ocr(page_text):
                        try:
                            images = convert_from_path(file_path, dpi=300, first_page=i+1, last_page=i+1)
                            if images:
                                page_text = ocr_page(images[0])
                        except Exception as e:
                            print(f"OCR error on page {i+1}: {e}")
                
                if not is_noise_page(page_text):
                    extracted_text += page_text + "\n"
        
        return clean_text(extracted_text)
    finally:
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)