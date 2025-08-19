"""
Logging configuration for HoYoverse check-in automation.
Handles file logging with rotation and CLI output filtering.
"""

import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    """
    Configure logging with:
    - INFO+ level logs saved to files with 7-day retention
    - WARN+ level logs displayed in CLI
    - Automatic log rotation and cleanup
    """
    # Remove default handler
    logger.remove()
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # File handler: INFO+ level with 7-day retention
    logger.add(
        logs_dir / "hoyo_checkin_{time:YYYY-MM-DD}.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days",
        compression="gz",
        enqueue=True
    )
    
    # Console handler: WARN+ level only
    logger.add(
        sys.stderr,
        level="WARNING",
        format="<red>{level}</red>: {message}",
        colorize=True
    )
    
    logger.info("Logging configured - INFO+ to files, WARN+ to console")