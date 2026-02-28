#!/usr/bin/env python3
"""
Logging Configuration Utility
Provides centralized logging setup that can be imported and used across the project.
"""

import logging
import sys
import os

# Global flag to ensure logging is only setup once
_logging_configured = False
_config_lock = None

def setup_logging():
    """Configure logging to output to both console and file (idempotent - only runs once)"""
    global _logging_configured, _config_lock
    
    # Import threading here to avoid circular imports
    if _config_lock is None:
        import threading
        _config_lock = threading.Lock()
    
    # Double-checked locking pattern for thread safety
    if _logging_configured:
        return logging.getLogger()
    
    with _config_lock:
        if _logging_configured:
            return logging.getLogger()
        
        # Setup root logger first
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers to avoid conflicts
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler (for Docker logs) - this must work!
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        
        # File handler (separate try-catch so console always works)
        log_path = os.getenv("LOG_PATH", "/app/logs/output.log")
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            # If file logging fails, log warning to console but continue
            logger.warning(f"Could not setup file logging: {e}")
        
        # Ensure all loggers propagate to root
        logging.getLogger().propagate = True
        
        # Disable buffering for immediate output
        for handler in logger.handlers:
            if hasattr(handler, 'stream'):
                handler.stream.reconfigure(line_buffering=True)
        
        # Force immediate output (no buffering)
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Mark as configured
        _logging_configured = True
        logger.info("📋 Logging configured successfully")
        
        return logger


def get_logger(name=None):
    """Get a logger instance with the given name (automatically sets up logging if needed)"""
    # Ensure logging is configured
    if not _logging_configured:
        setup_logging()
    
    if name is None:
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)
        # Ensure named loggers propagate to root (and thus to console)
        logger.propagate = True
        # Don't add handlers to named loggers - let them use root logger's handlers
        logger.handlers = []
    
    return logger