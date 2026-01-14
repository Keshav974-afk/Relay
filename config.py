"""
Configuration module for Telegram Userbot.
Hardcoded settings for Replit deployment.
"""
import os

API_ID = 25458518
API_HASH = "e0a73353c37306f9fa68b1e2a4ba6eab"
SESSION_NAME = "userbot_session"
SESSION_SECRET = "1BVtsOJ4Bu2hEXEj-o0dt1_U1_7pllTDWyzoKMVdCKh5TBtFk1z8vI84ZsCplTYukPloKwU-JYAmPIMH_dmj0EPqZQEchGJkhuXysdAa3r6rXiK55sLKv9PeAw1pCtw5mPFaykqPEcHYxgaXdXRpTMw4RsISlVNkSYlUjgdQv7AL25Qe5_SmanFIf019afDBueWhSewGgupqyw2JKTBklgvB0MgAP4nfiLQhlxGs9jsYlX63RfT6W5tuvQoSdgT4ca2VceqK12gPdztHE5na4S-P1f8x3wtv99pXQdkn1ZLxhd3kP2sJa43GEa_JJhdCZAAm8k7c0IohZn_pB1Up4JIWaJA-FsVE="
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
