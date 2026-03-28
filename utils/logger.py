"""
Logger configuration using loguru
"""

import sys
from loguru import logger
import os

# Remove default handler
logger.remove()

# Console handler with colors
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO")
)

# File handler
logger.add(
    "logs/gramin_sahayak_{time:YYYY-MM-DD}.log",
    rotation="500 MB",
    retention="10 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    level="DEBUG"
)

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Export logger
__all__ = ['logger']