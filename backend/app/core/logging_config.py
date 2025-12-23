"""
Structured Logging Configuration

Configures Python logging to output structured JSON logs for easy parsing
by log aggregation tools (ELK, Loki, etc.).

The JSON format includes:
- Timestamp (ISO 8601)
- Log level
- Message
- Module/function name
- Additional context fields
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON objects with consistent structure.
    Additional context can be passed via the 'extra' parameter.
    
    Example:
        >>> logger.info("User logged in", extra={"user_id": 123, "ip": "1.2.3.4"})
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: The log record to format.
            
        Returns:
            str: JSON-formatted log message.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields passed via 'extra' parameter
        # This allows context-rich logging: logger.info("msg", extra={"user_id": 123})
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "taskName"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logging() -> None:
    """
    Configure root logger with JSON formatter.
    
    Sets up console handler that outputs JSON-formatted logs to stdout.
    All loggers in the application will inherit this configuration.
    
    This function should be called once at application startup.
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Set log level from environment
    from app.core.config import settings
    root_logger.setLevel(getattr(logging, settings.API_LOG_LEVEL.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
