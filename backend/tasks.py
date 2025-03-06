"""
Background tasks for asynchronous processing.
This module defines tasks that can be executed by a task queue (e.g., Redis Queue).
"""

import logging
from rq import Queue
from redis import Redis
from .infrastructure.config import Config
from .infrastructure.job_manager import update_job
from .core.pdf_service import get_pdf_service
from .core.memo_service import get_memo_service

logger = logging.getLogger(__name__)

# Configure Redis connection
redis_conn = Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB
)

# Create queues
pdf_queue = Queue('pdf_jobs', connection=redis_conn)
memo_queue = Queue('memo_jobs', connection=redis_conn)

def process_pdf_task(file_path, job_id):
    """
    Process a PDF file in the background.
    
    Args:
        file_path (str): Path to the PDF file
        job_id (str): ID of the job to update progress
    """
    try:
        logger.info(f"Starting PDF processing task for job {job_id}")
        
        # Get the PDF service
        pdf_service = get_pdf_service()
        
        # Process the PDF
        result = pdf_service.process_pdf(file_path, job_id)
        
        logger.info(f"PDF processing task completed for job {job_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in PDF processing task for job {job_id}: {str(e)}", exc_info=True)
        update_job(job_id, {"status": "failed", "error": str(e)})
        raise

def generate_memo_task(text, job_id, template_key="default"):
    """
    Generate an investment memo in the background.
    
    Args:
        text (str): The text to generate a memo from
        job_id (str): ID of the job to update progress
        template_key (str): The template to use for memo generation (default: "default")
    """
    try:
        logger.info(f"Starting memo generation task for job {job_id} with template '{template_key}'")
        
        # Update job status
        update_job(job_id, {"status": "processing", "progress": 10})
        
        # Get the memo service
        memo_service = get_memo_service()
        
        # Generate the memo with template
        memo = memo_service.generate_memo(text, template_key=template_key)
        
        # Structure the result as expected by the frontend
        result = {
            "memo": memo,
            "template_used": template_key,
            "startup_stage": "default"  # We could enhance this later to detect the stage
        }
        
        # Update job with structured result
        update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "result": result
        })
        
        logger.info(f"Memo generation task completed for job {job_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in memo generation task for job {job_id}: {str(e)}", exc_info=True)
        update_job(job_id, {"status": "failed", "error": str(e)})
        raise 