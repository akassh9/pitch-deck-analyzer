"""
Memo controller for handling memo generation and validation API endpoints.
"""

import logging
from flask import Blueprint, request, jsonify
from ..core.memo_service import get_memo_service
from ..utils.error_handling import ApplicationError, ValidationError, handle_application_error
from ..infrastructure.job_manager import create_job, update_job, get_job
from ..tasks import memo_queue, generate_memo_task

logger = logging.getLogger(__name__)

# Create blueprint
memo_bp = Blueprint('memo', __name__, url_prefix='/api')

@memo_bp.route('/generate-memo', methods=['POST'])
def generate_memo_api():
    """Generate an investment memo from text."""
    try:
        # Get request data
        data = request.json
        if not data:
            raise ValidationError("Missing request body")
            
        text = data.get('text')
        if not text:
            raise ValidationError("Missing 'text' field in request")
            
        # Get the optional template parameter (default to "default")
        template_key = data.get('template', 'default')
        
        # Create a job for tracking
        job_id = create_job()
        update_job(job_id, {"status": "processing"})
        
        logger.info(f"Starting memo generation for job {job_id} with template '{template_key}'")
        
        # Process in background using Redis Queue with template
        memo_queue.enqueue(generate_memo_task, text, job_id, template_key)
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "processing"
        }), 202
        
    except ApplicationError as e:
        logger.warning(f"Application error in generate_memo_api: {e.message}")
        return jsonify(handle_application_error(e))
    except Exception as e:
        logger.error(f"Unexpected error in generate_memo_api: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }), 500

@memo_bp.route('/validate-selection', methods=['POST'])
def validate_selection():
    """Validate a selection of text against external sources."""
    try:
        # Get request data
        data = request.json
        if not data:
            raise ValidationError("Missing request body")
            
        text = data.get('text')
        if not text:
            raise ValidationError("Missing 'text' field in request")
            
        logger.info(f"Validating selection: {text[:50]}...")
        
        # Get the memo service
        memo_service = get_memo_service()
        
        # Validate the text
        validation_results = memo_service.validate_memo(text)
        
        return jsonify({
            "success": True,
            "results": validation_results
        }), 200
        
    except ApplicationError as e:
        logger.warning(f"Application error in validate_selection: {e.message}")
        return jsonify(handle_application_error(e))
    except Exception as e:
        logger.error(f"Unexpected error in validate_selection: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }), 500

@memo_bp.route('/web/generate-memo', methods=['POST'])
def generate_memo_web():
    """Generate an investment memo from text (web endpoint)."""
    try:
        # Get form data
        text = request.form.get('text')
        if not text:
            raise ValidationError("Missing 'text' field in request")
            
        # Get the optional template parameter
        template_key = request.form.get('template', 'default')
            
        # Get the memo service
        memo_service = get_memo_service()
        
        # Generate the memo with template
        memo = memo_service.generate_memo(text, template_key=template_key)
        
        return jsonify({
            "success": True,
            "memo": memo,
            "status": "success"
        }), 200
        
    except ApplicationError as e:
        logger.warning(f"Application error in generate_memo_web: {e.message}")
        return jsonify(handle_application_error(e))
    except Exception as e:
        logger.error(f"Unexpected error in generate_memo_web: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }), 500 