"""
JSON-based storage layer with atomic writes and asyncio locking.
Handles config, mappings, and active requests persistence.
"""
import os
import json
import asyncio
import time
import tempfile
import logging
from datetime import datetime
from typing import Any, Optional
import aiofiles

from config import (
    DATA_DIR, CONFIG_FILE, MAPPINGS_FILE, REQUESTS_FILE,
    OWNER_ID, TIMEOUT_SECONDS, REPLY_IDLE_SECONDS, 
    EDIT_DEBOUNCE_SECONDS, CLEANUP_HOURS
)

logger = logging.getLogger(__name__)

_config_lock = asyncio.Lock()
_mappings_lock = asyncio.Lock()
_requests_lock = asyncio.Lock()


def _ensure_data_dir():
    """Ensure data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


async def _atomic_write(filepath: str, data: dict):
    """Write data to file atomically using temp file + rename."""
    _ensure_data_dir()
    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        os.close(temp_fd)
        async with aiofiles.open(temp_path, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
        os.replace(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise e


async def _read_json(filepath: str, default: dict) -> dict:
    """Read JSON file or return default if not exists/corrupt."""
    if not os.path.exists(filepath):
        return default.copy()
    try:
        async with aiofiles.open(filepath, 'r') as f:
            content = await f.read()
            return json.loads(content) if content.strip() else default.copy()
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Error reading {filepath}: {e}, using defaults")
        return default.copy()


def _get_default_config() -> dict:
    """Return default configuration structure."""
    return {
        "global_bot": None,
        "chat_bots": {},
        "owner_id": OWNER_ID,
        "allowed_users": [OWNER_ID] if OWNER_ID else [],
        "settings": {
            "timeout": TIMEOUT_SECONDS,
            "reply_idle": REPLY_IDLE_SECONDS,
            "edit_debounce": EDIT_DEBOUNCE_SECONDS,
            "cleanup_hours": CLEANUP_HOURS
        }
    }


def _get_default_mappings() -> dict:
    """Return default mappings structure."""
    return {
        "created_at": datetime.utcnow().isoformat(),
        "mappings": []
    }


def _get_default_requests() -> dict:
    """Return default requests structure."""
    return {
        "active_requests": {}
    }


class ConfigStorage:
    """Handles configuration storage (global bot, per-chat bots, allowed users)."""
    
    _cache: Optional[dict] = None
    
    @classmethod
    async def load(cls) -> dict:
        """Load config from file or cache."""
        async with _config_lock:
            if cls._cache is None:
                cls._cache = await _read_json(CONFIG_FILE, _get_default_config())
                if cls._cache.get("owner_id") == 0 and OWNER_ID:
                    cls._cache["owner_id"] = OWNER_ID
                if OWNER_ID and OWNER_ID not in cls._cache.get("allowed_users", []):
                    cls._cache.setdefault("allowed_users", []).append(OWNER_ID)
            return cls._cache
    
    @classmethod
    async def save(cls):
        """Save current cache to file."""
        async with _config_lock:
            if cls._cache:
                await _atomic_write(CONFIG_FILE, cls._cache)
    
    @classmethod
    async def get_global_bot(cls) -> Optional[str]:
        """Get global default bot username."""
        config = await cls.load()
        return config.get("global_bot")
    
    @classmethod
    async def set_global_bot(cls, bot_username: str):
        """Set global default bot username."""
        config = await cls.load()
        config["global_bot"] = bot_username
        await cls.save()
    
    @classmethod
    async def get_chat_bot(cls, chat_id: int) -> Optional[str]:
        """Get bot for specific chat, fallback to global."""
        config = await cls.load()
        chat_id_str = str(chat_id)
        chat_bot = config.get("chat_bots", {}).get(chat_id_str)
        return chat_bot or config.get("global_bot")
    
    @classmethod
    async def set_chat_bot(cls, chat_id: int, bot_username: str):
        """Set bot for specific chat."""
        config = await cls.load()
        config.setdefault("chat_bots", {})[str(chat_id)] = bot_username
        await cls.save()
    
    @classmethod
    async def get_allowed_users(cls) -> list:
        """Get list of allowed user IDs."""
        config = await cls.load()
        return config.get("allowed_users", [])
    
    @classmethod
    async def is_allowed(cls, user_id: int) -> bool:
        """Check if user is allowed to use /strco."""
        config = await cls.load()
        owner = config.get("owner_id", OWNER_ID)
        if user_id == owner:
            return True
        return user_id in config.get("allowed_users", [])
    
    @classmethod
    async def allow_user(cls, user_id: int):
        """Add user to allowed list."""
        config = await cls.load()
        if user_id not in config.setdefault("allowed_users", []):
            config["allowed_users"].append(user_id)
            await cls.save()
    
    @classmethod
    async def disallow_user(cls, user_id: int):
        """Remove user from allowed list."""
        config = await cls.load()
        owner = config.get("owner_id", OWNER_ID)
        if user_id == owner:
            return False
        allowed = config.get("allowed_users", [])
        if user_id in allowed:
            allowed.remove(user_id)
            await cls.save()
            return True
        return False
    
    @classmethod
    async def get_owner_id(cls) -> int:
        """Get owner ID."""
        config = await cls.load()
        return config.get("owner_id", OWNER_ID)
    
    @classmethod
    async def get_settings(cls) -> dict:
        """Get settings dict."""
        config = await cls.load()
        return config.get("settings", {
            "timeout": TIMEOUT_SECONDS,
            "reply_idle": REPLY_IDLE_SECONDS,
            "edit_debounce": EDIT_DEBOUNCE_SECONDS,
            "cleanup_hours": CLEANUP_HOURS
        })


class MappingsStorage:
    """Handles message mappings for edit mirroring."""
    
    _cache: Optional[dict] = None
    
    @classmethod
    async def load(cls) -> dict:
        """Load mappings from file or cache."""
        async with _mappings_lock:
            if cls._cache is None:
                cls._cache = await _read_json(MAPPINGS_FILE, _get_default_mappings())
            return cls._cache
    
    @classmethod
    async def save(cls):
        """Save mappings to file immediately (for crash safety)."""
        async with _mappings_lock:
            if cls._cache:
                await _atomic_write(MAPPINGS_FILE, cls._cache)
    
    @classmethod
    async def add_mapping(cls, bot_chat_id: int, bot_msg_id: int, 
                          origin_chat_id: int, mirrored_msg_id: int,
                          msg_type: str = "text", content_hash: str = ""):
        """Add a new message mapping."""
        data = await cls.load()
        mapping = {
            "ts": int(time.time()),
            "bot_chat_id": bot_chat_id,
            "bot_msg_id": bot_msg_id,
            "origin_chat_id": origin_chat_id,
            "mirrored_msg_id": mirrored_msg_id,
            "type": msg_type,
            "last_hash": content_hash
        }
        data["mappings"].append(mapping)
        await cls.save()
    
    @classmethod
    async def get_mapping(cls, bot_chat_id: int, bot_msg_id: int) -> Optional[dict]:
        """Get mapping by bot message info."""
        data = await cls.load()
        for m in data.get("mappings", []):
            if m["bot_chat_id"] == bot_chat_id and m["bot_msg_id"] == bot_msg_id:
                return m
        return None
    
    @classmethod
    async def update_hash(cls, bot_chat_id: int, bot_msg_id: int, new_hash: str):
        """Update the content hash for a mapping."""
        data = await cls.load()
        for m in data.get("mappings", []):
            if m["bot_chat_id"] == bot_chat_id and m["bot_msg_id"] == bot_msg_id:
                m["last_hash"] = new_hash
                await cls.save()
                return
    
    @classmethod
    async def update_mapping(cls, bot_chat_id: int, bot_msg_id: int, 
                             new_mirrored_msg_id: int, new_hash: str, new_type: str = None):
        """Update an existing mapping with new mirrored message info (for media replacement)."""
        data = await cls.load()
        for m in data.get("mappings", []):
            if m["bot_chat_id"] == bot_chat_id and m["bot_msg_id"] == bot_msg_id:
                m["mirrored_msg_id"] = new_mirrored_msg_id
                m["last_hash"] = new_hash
                m["ts"] = int(time.time())
                if new_type:
                    m["type"] = new_type
                await cls.save()
                return True
        return False
    
    @classmethod
    async def cleanup_old(cls, hours: int):
        """Remove mappings older than specified hours."""
        data = await cls.load()
        cutoff = int(time.time()) - (hours * 3600)
        original_count = len(data.get("mappings", []))
        data["mappings"] = [m for m in data.get("mappings", []) if m.get("ts", 0) > cutoff]
        removed = original_count - len(data["mappings"])
        if removed > 0:
            logger.info(f"Cleaned up {removed} old mappings")
            await cls.save()
        return removed


class RequestsStorage:
    """Handles active relay request tracking."""
    
    _cache: Optional[dict] = None
    
    @classmethod
    async def load(cls) -> dict:
        """Load requests from file or cache."""
        async with _requests_lock:
            if cls._cache is None:
                cls._cache = await _read_json(REQUESTS_FILE, _get_default_requests())
            return cls._cache
    
    @classmethod
    async def save(cls):
        """Save requests to file."""
        async with _requests_lock:
            if cls._cache:
                await _atomic_write(REQUESTS_FILE, cls._cache)
    
    @classmethod
    async def add_request(cls, origin_chat_id: int, bot_chat_id: int, 
                          sent_to_bot_msg_id: int, request_id: str):
        """Track a new relay request."""
        data = await cls.load()
        data["active_requests"][str(origin_chat_id)] = {
            "request_id": request_id,
            "bot_chat_id": bot_chat_id,
            "sent_to_bot_msg_id": sent_to_bot_msg_id,
            "started_ts": int(time.time())
        }
        await cls.save()
    
    @classmethod
    async def get_request(cls, origin_chat_id: int) -> Optional[dict]:
        """Get active request for a chat."""
        data = await cls.load()
        return data.get("active_requests", {}).get(str(origin_chat_id))
    
    @classmethod
    async def remove_request(cls, origin_chat_id: int):
        """Remove completed request."""
        data = await cls.load()
        if str(origin_chat_id) in data.get("active_requests", {}):
            del data["active_requests"][str(origin_chat_id)]
            await cls.save()
    
    @classmethod
    async def cleanup_stale(cls, timeout_seconds: int):
        """Remove requests older than timeout."""
        data = await cls.load()
        cutoff = int(time.time()) - timeout_seconds
        stale = [k for k, v in data.get("active_requests", {}).items() 
                 if v.get("started_ts", 0) < cutoff]
        for k in stale:
            del data["active_requests"][k]
        if stale:
            logger.info(f"Cleaned up {len(stale)} stale requests")
            await cls.save()
