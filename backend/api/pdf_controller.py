"""
PDF controller for handling PDF-related API endpoints.
"""

import os
import logging
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from ..core.pdf_service import get_pdf_service
from ..utils.error_handling import ApplicationError, ValidationError, handle_application_error
from ..infrastructure.job_manager import create_job, get_job, delete_job
from ..infrastructure.config import Config
from ..tasks import pdf_queue, process_pdf_task

logger = logging.getLogger(__name__)

# Create blueprint
pdf_bp = Blueprint('pdf', __name__, url_prefix='/api')

@pdf_bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_pdf():
    """Upload and process a PDF file."""
    try:
        # Handle preflight OPTIONS request for CORS
        if request.method == 'OPTIONS':
            return jsonify({"status": "ok"}), 200
            
        # Check if file is present in request
        if 'file' not in request.files:
            raise ValidationError("No file part in the request")
            
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            raise ValidationError("No selected file")
            
        # Check if file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            raise ValidationError("File must be a PDF")
            
        # Create a job and save file
        job_id = create_job()
        
        # Ensure upload directory exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Save the file
        filename = secure_filename(f"{job_id}.pdf")
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        logger.info(f"Saved uploaded PDF to {file_path} with job ID {job_id}")
        
        # Process PDF in background using Redis Queue
        pdf_queue.enqueue(process_pdf_task, file_path, job_id)
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "processing"
        }), 202
        
    except ApplicationError as e:
        logger.warning(f"Application error in upload_pdf: {e.message}")
        return jsonify(handle_application_error(e))
    except Exception as e:
        logger.error(f"Unexpected error in upload_pdf: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }), 500

@pdf_bp.route('/status', methods=['GET'])
def job_status():
    """Get the status of a job."""
    try:
        job_id = request.args.get('job_id')
        if not job_id:
            raise ValidationError("Missing job_id parameter")
            
        job_data = get_job(job_id)
        if not job_data:
            raise ValidationError(f"Job {job_id} not found")
            
        return jsonify({
            "success": True,
            "data": job_data
        }), 200
        
    except ApplicationError as e:
        logger.warning(f"Application error in job_status: {e.message}")
        return jsonify(handle_application_error(e))
    except Exception as e:
        logger.error(f"Unexpected error in job_status: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }), 500

@pdf_bp.route('/cleanup', methods=['POST'])
def cleanup_job():
    """Clean up a completed job."""
    try:
        job_id = request.json.get('job_id')
        if not job_id:
            raise ValidationError("Missing job_id parameter")
            
        # Delete the job from Redis
        delete_job(job_id)
        
        # Also delete the file if it exists
        file_path = os.path.join(Config.UPLOAD_FOLDER, f"{job_id}.pdf")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file {file_path}")
            
        return jsonify({
            "success": True,
            "status": "success"
        }), 200
        
    except ApplicationError as e:
        logger.warning(f"Application error in cleanup_job: {e.message}")
        return jsonify(handle_application_error(e))
    except Exception as e:
        logger.error(f"Unexpected error in cleanup_job: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }), 500 