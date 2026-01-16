"""
Configuration module for Telegram Userbot.
Hardcoded settings for Replit deployment.
"""
import os

API_ID = 25458518
API_HASH = "e0a73353c37306f9fa68b1e2a4ba6eab"
SESSION_NAME = "userbot_session"
SESSION_SECRET = "1BVtsOMcBu3v72ZykT7FJhZlimKwwcWue89IJJOeosJ1Mm5-IQzDDwJN6u4HemmG3mdvIu5OAJm74RHog8l77GcBjgS9Z8GtfXd5lAE1PFYQyQ6NF2n_ubqH8vWhqqCYc-3rnoE0TBjpntdHIXWIzeGSm9_y-sYyWfvjBeNPaFEZmPSvfh4ybYS_gXRYRtchz6mXRpDHpsf10DcEIvJgMbmauMx4DHBt90d5DX2uJPmivJA-npd-zZSVRmwD_Ysnu4CjwDBlFdmBfbyQPD59dFoMwdQedc-EnKJh4uYrWxxyCP5ttC5l8UQce04Mg0kNqmK3wuoADf7Ja5mQzlpVpWNO3LGQ_5FE="
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
