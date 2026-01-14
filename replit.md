# Telegram Relay Userbot

## Overview
A Telegram userbot built with Telethon that relays messages starting with `/strco` to a configured target bot, mirrors all replies, and synchronizes edits in real-time.

## Recent Changes
- **2026-01-14**: Initial project setup with complete relay functionality

## Project Architecture

### Core Files
- `main.py` - Entry point, Telethon event handlers for commands and message processing
- `config.py` - Configuration loading from environment variables
- `storage.py` - JSON-based storage layer with atomic writes and asyncio locking
- `relay.py` - Message relay logic, response collection, and edit mirroring

### Data Storage
All data stored in `data/` folder as JSON files:
- `config.json` - Bot configuration, allowed users, settings
- `mappings.json` - Message mappings for edit synchronization
- `requests.json` - Active relay request tracking

### Key Features
1. **Relay**: Forward `/strco` messages to target bots
2. **Mirror**: Mirror all bot replies back to origin chat
3. **Edit Sync**: Track and sync bot message edits with debouncing
4. **Access Control**: Owner + allowed users system
5. **Per-Chat Bots**: Configure different target bots per chat

## Required Secrets
- `API_ID` - Telegram API ID from https://my.telegram.org
- `API_HASH` - Telegram API Hash
- `OWNER_ID` - Your Telegram user ID

## Commands
- `/strco <msg>` - Relay message to target bot
- `/setstrco @Bot` - Set bot for current chat
- `/setstrcoglobal @Bot` - Set global default bot
- `/strcobot` - Show current target bot
- `/allow <id>` - Allow user (owner only)
- `/disallow <id>` - Revoke access (owner only)
- `/allowed` - List allowed users
- `/strcohelp` - Show help

## Technical Notes
- Uses Telethon MTProto API (user session, not bot token)
- JSON storage with atomic writes (temp file + rename)
- Asyncio locks for concurrent access safety
- Idle-window logic for collecting multiple bot replies
- Edit debouncing to prevent rate limits
