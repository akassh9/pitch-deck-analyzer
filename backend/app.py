"""
Main application entry point for the Pitch Deck Analyzer API.
This module creates and configures the Flask application.
"""

import logging
from flask import Flask, jsonify
from flask_cors import CORS
from infrastructure.config import Config
from api.pdf_controller import pdf_bp
from api.memo_controller import memo_bp
from utils.error_handling import ApplicationError, handle_application_error

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