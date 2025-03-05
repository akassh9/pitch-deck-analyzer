# Pitch Deck Analyzer

A web application that analyzes pitch decks, extracts text, and generates investment memos.

## Features

- PDF upload and text extraction
- Text cleaning and processing
- Investment memo generation using LLM APIs
- Fact validation against external sources
- Asynchronous processing with job tracking

## Architecture

The application follows a clean, layered architecture:

```
backend/
├── api/                  # API routes and controllers
├── core/                 # Core business logic
├── infrastructure/       # External services, DB, etc.
├── utils/                # Utility functions
├── app.py                # Main application entry point
└── wsgi.py               # WSGI entry point

frontend/
├── app/                  # Next.js app directory
├── components/           # React components
└── lib/                  # Utility libraries
```

## Backend Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory with the following variables:
   ```
   HF_API_KEY=your_huggingface_api_key
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CSE_ID=your_google_custom_search_engine_id
   GROQ_API_KEY=your_groq_api_key
   DEBUG=True
   ```

4. Run the development server:
   ```
   python app.py
   ```

## Frontend Setup

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:5001
   ```

3. Run the development server:
   ```
   npm run dev
   ```

## API Endpoints

- `POST /api/upload`: Upload a PDF file
- `GET /api/status`: Get job status
- `POST /api/generate-memo`: Generate an investment memo
- `POST /api/validate-selection`: Validate text against external sources
- `POST /api/cleanup`: Clean up a job

## Dependencies

### Backend
- Flask: Web framework
- Redis: Job queue and caching
- PyPDF2/pdfplumber: PDF text extraction
- pdf2image/pytesseract: OCR for image-based PDFs
- Requests: API calls to LLM services

### Frontend
- Next.js: React framework
- TypeScript: Type-safe JavaScript
- TailwindCSS: Styling

## License

MIT

## Investment Memo Templates

The application supports customizable investment memo templates for different investment stages and use cases. Each template defines:
- An ordered list of sections to include in the memo
- Specific instructions for the LLM to focus on relevant aspects

### Available Templates

1. **Default Template**
   - Balanced analysis suitable for most pitch decks
   - Sections: Executive Summary, Market Opportunity, Competitive Landscape, Financial Highlights, Investment Thesis, Risks and Mitigations

2. **Seed Stage Template**
   - Focus on team capabilities, market potential, and early validation
   - Sections: Executive Summary, Market Opportunity, Team and Vision, Product and Technology, Go-to-Market Strategy, Risks and Mitigations

3. **Series A Template**
   - Emphasis on growth metrics, unit economics, and market validation
   - Sections: Executive Summary, Market Opportunity, Financial Highlights, Growth Metrics, Competitive Landscape, Unit Economics, Investment Thesis, Risks and Mitigations

4. **Growth Stage Template**
   - Focus on market leadership, scaling metrics, and operational excellence
   - Sections: Executive Summary, Financial Performance, Market Leadership, Expansion Strategy, Competitive Moat, Team Assessment, Investment Thesis, Risk Analysis

### Using Templates

To use a specific template when generating a memo, include the `template` parameter in your API request:

```bash
# Using default template
curl -X POST http://localhost:5000/api/generate-memo \
  -H "Content-Type: application/json" \
  -d '{"text": "pitch deck content", "template": "default"}'

# Using seed stage template
curl -X POST http://localhost:5000/api/generate-memo \
  -H "Content-Type: application/json" \
  -d '{"text": "pitch deck content", "template": "seed"}'
```

If no template is specified, the default template will be used.

### Custom Templates

Templates are defined in `utils/memo_templates.py`. To add a new template:

1. Add a new entry to the `TEMPLATES` dictionary
2. Specify the sections order and instructions
3. The template will be automatically available via the API

Example:
```python
TEMPLATES = {
    "custom": {
        "sections_order": [
            "Executive Summary",
            "Custom Section 1",
            "Custom Section 2"
        ],
        "instructions": "Custom instructions for the LLM..."
    }
}
```

## Development

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pitch-deck-analyzer.git
cd pitch-deck-analyzer/backend

# Install dependencies
pip install -e .
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test files
python -m pytest tests/test_memo_templates.py
python -m pytest tests/test_memo_service.py
```

### API Documentation

The memo generation endpoint accepts the following parameters:

- `text` (required): The pitch deck content to analyze
- `template` (optional): The template to use for memo generation
  - Values: "default", "seed", "seriesA", "growth"
  - Default: "default"

Response format:
```json
{
    "success": true,
    "job_id": "unique-job-id",
    "status": "processing"
}
```