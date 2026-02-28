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
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
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
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # If file logging fails, log warning to console but continue
        console_handler.stream.write(f"WARNING: Could not setup file logging: {e}\n")
        console_handler.stream.flush()
    
    # Force immediate output (no buffering)
    sys.stdout.flush()
    sys.stderr.flush()
    
    return logger


def get_logger(name=None):
    """Get a logger instance with the given name"""
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)