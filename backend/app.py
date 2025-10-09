"""
Main application entry point for the Pitch Deck Analyzer API.
This module creates and configures the Flask application.
"""

import logging
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# When this module is executed directly (``python backend/app.py``) Python does
# not treat ``backend`` as a package, so the relative imports below fail.  This
# fallback ensures the parent directory is available on ``sys.path`` and the
# absolute package imports succeed in both execution modes.
if __package__ in (None, ""):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    from backend.config import Config  # type: ignore
    from backend.api.pdf_controller import pdf_bp  # type: ignore
    from backend.api.memo_controller import memo_bp  # type: ignore
    from backend.utils.error_handling import (  # type: ignore
        ApplicationError,
        handle_application_error,
    )
else:
    from .config import Config
    from .api.pdf_controller import pdf_bp
    from .api.memo_controller import memo_bp
    from .utils.error_handling import ApplicationError, handle_application_error

def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Configuration object to use (defaults to Config)
        
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    
    # Apply configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(Config)
    
    # Configure logging
    Config.configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Pitch Deck Analyzer API")

    if config is None:
        try:
            Config.validate()
        except ValueError as exc:
            logger.error("Configuration validation failed: %s", exc)
            raise
    
    # Enable CORS
    CORS(app)
    logger.info("CORS enabled")
    
    # Register blueprints
    app.register_blueprint(pdf_bp)
    app.register_blueprint(memo_bp)
    logger.info("Registered API blueprints")
    
    # Register error handlers
    @app.errorhandler(ApplicationError)
    def handle_application_exception(error):
        response, status_code = handle_application_error(error)
        return jsonify(response), status_code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the error
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        
        # Return a generic error response
        return jsonify({
            "error": {
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        }), 500
    
    # Health check endpoint
    @app.route('/')
    def health_check():
        return jsonify({
            "status": "ok",
            "version": "1.0.0"
        }), 200
    
    logger.info("Application configuration complete")
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logging.error(f"Configuration error: {str(e)}")
        exit(1)
    
    # Run the application
    app.run(debug=Config.DEBUG)
