# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Logging configuration for Fabric deployment scripts."""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger for the deployment scripts.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level from parameter or default to INFO
    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    else:
        logger.setLevel(logging.INFO)
    
    # Only add handler if logger doesn't have handlers (avoid duplicates)
    if not logger.handlers:
        # Create console handler with formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Create formatter without timestamps for GitHub Actions (Actions adds timestamps)
        # Format: Simple message format for clean CI/CD logs
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with default configuration.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return setup_logger(name)
