#!/usr/bin/env python3
"""
Logging Configuration Utility
Provides centralized logging setup that can be imported and used across the project.
"""

import logging
import sys
import os


def setup_logging():
    """Configure logging to output to both console and file"""
    
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
    
    return logger


def get_logger(name=None):
    """Get a logger instance with the given name"""
    if name is None:
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)
        # Ensure named loggers propagate to root (and thus to console)
        logger.propagate = True
        # Don't add handlers to named loggers - let them use root logger's handlers
        logger.handlers = []
    
    return logger