"""
Configuration module for Telegram Userbot.
Hardcoded settings for Replit deployment.
"""
import os

API_ID = 25458518
API_HASH = "e0a73353c37306f9fa68b1e2a4ba6eab"
SESSION_NAME = "userbot_session"
SESSION_SECRET = "1BVts0McBu5gg4wXowLEIfki8G20Bu2_FXD0WQMowcHzRq4ihfgH-GfRCqwdCagDFBAXbIfVd1JIutcR-wYLZJkSrcg_JqHqr9M3Tl4y_ARz9cqHSE_6u-XrC5RiBfSfZMkW1D-Ixrngu6ep1JytCJgf1dlXLq-kdRpp3A2drFBMpFBtdQjpyalMxgP71RRgvM2B6qML0JacF8bgwjF_AurpbQ69Ib3Wqpak53gt06Zk3ULQ3n9QBQjl9H7PUNcXphZlTyN2mM_tbY-PjdqF2JNgHt_LgQqkvt_-apos-cuGtMoJ2iwjzgcDhaTrHNg0TLfEhv3Bj5wD7fi3MyYh50UY9vbIlVdw="
OWNER_ID = 8116724251

TIMEOUT_SECONDS = 60
REPLY_IDLE_SECONDS = 2.0
EDIT_DEBOUNCE_SECONDS = 1.5
CLEANUP_HOURS = 24

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
MAPPINGS_FILE = os.path.join(DATA_DIR, "mappings.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")

COMMAND_PREFIX = "/strco"
