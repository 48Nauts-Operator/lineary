"""
BETTY Memory System Python SDK - Exceptions

This module defines custom exceptions for the BETTY Python SDK,
providing detailed error information and proper exception hierarchy.
"""

from typing import Dict, List, Optional, Any


class BettyException(Exception):
    """
    Base exception for all BETTY SDK errors.
    
    This is the parent class for all BETTY-specific exceptions.
    Provides common functionality for error handling and logging.
    """
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        """
        Initialize BETTY exception.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the exception."""
        
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message
    
    def __repr__(self) -> str:
        """Detailed representation of the exception."""
        
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


class BettyAPIException(BettyException):
    """
    Exception for general API errors.
    
    Raised when the BETTY API returns an error response that doesn't
    fall into more specific exception categories.
    """
    
    def __init__(self, 
                 message: str,
                 status_code: Optional[int] = None,
                 details: Dict[str, Any] = None,
                 request_id: Optional[str] = None):
        """
        Initialize API exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            request_id: Request tracking ID for debugging
        """
        
        super().__init__(message, details)
        self.status_code = status_code
        self.request_id = request_id
    
    def __str__(self) -> str:
        """String representation with status code and request ID."""
        
        parts = [self.message]
        
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        
        if self.details:
            parts.append(f"Details: {self.details}")
        
        return " | ".join(parts)


class AuthenticationException(BettyAPIException):
    """
    Exception for authentication errors.
    
    Raised when:
    - JWT token is missing or invalid
    - Token has expired
    - Token signature is invalid
    - Authentication service is unavailable
    """
    
    def __init__(self, 
                 message: str = "Authentication failed",
                 details: Dict[str, Any] = None,
                 request_id: Optional[str] = None):
        """
        Initialize authentication exception.
        
        Args:
            message: Human-readable error message
            details: Additional error details
            request_id: Request tracking ID
        """
        
        super().__init__(
            message=message,
            status_code=401,
            details=details,
            request_id=request_id
        )


class PermissionException(BettyAPIException):
    """
    Exception for permission/authorization errors.
    
    Raised when:
    - User lacks required permissions for an operation
    - Resource access is forbidden
    - Role-based access control denies access
    """
    
    def __init__(self, 
                 message: str = "Permission denied",
                 missing_permissions: List[str] = None,
                 user_permissions: List[str] = None,
                 details: Dict[str, Any] = None,
                 request_id: Optional[str] = None):
        """
        Initialize permission exception.
        
        Args:
            message: Human-readable error message
            missing_permissions: List of missing permissions
            user_permissions: List of user's current permissions
            details: Additional error details
            request_id: Request tracking ID
        """
        
        self.missing_permissions = missing_permissions or []
        self.user_permissions = user_permissions or []
        
        # Add permission info to details
        permission_details = details or {}
        permission_details.update({
            "missing_permissions": self.missing_permissions,
            "user_permissions": self.user_permissions
        })
        
        super().__init__(
            message=message,
            status_code=403,
            details=permission_details,
            request_id=request_id
        )
    
    def __str__(self) -> str:
        """String representation with permission details."""
        
        parts = [self.message]
        
        if self.missing_permissions:
            parts.append(f"Missing: {', '.join(self.missing_permissions)}")
        
        if self.user_permissions:
            parts.append(f"Current: {', '.join(self.user_permissions)}")
        
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        
        return " | ".join(parts)


class RateLimitException(BettyAPIException):
    """
    Exception for rate limiting errors.
    
    Raised when:
    - API rate limit is exceeded
    - Too many requests in a time window
    - Quota limits are reached
    """
    
    def __init__(self, 
                 message: str = "Rate limit exceeded",
                 retry_after: Optional[int] = None,
                 limit_info: Dict[str, Any] = None,
                 details: Dict[str, Any] = None,
                 request_id: Optional[str] = None):
        """
        Initialize rate limit exception.
        
        Args:
            message: Human-readable error message
            retry_after: Seconds to wait before retrying
            limit_info: Rate limit information
            details: Additional error details
            request_id: Request tracking ID
        """
        
        self.retry_after = retry_after
        self.limit_info = limit_info or {}
        
        # Add rate limit info to details
        rate_limit_details = details or {}
        rate_limit_details.update({
            "retry_after": self.retry_after,
            "limit_info": self.limit_info
        })
        
        super().__init__(
            message=message,
            status_code=429,
            details=rate_limit_details,
            request_id=request_id
        )
    
    def __str__(self) -> str:
        """String representation with rate limit details."""
        
        parts = [self.message]
        
        if self.retry_after:
            parts.append(f"Retry after: {self.retry_after}s")
        
        if self.limit_info:
            if "requests_per_minute" in self.limit_info:
                parts.append(f"Limit: {self.limit_info['requests_per_minute']}/min")
            
            if "current_usage" in self.limit_info:
                parts.append(f"Current: {self.limit_info['current_usage']}")
        
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        
        return " | ".join(parts)


