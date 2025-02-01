import os
import requests
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
print("Loaded API Key:", HF_API_KEY)

# Define the API endpoint and headers
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# Prepare a simple payload for testing
payload = {"inputs": "Test input for summarization."}

# Send the POST request to the Hugging Face API
response = requests.post(API_URL, headers=headers, json=payload)

# Print out the status code and response from the API
print("Status Code:", response.status_code)
print("Response:", response.text)
