"""
Telegram Userbot - Main entry point.
Relays /strco messages to target bots and mirrors responses.
"""
import asyncio
import logging
import sys
import time as time_module
from telethon import TelegramClient, events
from telethon.tl.types import Message
from telethon.sessions import StringSession

from config import API_ID, API_HASH, SESSION_NAME, SESSION_SECRET, OWNER_ID, COMMAND_PREFIX
from storage import ConfigStorage, MappingsStorage, RequestsStorage
from relay import process_relay_request, handle_edit

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

if not API_ID or not API_HASH:
    logger.error("API_ID and API_HASH must be set in environment variables")
    sys.exit(1)

if not OWNER_ID:
    logger.warning("OWNER_ID not set - commands will be restricted")

if SESSION_SECRET:
    logger.info("Using StringSession from SESSION_SECRET")
    client = TelegramClient(StringSession(SESSION_SECRET), API_ID, API_HASH)
else:
    logger.info("Using file-based session (requires interactive login)")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

_tracked_bot_chats: set = set()
_user_cooldowns: dict = {}
COOLDOWN_SECONDS = 5


def parse_command(text: str) -> tuple:
    """Parse command and arguments from message text."""
    if not text:
        return None, []
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else None
    args = parts[1] if len(parts) > 1 else ""
    return cmd, args


async def is_owner(user_id: int) -> bool:
    """Check if user is the owner."""
    owner = await ConfigStorage.get_owner_id()
    return user_id == owner


async def process_strco_command(event, message: Message, sender_id: int):
    """Process /strco relay command."""
    if not await ConfigStorage.is_allowed(sender_id):
        return
    
    now = time_module.time()
    cooldown_key = f"{sender_id}_{event.chat_id}"
    if cooldown_key in _user_cooldowns:
        if now - _user_cooldowns[cooldown_key] < COOLDOWN_SECONDS:
            logger.debug(f"Cooldown active for user {sender_id}, ignoring")
            return
    _user_cooldowns[cooldown_key] = now
    
    logger.info(f"Processing /strco relay from user {sender_id} in chat {event.chat_id}")
    
    target_bot = await ConfigStorage.get_chat_bot(event.chat_id)
    if target_bot:
        try:
            bot_entity = await client.get_entity(target_bot)
            _tracked_bot_chats.add(bot_entity.id)
        except Exception as e:
            logger.warning(f"Could not track bot chat: {e}")
    
    await process_relay_request(client, message, event.chat_id)


