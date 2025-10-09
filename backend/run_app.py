#!/usr/bin/env python
"""
Run script for the Pitch Deck Analyzer API.
This script starts the Flask development server.
"""

from flask import Flask
from flask_cors import CORS
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create a simple Flask app
app = Flask(__name__)
CORS(app)

# Import the necessary modules
from .config import Config
from .api.pdf_controller import pdf_bp
from .api.memo_controller import memo_bp

# Register blueprints
app.register_blueprint(pdf_bp)
app.register_blueprint(memo_bp)

# Health check endpoint
@app.route('/')
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0"
    }, 200

if __name__ == '__main__':
    logger.info("Starting Pitch Deck Analyzer API")
    app.run(host='0.0.0.0', port=5001, debug=True) 