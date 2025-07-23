class VirtuosoError(Exception):
    """Base class for application-specific errors."""
    pass

class ConfigurationError(VirtuosoError):
    """Custom exception for configuration-related errors."""
    pass

class APIError(VirtuosoError):
    """Base class for API related errors"""
    def __init__(self, api_name: str, status_code: int = 0, message: str = ""):
        self.api_name = api_name
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error for {api_name}: {status_code} - {message}")

class APIConnectionError(APIError):
    """For errors related to connecting to an API (network issues, timeouts)."""
    def __init__(self, api_name: str, message: str = None, status_code: int = 0, original_error: Exception = None):
        # Allow message to be optional for backward compatibility
        msg = message or (f"Connection error: {original_error}" if original_error else "Connection error")
        super().__init__(api_name, status_code, msg)
        self.original_error = original_error

class APIDataError(APIError):
    """For errors related to data from an API (unexpected format, validation errors)."""
    def __init__(self, api_name: str, message: str, status_code: int = 0):
        super().__init__(api_name, status_code, message=f"Data error: {message}")

class DatabaseError(VirtuosoError):
    """Custom exception for database-related errors."""
    pass 