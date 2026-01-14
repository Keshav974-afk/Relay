"""
Configuration module for Telegram Userbot.
Loads settings from environment variables and provides defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "userbot_session")
SESSION_SECRET = os.getenv("SESSION_SECRET", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "60"))
REPLY_IDLE_SECONDS = float(os.getenv("REPLY_IDLE_SECONDS", "2"))
EDIT_DEBOUNCE_SECONDS = float(os.getenv("EDIT_DEBOUNCE_SECONDS", "1.5"))
CLEANUP_HOURS = int(os.getenv("CLEANUP_HOURS", "24"))

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
MAPPINGS_FILE = os.path.join(DATA_DIR, "mappings.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")

COMMAND_PREFIX = "/strco"
