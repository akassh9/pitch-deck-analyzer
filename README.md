Below is an architectural and code-level documentation designed to help new developers onboard onto the **Pitch Deck Analyzer** application. This document explains the core folder structure, what each file does, the technology stack, and how the request flow works from PDF upload to generating/validating an investment memo.

---

# Table of Contents
1. [Overview & Goals](#overview--goals)  
2. [Technology Stack](#technology-stack)  
3. [Project Structure](#project-structure)  
   1. [Root-Level](#root-level)  
   2. [Backend](#backend)  
   3. [Frontend](#frontend)  
   4. [Uploads](#uploads)  
   5. [Testing](#testing)  
4. [Backend Architecture & Flow](#backend-architecture--flow)  
5. [Frontend Architecture & Flow](#frontend-architecture--flow)  
6. [Detailed File Explanations](#detailed-file-explanations)  
   1. [Backend Files](#backend-files)  
   2. [Frontend Files](#frontend-files)  
7. [Environment Variables](#environment-variables)  
8. [How to Run Locally](#how-to-run-locally)  
9. [Key Workflows](#key-workflows)  
   1. [Uploading and Extracting PDF](#uploading-and-extracting-pdf)  
   2. [Generating Memo](#generating-memo)  
   3. [Validating Selections](#validating-selections)  
10. [Extending & Debugging](#extending--debugging)  

---

## 1. Overview & Goals
This project provides an end-to-end workflow for **analyzing pitch decks** and generating an **investment memo**. The main steps are:
1. **Upload a pitch deck PDF**.  
2. **Extract and clean textual data** (including OCR, if needed).  
3. **Generate an investment memo** using external LLM APIs.  
4. **Validate sections** of the memo by performing web searches (via Google CSE).  

The goal is to streamline the initial due diligence on a startup pitch deck by quickly generating a first-pass memo and verifying claims through an automated process.

---

## 2. Technology Stack
- **Frontend**: 
  - [Next.js](https://nextjs.org/) (App Router) & React  
  - TypeScript  
  - Tailwind CSS
- **Backend**: 
  - [Flask](https://flask.palletsprojects.com/)  
  - Python 3  
  - Redis & [RQ (Redis Queue)](https://python-rq.org/) for asynchronous job processing
- **External Services**:
  - [Google Custom Search Engine (CSE)](https://developers.google.com/custom-search/v1/overview)  
  - [OpenRouter / Groq APIs](https://openrouter.ai/) for LLM text generation  
- **PDF Parsing**: 
  - [PyPDF2](https://pypi.org/project/PyPDF2/)  
  - [pdfplumber](https://pypi.org/project/pdfplumber/)  
  - [pytesseract](https://pypi.org/project/pytesseract/) for OCR  

---

## 3. Project Structure

### Root-Level
```
pitch-deck-analyzer
├── backend/
├── frontend/
├── uploads/
├── app.log
├── generate_test_pdf.py
├── package.json
├── README.md
├── test_api.py
└── test_pitch_deck.pdf
```
- **app.log**: The main log file (though logs can also come from `backend/app.log`).  
- **generate_test_pdf.py**: An auxiliary script to create a dummy PDF for testing.  
- **test_api.py**: A placeholder or example test script for the backend.  
- **test_pitch_deck.pdf**: A sample pitch deck used for testing.  
- **package.json**: Potential Node-level script definitions, though the main Node project is in `frontend/`.  

### 3.1 Backend
Located in the `backend` folder:
```
backend
├── services/
│   └── investment_memo_service.py
├── app.py
├── config.py
├── job_manager.py
├── pdf_processing.py
├── tasks.py
├── utils.py
└── wsgi.py
```
- Implements Flask endpoints and uses RQ + Redis for asynchronous tasks.  
- Responsible for receiving the PDF, extracting text, generating memos, and returning the results.

### 3.2 Frontend
Located in the `frontend` folder:
```
frontend
├── app/
│   ├── api/
│   ├── components/
│   ├── edit/
│   ├── loading/
│   ├── result/
│   ├── page.tsx
│   └── ...
├── components/
├── public/
├── styles/
├── next-env.d.ts
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
└── ...
```
- **Next.js** (App Router) front end with pages for:
  1. Uploading a file (`page.tsx`)
  2. Loading/progress display (`loading/page.tsx`)
  3. Editing extracted text (`edit/page.tsx`)
  4. Viewing results (`result/page.tsx`).

### 3.3 Uploads
```
uploads/
└── test_pitch_deck.pdf
```
- Stores uploaded PDFs temporarily on the server. A cleanup routine removes the file once processing is done.

### 3.4 Testing
- Minimal test coverage currently. There is a file `test_api.py` that presumably interacts with the backend for integration testing.

---

## 4. Backend Architecture & Flow

1. **Flask Application**: `app.py` defines the primary routes and sets up error handling and CORS.  
2. **Job Queue**: 
   - We store `job_id` in Redis to track progress.  
   - A request to `/api/upload` enqueues a PDF processing job (`process_pdf_task` in `tasks.py`).  
   - Progress is updated at each page processed; final refined text is stored in Redis when done.  
3. **PDF Processing**: 
   - Implemented in `pdf_processing.py` using `PyPDF2`, `pdfplumber`, Tesseract, and some text-cleaning functions in `utils.py`.  
4. **Investment Memo Generation**: 
   - Endpoints `/api/generate-memo` or `/generate_memo` call `generate_investment_memo()` (or `generate_memo()` in `investment_memo_service.py`), which uses either **Groq** or **OpenRouter** LLM APIs to produce a textual memo.  
5. **Validation**: 
   - The endpoint `/api/validate-selection` calls a custom Google CSE to find relevant articles that validate (or provide context to) a user-selected snippet from the final memo.  

---

## 5. Frontend Architecture & Flow

1. **Page Routes** (under `frontend/app`):
   - **`page.tsx`**: The home page with PDF upload.  
   - **`loading/page.tsx`**: A progress bar screen polling job status.  
   - **`edit/page.tsx`**: Allows the user to edit extracted text before analysis.  
   - **`result/page.tsx`**: Displays the generated memo and optional “Model Reasoning” section, plus a “Validate Selection” feature.  
2. **API Routes** (under `frontend/app/api`):
   - **`upload/route.ts`** calls the backend `/api/upload`.  
   - **`generate-memo/route.ts`** calls `/api/generate-memo` on the backend.  
   - **`validate-selection/route.ts`** calls `/api/validate-selection` on the backend.  
3. **UI Components**:
   - **`Header.tsx`**: Contains a simple top navbar.  
   - **`ValidationResults.tsx`**: A reusable component for displaying validation results.  

---

## 6. Detailed File Explanations

### 6.1 Backend Files

1. **`backend/app.py`**  
   - **Flask Initialization** and creation of the `app` object.  
   - **Global error handling** for HTTP and internal exceptions.  
   - **CORS** configuration.  
   - Defines the main routes:
     - `/` (health check)  
     - `/generate_memo` (web form version – returns HTML)  
     - `/api/validate-selection` (validates user selections via Google CSE)  
     - `/api/status` (checks job status in Redis)  
     - `/api/upload` (handles PDF upload, enqueues the extraction job)  
     - `/api/cleanup` (cleanup job in Redis)  
     - `/api/generate-memo` (JSON version for generating a memo)  
     - `/web/generate-memo` (HTML version for generating a memo)  
   - **Helper functions**:
     - `google_custom_search()` for performing a limited Google CSE query.  
     - `validate_investment_memo()` for adding a “Validation Summary” to a memo.  
     - `generate_investment_memo()` to call external LLM APIs.  
     - `api_response()` to return consistent JSON.  

2. **`backend/config.py`**  
   - Manages environment variables using [python-dotenv](https://pypi.org/project/python-dotenv/).  
   - Class `Config` consolidates keys for HuggingFace, Google, and Groq.  
   - `validate_config()` ensures that required environment variables are present.

3. **`backend/job_manager.py`**  
   - Connects to Redis.  
   - Provides CRUD for job data with expiration (defaults to one hour).  
   - `create_job()`, `update_job()`, `get_job()`, `delete_job()`.  

4. **`backend/tasks.py`**  
   - The RQ task definitions.  
   - Currently, it just wraps `process_pdf_job()` from `pdf_processing.py`.  

5. **`backend/pdf_processing.py`**  
   - The main asynchronous job that:
     1. **Reads PDF pages** with `PyPDF2`.  
     2. Checks if each page **needs OCR** using heuristics.  
     3. If needed, attempts extraction with `pdfplumber` or Tesseract OCR.  
     4. Filters out noise (like “intro”, “thank you” slides).  
     5. Periodically updates `job_id` progress.  
     6. Calls `prepare_text(..., refine=True)` for final cleanup.  
     7. Stores the refined text in Redis.  
     8. Cleans up (removes the file).  

6. **`backend/utils.py`**  
   - Various utility functions for text extraction and cleanup:
     - `is_noise_page(text)`: Checks common noise keywords.  
     - `needs_ocr(text)`: Checks if page text is short or mostly non-alphanumeric.  
     - `ocr_page(image)`: Performs OCR using Tesseract.  
     - `prepare_text(raw_text, refine=False)`: The main text pipeline:
       1. `clean_text()` → fix spacing, remove repeated lines  
       2. If `refine=True`, calls `_refine_text()` with an LLM to reformat the text.  

7. **`backend/services/investment_memo_service.py`**  
   - Contains the helper methods to generate the memo using external APIs:
     - `_call_groq_api()`  
     - `_call_openrouter_api()`  
   - `generate_memo()` picks which service to call based on environment variables and handles fallback.  

8. **`backend/wsgi.py`**  
   - Standard WSGI entry point that references `app` from `app.py`.  

### 6.2 Frontend Files

1. **App Router Structure** (`frontend/app`):
   - **`page.tsx`** (Home / Upload): 
     - Allows user to select a PDF file, then triggers an upload to `api/upload/route.ts`.  
   - **`loading/page.tsx`**: 
     - Displays a progress bar that polls `/api/status?job_id=XXX` until text extraction completes or fails.  
   - **`edit/page.tsx`**: 
     - Fetches the extracted text from Local Storage (`extractedText`).  
     - Allows the user to edit it, then calls `api/generate-memo/route.ts` to produce the final memo.  
   - **`result/page.tsx`**: 
     - Displays the generated memo (from Local Storage).  
     - Provides “Validate Selection” by sending the user’s highlighted text to `api/validate-selection/route.ts`.

2. **API Routes** (in `frontend/app/api`):
   - **`upload/route.ts`** → hits `POST /api/upload` on the backend.  
   - **`generate-memo/route.ts`** → hits `POST /api/generate-memo`.  
   - **`validate-selection/route.ts`** → hits `POST /api/validate-selection`.

3. **Global Components**:
   - **`Header.tsx`**: Basic top header (e.g. the logo).  
   - **`ValidationResults.tsx`**: An example reusable component to show Google CSE results.  

4. **Global CSS**:
   - **`globals.css`**: Base Tailwind setup and some theme variables.  

---

## 7. Environment Variables
All environment variables are loaded in `backend/config.py`. The required ones are:
- `HF_API_KEY`: The Hugging Face or OpenRouter API key used to call the text-generation model.  
- `GROQ_API_KEY`: (Optional) The Groq API key. If provided, the code will try this first.  
- `GOOGLE_API_KEY`: Google API key used for custom search validation.  
- `GOOGLE_CSE_ID`: Google Custom Search Engine ID.  
- `REDIS_URL`: (Optional) Defaults to `redis://localhost:6379/0` if not provided.  

Failure to provide mandatory variables will result in a runtime error at launch time.

---

## 8. How to Run Locally

**Prerequisites**:
- Python 3.9+  
- Redis server (install or run Docker: `docker run -p 6379:6379 redis`)  
- Node.js 16+  

**Steps**:
1. **Clone the repo**:  
   ```bash
   git clone https://github.com/YourOrg/pitch-deck-analyzer.git
   cd pitch-deck-analyzer
   ```
2. **Set environment variables** in a `.env` file, e.g.:  
   ```bash
   HF_API_KEY=YOUR_OPENROUTER_OR_HF_KEY
   GOOGLE_API_KEY=YOUR_GOOGLE_KEY
   GOOGLE_CSE_ID=YOUR_CSE_ID
   GROQ_API_KEY=YOUR_GROQ_KEY
   ```
3. **Install Python backend dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   # or
   pip install flask redis rq PyPDF2 pdfplumber pytesseract ...
   ```
4. **Install Node frontend dependencies**:
   ```bash
   cd ../frontend
   npm install
   # or yarn
   ```
5. **Start Redis**:
   ```bash
   redis-server
   ```
6. **Run the backend**:
   ```bash
   cd ../backend
   python app.py
   ```
   - By default, runs on `http://localhost:5000`
7. **Run the RQ worker** (in a separate terminal):
   ```bash
   rq worker pdf_jobs
   ```
8. **Run the frontend**:
   ```bash
   cd ../frontend
   npm run dev
   ```
   - By default, runs on `http://localhost:3000`

---

## 9. Key Workflows

### 9.1 Uploading and Extracting PDF
1. User chooses a PDF on `frontend/app/page.tsx`.  
2. Form data is sent to `frontend/app/api/upload/route.ts` → which does a `fetch` to **`POST /api/upload`**.  
3. Backend:
   - Creates a Redis job (`job_id`).  
   - Stores the file temporarily in `uploads/`.  
   - Enqueues `process_pdf_task(file_path, job_id)`.  

4. The user is redirected to `frontend/app/loading/page.tsx`, which polls **`GET /api/status?job_id=XXX`** every second.  
5. Once the backend finishes extracting text (and possibly running OCR), the result is stored in Redis.  
6. The polling sees `status: complete`, fetches the extracted text, and stores it in `localStorage`.  

### 9.2 Generating Memo
1. On `frontend/app/edit/page.tsx`, user modifies extracted text and clicks **“Send for Analysis”**.  
2. A `fetch` is sent to `frontend/app/api/generate-memo/route.ts` → which calls **`POST /api/generate-memo`** on the backend.  
3. The backend calls `generate_investment_memo()` (or `generate_memo()`) → which hits either Groq or OpenRouter.  
4. The memo is returned and stored in localStorage.  
5. The user is redirected to `frontend/app/result/page.tsx` to view the memo.

### 9.3 Validating Selections
1. On the Result page, user highlights text.  
2. Clicking **“Validate Selection”** calls `frontend/app/api/validate-selection/route.ts` → which calls **`POST /api/validate-selection`** with `selected_text`.  
3. Backend queries Google CSE and returns top 3 results.  
4. The frontend displays these search results in a collapsible UI section.

---

## 10. Extending & Debugging

1. **Add new memo sections**:  
   - Modify the prompt in `investment_memo_service.py` or `app.py → generate_investment_memo`.  
2. **Adjust OCR thresholds**:  
   - Tweak `needs_ocr()` in `utils.py`.  
3. **Debugging**:  
   - Check `app.log` and console logs.  
   - Redis job data can be inspected via `redis-cli`.  
   - If using Docker, ensure containers are healthy and volumes are mounted correctly.
4. **Add new API routes**:  
   - In **backend**: Create a new Flask route.  
   - In **frontend**: Add a Next.js route under `frontend/app/api/...`.  

---

### Final Note
This codebase leverages asynchronous processing for PDF extraction to ensure the main Flask thread remains responsive. The user experience is primarily orchestrated on the frontend (Next.js) with smooth transitions and progress updates, while the backend focuses on text extraction, cleanup, LLM requests, and validation with external APIs.

Should you have any questions or need to add additional functionality, this overview should serve as your starting guide. Happy coding!
