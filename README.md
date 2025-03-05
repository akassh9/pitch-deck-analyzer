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