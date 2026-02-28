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
    log_path = os.getenv("LOG_PATH", "/app/logs/output.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        return logger
    
    # Console handler (for Docker logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (for email attachments)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name=None):
    """Get a logger instance with the given name"""
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)