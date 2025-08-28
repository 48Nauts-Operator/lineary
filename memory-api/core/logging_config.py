# ABOUTME: Structured logging configuration for BETTY Memory System
# ABOUTME: Sets up consistent JSON logging with structured fields and error tracking

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory

def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with JSON output"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level and timestamp
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Use JSON formatter for production
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

class StructuredLogger:
    """Wrapper for structured logger with common fields"""
    
    def __init__(self, logger_name: str):
        self.logger = structlog.get_logger(logger_name)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with structured fields"""
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with structured fields"""
        self.logger.error(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with structured fields"""
        self.logger.warning(message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with structured fields"""
        self.logger.debug(message, **kwargs)
    
    def database_operation(self, operation: str, table: str = None, duration: float = None, **kwargs) -> None:
        """Log database operation with standard fields"""
        fields = {
            "operation_type": "database",
            "operation": operation,
            "duration_ms": f"{duration * 1000:.2f}" if duration else None,
            **kwargs
        }
        if table:
            fields["table"] = table
        
        self.info("Database operation", **fields)
    
    def api_request(self, method: str, path: str, status_code: int = None, duration: float = None, **kwargs) -> None:
        """Log API request with standard fields"""
        fields = {
            "operation_type": "api_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": f"{duration * 1000:.2f}" if duration else None,
            **kwargs
        }
        
        self.info("API request", **fields)

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)