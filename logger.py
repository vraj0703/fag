import logging
import os
from logging.handlers import RotatingFileHandler

from config import config

# Base dir = directory where this file is located (your project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, str(config["logging"]["dir"]))
os.makedirs(LOG_DIR, exist_ok=True)

# Define log file
LOG_FILE =  os.path.join(LOG_DIR, str(config["logging"]["file"]))
print(LOG_FILE)

# Create logger
logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)

# Formatter for logs
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# File handler (rotates after 5 MB, keeps 5 backups)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setLevel(logging.DEBUG)  # File logs everything
file_handler.setFormatter(formatter)

# Avoid duplicate logs
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
