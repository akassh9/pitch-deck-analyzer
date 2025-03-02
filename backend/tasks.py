from .pdf_processing import process_pdf_job

def process_pdf_task(file_path, job_id):
    # This function wraps the PDF processing job.
    process_pdf_job(file_path, job_id)
