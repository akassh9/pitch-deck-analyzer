"""
Error handling utilities for the application.
This module provides a consistent way to handle errors across the application.
"""

class ApplicationError(Exception):
    """Base exception class for application errors."""
    
    def __init__(self, message, status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class ValidationError(ApplicationError):
    """Raised when validation fails."""
    
    def __init__(self, message, error_details=None):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")
        self.error_details = error_details or {}

class ProcessingError(ApplicationError):
    """Raised when processing fails."""
    
    def __init__(self, message):
        super().__init__(message, status_code=500, error_code="PROCESSING_ERROR")

class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type, resource_id):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, status_code=404, error_code="RESOURCE_NOT_FOUND")

class AuthorizationError(ApplicationError):
    """Raised when a user is not authorized to perform an action."""
    
    def __init__(self, message="You are not authorized to perform this action"):
        super().__init__(message, status_code=403, error_code="AUTHORIZATION_ERROR")

def handle_application_error(error):
    """Convert ApplicationError to appropriate response format."""
    response = {
        "success": False,
        "error": {
            "message": error.message,
            "code": error.error_code
        }
    }
    
    if hasattr(error, 'error_details') and error.error_details:
        response["error"]["details"] = error.error_details
        
    return response, error.status_code 