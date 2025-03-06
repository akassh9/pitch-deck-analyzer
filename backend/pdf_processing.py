import os
import time
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from .utils.text_processing import prepare_text, is_noise_page, needs_ocr, ocr_page
from .job_manager import update_job

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
                        # Log the error using print or a logger as needed.
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
                # Update progress for extraction phase (scale extraction to 80% of total progress)
                progress = int(((i + 1) / total_pages) * 80)
                update_job(job_id, {"progress": progress})
                print(f"Updated progress to {progress}% after processing page {i+1}")
                time.sleep(0.6)
        update_job(job_id, {"progress": 80})
        print("Extraction complete, starting refinement...")
        refined_text = prepare_text(extracted_text, refine=True)
        update_job(job_id, {"result": refined_text, "status": "complete", "progress": 100})
        print("Refinement complete, job marked as complete.")
    except Exception as e:
        print(f"Error in process_pdf_job: {e}")
        update_job(job_id, {"result": str(e), "status": "error"})
    finally:
        try:
            os.remove(file_path)
        except Exception:
            pass