@client.on(events.NewMessage(outgoing=True))
async def handle_outgoing(event: events.NewMessage.Event):
    """Handle outgoing messages (from owner account)."""
    message: Message = event.message
    sender_id = (await client.get_me()).id
    
    text = message.text or message.message or ""
    cmd, args = parse_command(text)
    
    if cmd == "/strcohelp":
        help_text = """**Telegram Relay Userbot Commands**

**Relay:**
`/strco <message>` - Relay message to target bot

**Bot Configuration:**
`/setstrco @BotUsername` - Set bot for this chat
`/setstrcoglobal @BotUsername` - Set global default bot
`/strcobot` - Show current target bot

**Access Control (Owner only):**
`/allow <user_id>` - Allow user to use /strco
`/disallow <user_id>` - Revoke access
`/allowed` - List allowed users

`/strcohelp` - Show this help"""
        await event.respond(help_text)
        return
    
    if cmd == "/setstrco":
        if not await is_owner(sender_id):
            return
        bot_username = args.strip()
        if not bot_username or not bot_username.startswith("@"):
            await event.respond("Usage: /setstrco @BotUsername")
            return
        await ConfigStorage.set_chat_bot(event.chat_id, bot_username)
        await event.respond(f"Target bot for this chat set to: {bot_username}")
        return
    
    if cmd == "/setstrcoglobal":
        if not await is_owner(sender_id):
            return
        bot_username = args.strip()
        if not bot_username or not bot_username.startswith("@"):
            await event.respond("Usage: /setstrcoglobal @BotUsername")
            return
        await ConfigStorage.set_global_bot(bot_username)
        await event.respond(f"Global target bot set to: {bot_username}")
        return
    
    if cmd == "/strcobot":
        chat_bot = await ConfigStorage.get_chat_bot(event.chat_id)
        if chat_bot:
            await event.respond(f"Current target bot: {chat_bot}")
        else:
            await event.respond("No target bot configured. Use /setstrco or /setstrcoglobal")
        return
    
    if cmd == "/allow":
        if not await is_owner(sender_id):
            await event.respond("Not allowed.")
            return
        try:
            user_id = int(args.strip())
            await ConfigStorage.allow_user(user_id)
            await event.respond(f"User {user_id} is now allowed to use /strco")
        except ValueError:
            await event.respond("Usage: /allow <user_id>")
        return
    
    if cmd == "/disallow":
        if not await is_owner(sender_id):
            await event.respond("Not allowed.")
            return
        try:
            user_id = int(args.strip())
            result = await ConfigStorage.disallow_user(user_id)
            if result:
                await event.respond(f"User {user_id} access revoked")
            else:
                await event.respond("Cannot remove owner or user not in list")
        except ValueError:
            await event.respond("Usage: /disallow <user_id>")
        return
    
    if cmd == "/allowed":
        if not await is_owner(sender_id):
            await event.respond("Not allowed.")
            return
        allowed = await ConfigStorage.get_allowed_users()
        owner = await ConfigStorage.get_owner_id()
        users_str = "\n".join([f"- {uid}" + (" (owner)" if uid == owner else "") for uid in allowed])
        await event.respond(f"**Allowed Users:**\n{users_str}" if users_str else "No users allowed")
        return
    
    if text.startswith(COMMAND_PREFIX):
        await process_strco_command(event, message, sender_id)


@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event: events.NewMessage.Event):
    """Handle incoming messages from allowed users (non-owner) for /strco relay."""
    message: Message = event.message
    
    if not event.sender_id:
        return
    
    sender_id = event.sender_id
    
    owner_id = await ConfigStorage.get_owner_id()
    if sender_id == owner_id:
        return
    
    text = message.text or message.message or ""
    
    if not text.startswith(COMMAND_PREFIX):
        return
    
    await process_strco_command(event, message, sender_id)


@client.on(events.MessageEdited())
async def handle_message_edited(event: events.MessageEdited.Event):
    """Handle edited messages from tracked bots."""
    message: Message = event.message
    
    if message.out:
        return
    
    chat_id = event.chat_id
    if chat_id not in _tracked_bot_chats:
        return
    
    settings = await ConfigStorage.get_settings()
    debounce = settings.get("edit_debounce", 1.5)
    
    await handle_edit(client, message, chat_id, debounce)


async def periodic_cleanup():
    """Periodically clean up old mappings and stale requests."""
    while True:
        await asyncio.sleep(3600)
        try:
            settings = await ConfigStorage.get_settings()
            cleanup_hours = settings.get("cleanup_hours", 24)
            timeout = settings.get("timeout", 60)
            
            await MappingsStorage.cleanup_old(cleanup_hours)
            await RequestsStorage.cleanup_stale(timeout * 2)
            
            logger.info("Periodic cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def startup_cleanup():
    """Run cleanup on startup."""
    try:
        settings = await ConfigStorage.get_settings()
        cleanup_hours = settings.get("cleanup_hours", 24)
        timeout = settings.get("timeout", 60)
        
        await MappingsStorage.cleanup_old(cleanup_hours)
        await RequestsStorage.cleanup_stale(timeout * 2)
        
        logger.info("Startup cleanup completed")
    except Exception as e:
        logger.error(f"Startup cleanup error: {e}")


async def main():
    """Main entry point."""
    logger.info("Starting Telegram Relay Userbot...")
    
    await client.start()
    
    me = await client.get_me()
    logger.info(f"Logged in as: {me.first_name} (@{me.username}) [ID: {me.id}]")
    
    await startup_cleanup()
    
    asyncio.create_task(periodic_cleanup())
    
    logger.info("Userbot is running. Use /strcohelp for commands.")
    logger.info(f"Owner ID: {OWNER_ID}")
    
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Userbot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
