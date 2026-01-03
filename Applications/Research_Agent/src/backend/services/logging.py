"""
Centralized logging service for the Research Agent application.
Provides structured logging with file rotation, multiple log levels, and monitoring.
"""
from __future__ import annotations
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from backend.config import settings


class LoggerConfig:
    """Configuration for application logging"""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: str = "logs",
        log_file: str = "app.log",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_console: bool = True,
        enable_file: bool = True,
    ):
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_dir = Path(log_dir)
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)


# Global logger configuration
_log_config = LoggerConfig(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.getenv("LOG_DIR", "logs"),
)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(_log_config.log_level)
    
    # Format for logs
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    if _log_config.enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_log_config.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if _log_config.enable_file:
        log_path = _log_config.log_dir / _log_config.log_file
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=_log_config.max_bytes,
            backupCount=_log_config.backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(_log_config.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def configure_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "app.log",
) -> None:
    """
    Configure the global logging configuration.
    Call this once at application startup.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        log_file: Log file name
    """
    global _log_config
    _log_config = LoggerConfig(
        log_level=log_level,
        log_dir=log_dir,
        log_file=log_file,
    )


def setup_application_logging() -> None:
    """Set up logging for the application on startup."""
    configure_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_dir=os.getenv("LOG_DIR", "logs"),
    )
    
    # Get root logger and log startup
    logger = get_logger("app.startup")
    logger.info("Application logging configured")
    logger.info(f"Log level: {os.getenv('LOG_LEVEL', 'INFO')}")
    logger.info(f"Log directory: {os.getenv('LOG_DIR', 'logs')}")


class ErrorHandler:
    """Utility class for handling and logging errors"""
    
    def __init__(self):
        self.logger = get_logger("app.errors")
        self.error_counts = {}
    
    def log_error(
        self,
        error: Exception,
        context: str = "",
        severity: str = "ERROR"
    ) -> None:
        """
        Log an error with context information.
        
        Args:
            error: The exception that occurred
            context: Additional context about where/why the error occurred
            severity: Log level (ERROR, WARNING, CRITICAL)
        """
        error_key = f"{type(error).__name__}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        log_func = getattr(self.logger, severity.lower(), self.logger.error)
        
        if context:
            log_func(f"[{context}] {type(error).__name__}: {str(error)}")
        else:
            log_func(f"{type(error).__name__}: {str(error)}")
        
        # Log full traceback at debug level
        self.logger.debug(f"Full traceback:", exc_info=error)
    
    def get_error_summary(self) -> dict:
        """Get summary of errors that have occurred"""
        return self.error_counts.copy()
    
    def clear_error_summary(self) -> None:
        """Clear error count summary"""
        self.error_counts.clear()


class PerformanceLogger:
    """Utility class for logging performance metrics"""
    
    def __init__(self):
        self.logger = get_logger("app.performance")
    
    def log_operation_time(
        self,
        operation_name: str,
        duration_seconds: float,
        threshold_seconds: Optional[float] = None
    ) -> None:
        """
        Log the execution time of an operation.
        
        Args:
            operation_name: Name of the operation
            duration_seconds: How long the operation took
            threshold_seconds: If provided, warn if duration exceeds this
        """
        if threshold_seconds and duration_seconds > threshold_seconds:
            self.logger.warning(
                f"Slow operation: {operation_name} took {duration_seconds:.2f}s "
                f"(threshold: {threshold_seconds}s)"
            )
        else:
            self.logger.info(
                f"Operation: {operation_name} took {duration_seconds:.2f}s"
            )
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float
    ) -> None:
        """Log API request with timing"""
        self.logger.info(
            f"API {method} {path} -> {status_code} ({duration_seconds:.3f}s)"
        )


# Global instances
error_handler = ErrorHandler()
performance_logger = PerformanceLogger()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return error_handler


def get_performance_logger() -> PerformanceLogger:
    """Get the global performance logger instance"""
    return performance_logger
