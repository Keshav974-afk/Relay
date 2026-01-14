"""
Relay logic for message forwarding, response collection, and edit mirroring.
"""
import asyncio
import time
import hashlib
import logging
from typing import Optional, List
from telethon import TelegramClient
from telethon.tl.types import (
    Message, MessageMediaPhoto, MessageMediaDocument,
    DocumentAttributeVideo, DocumentAttributeAudio
)
from telethon.errors import FloodWaitError, RPCError

from storage import ConfigStorage, MappingsStorage, RequestsStorage

logger = logging.getLogger(__name__)

_edit_debounce: dict = {}


def get_content_hash(message: Message) -> str:
    """Generate hash of message content for change detection."""
    content = ""
    if message.text:
        content = message.text
    if message.message:
        content += message.message
    if message.media:
        content += str(type(message.media).__name__)
    return hashlib.md5(content.encode()).hexdigest()[:16]


def is_media_message(message: Message) -> bool:
    """Check if message contains media."""
    return message.media is not None


def get_media_type(message: Message) -> str:
    """Determine the type of media in message."""
    if not message.media:
        return "text"
    if isinstance(message.media, MessageMediaPhoto):
        return "photo"
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if doc:
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeVideo):
                    return "video"
                if isinstance(attr, DocumentAttributeAudio):
                    if getattr(attr, 'voice', False):
                        return "voice"
                    return "audio"
            return "document"
    return "media"


