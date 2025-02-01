# app.py
import os
from flask import Flask, render_template, request
import PyPDF2
from dotenv import load_dotenv
import requests

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
print("Loaded API Key:", HF_API_KEY)  # Debug line

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def generate_investment_memo(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    payload = {
    "inputs": (
        "You are a seasoned venture capitalist. Please review the following pitch deck content and generate a detailed investment memo. "
        "Your memo should include the following sections: \n"
        "1. Executive Summary\n"
        "2. Market Opportunity\n"
        "3. Competitive Landscape\n"
        "4. Financial Highlights\n\n"
        "Pitch Deck Content:\n"
        f"{text}"
    )
}
    
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        print("Error with Hugging Face API:", response.status_code, response.text)
        return "An error occurred while generating the investment memo."
    
    response_json = response.json()
    
    try:
        summary_text = response_json[0]['summary_text']
    except (KeyError, IndexError):
        summary_text = "Could not extract summary from API response."
    
    return summary_text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files.get('pdf_file')
        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Extract text from the PDF
            extracted_text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"

            # Call the API to generate an investment memo
            investment_memo = generate_investment_memo(extracted_text)

            # Render the result template and pass the investment memo
            return render_template('result.html', text=investment_memo)
        else:
            return "Please upload a valid PDF file.", 400
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
