# Pitch Deck Analyzer

Pitch Deck Analyzer is a web application that allows users to upload PDF pitch decks and receive a generated investment memo based on the content of the deck. The application uses Flask for the web framework, PyPDF2 for PDF text extraction, and the Hugging Face Inference API for summarization.

## Features

- **PDF Upload:** Users can upload a pitch deck in PDF format.
- **Text Extraction:** The application extracts text from the PDF using PyPDF2.
- **AI Summarization:** The extracted text is sent to the Hugging Face Inference API to generate an investment memo.
- **Investment Memo:** The memo includes key sections such as Executive Summary, Market Opportunity, Competitive Landscape, and Financial Highlights.

## Getting Started

### Prerequisites

- Python 3.8 or later
- pip (Python package installer)
- Virtual environment (recommended)