async def relay_message(client: TelegramClient, origin_message: Message, 
                        target_bot: str) -> Optional[Message]:
    """
    Relay a message to the target bot.
    Returns the sent message or None on failure.
    """
    try:
        bot_entity = await client.get_entity(target_bot)
        
        if is_media_message(origin_message):
            sent = await client.send_file(
                bot_entity,
                origin_message.media,
                caption=origin_message.message or ""
            )
        else:
            sent = await client.send_message(
                bot_entity,
                origin_message.text or origin_message.message
            )
        
        logger.info(f"Relayed message to {target_bot}, msg_id: {sent.id}")
        return sent
        
    except FloodWaitError as e:
        logger.warning(f"FloodWait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return await relay_message(client, origin_message, target_bot)
    except RPCError as e:
        logger.error(f"RPC error relaying message: {e}")
        return None
    except Exception as e:
        logger.error(f"Error relaying message: {e}")
        return None


async def collect_bot_replies(client: TelegramClient, bot_entity, 
                              sent_msg_id: int, settings: dict) -> List[Message]:
    """
    Collect bot replies using idle-window logic.
    Waits for replies after sent_msg_id until idle timeout or hard timeout.
    """
    timeout = settings.get("timeout", 60)
    idle_timeout = settings.get("reply_idle", 2)
    
    start_time = time.time()
    replies: List[Message] = []
    last_reply_time = None
    first_reply_received = False
    
    logger.info(f"Collecting replies for msg {sent_msg_id}, timeout={timeout}s, idle={idle_timeout}s")
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed >= timeout:
            logger.info("Hard timeout reached")
            break
        
        if first_reply_received and last_reply_time:
            idle_elapsed = time.time() - last_reply_time
            if idle_elapsed >= idle_timeout:
                logger.info("Idle timeout reached, collection complete")
                break
        
        try:
            messages = await client.get_messages(bot_entity, limit=10)
            
            for msg in messages:
                if msg.id <= sent_msg_id:
                    continue
                if msg.out:
                    continue
                if any(r.id == msg.id for r in replies):
                    continue
                
                replies.append(msg)
                last_reply_time = time.time()
                first_reply_received = True
                logger.info(f"Collected reply msg_id: {msg.id}")
            
            await asyncio.sleep(0.3)
            
        except FloodWaitError as e:
            logger.warning(f"FloodWait during collection: {e.seconds}s")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Error collecting replies: {e}")
            await asyncio.sleep(0.5)
    
    replies.sort(key=lambda m: m.id)
    return replies


async def mirror_message(client: TelegramClient, origin_chat_id: int,
                         bot_message: Message, bot_chat_id: int, origin_entity=None) -> Optional[int]:
    """
    Mirror a bot's reply message to the origin chat.
    Returns the mirrored message ID.
    """
    try:
        if origin_entity is None:
            try:
                origin_entity = await client.get_entity(origin_chat_id)
            except Exception:
                origin_entity = await client.get_input_entity(origin_chat_id)
        
        if is_media_message(bot_message):
            mirrored = await client.send_file(
                origin_entity,
                bot_message.media,
                caption=bot_message.message or ""
            )
            msg_type = get_media_type(bot_message)
        else:
            mirrored = await client.send_message(
                origin_entity,
                bot_message.text or bot_message.message
            )
            msg_type = "text"
        
        content_hash = get_content_hash(bot_message)
        await MappingsStorage.add_mapping(
            bot_chat_id=bot_chat_id,
            bot_msg_id=bot_message.id,
            origin_chat_id=origin_chat_id,
            mirrored_msg_id=mirrored.id,
            msg_type=msg_type,
            content_hash=content_hash
        )
        
        logger.info(f"Mirrored msg {bot_message.id} -> {mirrored.id} in chat {origin_chat_id}")
        return mirrored.id
        
    except FloodWaitError as e:
        logger.warning(f"FloodWait mirroring: {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return await mirror_message(client, origin_chat_id, bot_message, bot_chat_id)
    except Exception as e:
        logger.error(f"Error mirroring message: {e}")
        return None


async def handle_edit(client: TelegramClient, edited_message: Message, 
                      bot_chat_id: int, debounce_seconds: float):
    """
    Handle a bot's message edit by updating the mirrored message.
    Includes debouncing to avoid rate limits.
    """
    global _edit_debounce
    
    debounce_key = f"{bot_chat_id}_{edited_message.id}"
    now = time.time()
    
    if debounce_key in _edit_debounce:
        if now - _edit_debounce[debounce_key] < debounce_seconds:
            logger.debug(f"Debouncing edit for {debounce_key}")
            return
    
    _edit_debounce[debounce_key] = now
    
    mapping = await MappingsStorage.get_mapping(bot_chat_id, edited_message.id)
    if not mapping:
        logger.debug(f"No mapping found for edit: {bot_chat_id}/{edited_message.id}")
        return
    
    new_hash = get_content_hash(edited_message)
    if new_hash == mapping.get("last_hash"):
        logger.debug("Content unchanged, skipping edit")
        return
    
    try:
        origin_chat_id = mapping["origin_chat_id"]
        mirrored_msg_id = mapping["mirrored_msg_id"]
        
        try:
            origin_entity = await client.get_entity(origin_chat_id)
        except Exception:
            origin_entity = await client.get_input_entity(origin_chat_id)
        
        if is_media_message(edited_message):
            if mapping.get("type") in ["photo", "video", "document", "voice", "audio"]:
                await client.edit_message(
                    origin_entity,
                    mirrored_msg_id,
                    text=edited_message.message or ""
                )
            else:
                new_mirrored = await client.send_file(
                    origin_entity,
                    edited_message.media,
                    caption=f"(updated media)\n{edited_message.message or ''}"
                )
                await MappingsStorage.update_mapping(
                    bot_chat_id=bot_chat_id,
                    bot_msg_id=edited_message.id,
                    new_mirrored_msg_id=new_mirrored.id,
                    new_hash=new_hash,
                    new_type=get_media_type(edited_message)
                )
        else:
            await client.edit_message(
                origin_entity,
                mirrored_msg_id,
                text=edited_message.text or edited_message.message
            )
        
        await MappingsStorage.update_hash(bot_chat_id, edited_message.id, new_hash)
        logger.info(f"Edited mirrored message {mirrored_msg_id}")
        
    except FloodWaitError as e:
        logger.warning(f"FloodWait on edit: {e.seconds}s")
        await asyncio.sleep(e.seconds)
        await handle_edit(client, edited_message, bot_chat_id, debounce_seconds)
    except Exception as e:
        logger.error(f"Error handling edit: {e}")


async def process_relay_request(client: TelegramClient, origin_message: Message,
                                origin_chat_id: int, origin_entity=None) -> bool:
    """
    Full relay workflow:
    1. Get target bot
    2. Relay message
    3. Collect replies
    4. Mirror replies to origin
    """
    if origin_entity is None:
        try:
            origin_entity = await client.get_entity(origin_chat_id)
        except Exception:
            try:
                origin_entity = await client.get_input_entity(origin_chat_id)
            except Exception:
                origin_entity = origin_chat_id
    
    target_bot = await ConfigStorage.get_chat_bot(origin_chat_id)
    if not target_bot:
        await client.send_message(
            origin_entity,
            "No target bot configured. Use /setstrco @BotUsername or /setstrcoglobal @BotUsername"
        )
        return False
    
    settings = await ConfigStorage.get_settings()
    
    sent = await relay_message(client, origin_message, target_bot)
    if not sent:
        await client.send_message(origin_entity, "Failed to relay message to bot.")
        return False
    
    try:
        bot_entity = await client.get_entity(target_bot)
        bot_chat_id = bot_entity.id
    except Exception as e:
        logger.error(f"Could not get bot entity: {e}")
        return False
    
    import uuid
    request_id = str(uuid.uuid4())[:8]
    await RequestsStorage.add_request(
        origin_chat_id=origin_chat_id,
        bot_chat_id=bot_chat_id,
        sent_to_bot_msg_id=sent.id,
        request_id=request_id
    )
    
    replies = await collect_bot_replies(client, bot_entity, sent.id, settings)
    
    if not replies:
        await client.send_message(origin_entity, "No response from bot (timeout).")
    else:
        for reply in replies:
            await mirror_message(client, origin_chat_id, reply, bot_chat_id, origin_entity)
    
    await RequestsStorage.remove_request(origin_chat_id)
    return True