class ValidationException(BettyAPIException):
    """
    Exception for request validation errors.
    
    Raised when:
    - Request data is invalid or malformed
    - Required fields are missing
    - Field values are out of range
    - Data format is incorrect
    """
    
    def __init__(self, 
                 message: str = "Request validation failed",
                 field_errors: Dict[str, List[str]] = None,
                 details: Dict[str, Any] = None,
                 request_id: Optional[str] = None):
        """
        Initialize validation exception.
        
        Args:
            message: Human-readable error message
            field_errors: Field-specific error messages
            details: Additional error details
            request_id: Request tracking ID
        """
        
        self.field_errors = field_errors or {}
        
        # Add field errors to details
        validation_details = details or {}
        validation_details.update({
            "field_errors": self.field_errors
        })
        
        super().__init__(
            message=message,
            status_code=422,
            details=validation_details,
            request_id=request_id
        )
    
    def __str__(self) -> str:
        """String representation with field error details."""
        
        parts = [self.message]
        
        if self.field_errors:
            error_summary = []
            for field, errors in self.field_errors.items():
                error_summary.append(f"{field}: {', '.join(errors)}")
            parts.append(f"Field errors: {'; '.join(error_summary)}")
        
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        
        return " | ".join(parts)


class TimeoutException(BettyException):
    """
    Exception for request timeout errors.
    
    Raised when:
    - HTTP request times out
    - WebSocket connection times out
    - Long-running operations exceed timeout
    """
    
    def __init__(self, 
                 message: str = "Request timeout",
                 timeout_seconds: Optional[float] = None,
                 operation: Optional[str] = None):
        """
        Initialize timeout exception.
        
        Args:
            message: Human-readable error message
            timeout_seconds: Timeout duration that was exceeded
            operation: Operation that timed out
        """
        
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(message, details)
    
    def __str__(self) -> str:
        """String representation with timeout details."""
        
        parts = [self.message]
        
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        
        if self.timeout_seconds:
            parts.append(f"Timeout: {self.timeout_seconds}s")
        
        return " | ".join(parts)


class ConnectionException(BettyException):
    """
    Exception for connection errors.
    
    Raised when:
    - Unable to connect to BETTY API
    - Network connectivity issues
    - DNS resolution fails
    - Connection is refused or reset
    """
    
    def __init__(self, 
                 message: str = "Connection error",
                 endpoint: Optional[str] = None,
                 underlying_error: Optional[Exception] = None):
        """
        Initialize connection exception.
        
        Args:
            message: Human-readable error message
            endpoint: Endpoint that failed to connect
            underlying_error: The underlying network error
        """
        
        self.endpoint = endpoint
        self.underlying_error = underlying_error
        
        details = {}
        if endpoint:
            details["endpoint"] = endpoint
        if underlying_error:
            details["underlying_error"] = str(underlying_error)
        
        super().__init__(message, details)
    
    def __str__(self) -> str:
        """String representation with connection details."""
        
        parts = [self.message]
        
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        
        if self.underlying_error:
            parts.append(f"Cause: {self.underlying_error}")
        
        return " | ".join(parts)


class WebSocketException(BettyException):
    """
    Exception for WebSocket-related errors.
    
    Raised when:
    - WebSocket connection fails
    - WebSocket message parsing fails
    - WebSocket is unexpectedly closed
    - WebSocket authentication fails
    """
    
    def __init__(self, 
                 message: str = "WebSocket error",
                 connection_state: Optional[str] = None,
                 close_code: Optional[int] = None,
                 close_reason: Optional[str] = None):
        """
        Initialize WebSocket exception.
        
        Args:
            message: Human-readable error message
            connection_state: Current connection state
            close_code: WebSocket close code
            close_reason: WebSocket close reason
        """
        
        self.connection_state = connection_state
        self.close_code = close_code
        self.close_reason = close_reason
        
        details = {}
        if connection_state:
            details["connection_state"] = connection_state
        if close_code is not None:
            details["close_code"] = close_code
        if close_reason:
            details["close_reason"] = close_reason
        
        super().__init__(message, details)
    
    def __str__(self) -> str:
        """String representation with WebSocket details."""
        
        parts = [self.message]
        
        if self.connection_state:
            parts.append(f"State: {self.connection_state}")
        
        if self.close_code is not None:
            parts.append(f"Close code: {self.close_code}")
        
        if self.close_reason:
            parts.append(f"Reason: {self.close_reason}")
        
        return " | ".join(parts)


