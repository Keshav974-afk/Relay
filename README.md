# Telegram Relay Userbot

A Telegram userbot built with Telethon that relays messages starting with `/strco` to a configured target bot, mirrors all replies, and synchronizes edits.

## Features

- Relay messages (text and media) to any Telegram bot
- Mirror all bot replies back to the origin chat
- Sync bot message edits in real-time with debouncing
- Per-chat and global bot configuration
- Access control system (owner + allowed users)
- JSON-based storage with atomic writes (no SQLite)
- Automatic cleanup of old message mappings

## Prerequisites

1. **Telegram API Credentials**: Get your `API_ID` and `API_HASH` from https://my.telegram.org
2. **Your Telegram User ID**: Use @userinfobot or similar to get your user ID

## Setup

### 1. Configure Environment Variables

Set the following secrets/environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | Yes | Your Telegram API ID |
| `API_HASH` | Yes | Your Telegram API Hash |
| `OWNER_ID` | Yes | Your Telegram user ID |
| `SESSION_SECRET` | Yes | Session string from auth.py (see below) |
| `TIMEOUT_SECONDS` | No | Max wait for bot reply (default: 60) |
| `REPLY_IDLE_SECONDS` | No | Idle window for reply collection (default: 2) |
| `EDIT_DEBOUNCE_SECONDS` | No | Debounce time for edits (default: 1.5) |
| `CLEANUP_HOURS` | No | Hours to keep mappings (default: 24) |

### 2. Generate Session String (One-Time Setup)

Run the authentication script in the Shell to generate your session string:

```bash
python auth.py
```

This will:
1. Ask for your phone number (with country code, e.g., +1234567890)
2. Send a verification code to your Telegram
3. Ask for 2FA password (if enabled)
4. Output a session string

Copy the session string and add it as `SESSION_SECRET` in your secrets.

### 3. Run the Userbot

Once `SESSION_SECRET` is set, the userbot will start automatically:

```bash
python main.py
```

## Commands

### Relay Command
- `/strco <message>` - Relay message to target bot (text or media with caption)

### Bot Configuration
- `/setstrco @BotUsername` - Set target bot for current chat
- `/setstrcoglobal @BotUsername` - Set global default bot
- `/strcobot` - Show current target bot

### Access Control (Owner Only)
- `/allow <user_id>` - Allow a user to use /strco
- `/disallow <user_id>` - Revoke user access
- `/allowed` - List all allowed users

### Help
- `/strcohelp` - Show command help

## Usage Example

1. Set a global target bot:
   ```
   /setstrcoglobal @ChatGPTBot
   ```

2. Send a message to the bot:
   ```
   /strco Hello, how are you?
   ```

3. The userbot will:
   - Forward your message to @ChatGPTBot
   - Mirror all bot replies back to your chat
   - Keep mirrored messages in sync if the bot edits

## Data Storage

All data is stored in the `data/` folder as JSON files:

- `config.json` - Bot settings, allowed users
- `mappings.json` - Message mappings for edit sync
- `requests.json` - Active relay requests

## Security Notes

- Only the owner and allowed users can use `/strco`
- Session file contains your login - keep it secure
- This is for personal automation only
- Do not use for spam or abuse

## Project Structure

```
├── main.py        # Entry point, event handlers
├── config.py      # Configuration and environment
├── storage.py     # JSON database layer
├── relay.py       # Relay and mirroring logic
├── auth.py        # One-time session generator
├── data/          # JSON storage files
│   ├── config.json
│   ├── mappings.json
│   └── requests.json
└── README.md
```

## Troubleshooting

**"API_ID and API_HASH must be set"**
- Ensure environment variables are configured correctly

**"No target bot configured"**
- Use `/setstrco @BotUsername` or `/setstrcoglobal @BotUsername`

**"Not allowed"**
- Only the owner (OWNER_ID) can configure bots and access control
- Use `/allow <user_id>` to grant access to other users

**Bot not responding**
- Check if the target bot is online and responding
- Increase TIMEOUT_SECONDS if needed