class ConfigurationException(BettyException):
    """
    Exception for configuration errors.
    
    Raised when:
    - Invalid configuration values
    - Missing required configuration
    - Configuration file parsing errors
    - Environment variable issues
    """
    
    def __init__(self, 
                 message: str = "Configuration error",
                 config_field: Optional[str] = None,
                 config_value: Optional[str] = None):
        """
        Initialize configuration exception.
        
        Args:
            message: Human-readable error message
            config_field: Configuration field that has the error
            config_value: Invalid configuration value
        """
        
        self.config_field = config_field
        self.config_value = config_value
        
        details = {}
        if config_field:
            details["config_field"] = config_field
        if config_value:
            details["config_value"] = config_value
        
        super().__init__(message, details)
    
    def __str__(self) -> str:
        """String representation with configuration details."""
        
        parts = [self.message]
        
        if self.config_field:
            parts.append(f"Field: {self.config_field}")
        
        if self.config_value:
            parts.append(f"Value: {self.config_value}")
        
        return " | ".join(parts)


# Exception mapping for HTTP status codes
STATUS_CODE_EXCEPTIONS = {
    401: AuthenticationException,
    403: PermissionException,
    422: ValidationException,
    429: RateLimitException,
}


def create_api_exception(status_code: int, 
                        response_data: Dict[str, Any],
                        request_id: Optional[str] = None) -> BettyAPIException:
    """
    Create appropriate API exception based on status code and response data.
    
    Args:
        status_code: HTTP status code
        response_data: API response data
        request_id: Request tracking ID
        
    Returns:
        Appropriate BettyAPIException subclass instance
    """
    
    message = response_data.get("message", "API request failed")
    details = response_data.get("details", {})
    
    # Get appropriate exception class
    exception_class = STATUS_CODE_EXCEPTIONS.get(status_code, BettyAPIException)
    
    # Create exception with class-specific parameters
    if exception_class == PermissionException:
        return exception_class(
            message=message,
            missing_permissions=details.get("missing_permissions", []),
            user_permissions=details.get("user_permissions", []),
            details=details,
            request_id=request_id
        )
    
    elif exception_class == RateLimitException:
        return exception_class(
            message=message,
            retry_after=details.get("retry_after"),
            limit_info=details.get("limit_info", {}),
            details=details,
            request_id=request_id
        )
    
    elif exception_class == ValidationException:
        return exception_class(
            message=message,
            field_errors=details.get("field_errors", {}),
            details=details,
            request_id=request_id
        )
    
    elif exception_class == AuthenticationException:
        return exception_class(
            message=message,
            details=details,
            request_id=request_id
        )
    
    else:
        # Generic API exception
        return BettyAPIException(
            message=message,
            status_code=status_code,
            details=details,
            request_id=request_id
        )


def is_retryable_exception(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the exception is retryable, False otherwise
    """
    
    # Retryable exceptions
    if isinstance(exception, (TimeoutException, ConnectionException)):
        return True
    
    # Server errors are retryable
    if isinstance(exception, BettyAPIException):
        if exception.status_code and exception.status_code >= 500:
            return True
    
    # Rate limits are retryable after delay
    if isinstance(exception, RateLimitException):
        return True
    
    # Other exceptions are not retryable
    return False


def get_retry_delay(exception: Exception, attempt: int) -> float:
    """
    Get retry delay for an exception.
    
    Args:
        exception: Exception that occurred
        attempt: Current attempt number (1-based)
        
    Returns:
        Delay in seconds before retry
    """
    
    # Rate limit exceptions have specific retry delay
    if isinstance(exception, RateLimitException) and exception.retry_after:
        return float(exception.retry_after)
    
    # Exponential backoff for other retryable exceptions
    base_delay = 1.0
    max_delay = 60.0
    backoff_factor = 2.0
    
    delay = base_delay * (backoff_factor ** (attempt - 1))
    return min(delay, max_delay)


# Convenience functions for common error scenarios

def raise_authentication_error(message: str = None, details: Dict = None):
    """Raise authentication exception with optional details."""
    raise AuthenticationException(
        message=message or "Authentication required. Please check your API token.",
        details=details
    )


def raise_permission_error(missing_permissions: List[str], message: str = None):
    """Raise permission exception with missing permissions."""
    raise PermissionException(
        message=message or f"Missing required permissions: {', '.join(missing_permissions)}",
        missing_permissions=missing_permissions
    )


def raise_validation_error(field_errors: Dict[str, List[str]], message: str = None):
    """Raise validation exception with field errors."""
    raise ValidationException(
        message=message or "Request validation failed",
        field_errors=field_errors
    )


def raise_rate_limit_error(retry_after: int = None, message: str = None):
    """Raise rate limit exception with retry information."""
    raise RateLimitException(
        message=message or "Rate limit exceeded. Please slow down your requests.",
        retry_after=retry_after
    )