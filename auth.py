"""
One-time authentication script to generate a session string.
Run this once to get your SESSION_SECRET, then add it to secrets.
"""
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

if not API_ID or not API_HASH:
    print("ERROR: API_ID and API_HASH must be set in environment variables")
    exit(1)

async def main():
    print("=" * 50)
    print("Telegram Session Generator")
    print("=" * 50)
    print("\nThis will authenticate you with Telegram and generate a session string.")
    print("You only need to do this once.\n")
    
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    await client.start()
    
    session_string = client.session.save()
    
    me = await client.get_me()
    print(f"\nLogged in as: {me.first_name} (@{me.username}) [ID: {me.id}]")
    print("\n" + "=" * 50)
    print("SESSION STRING (add this as SESSION_SECRET):")
    print("=" * 50)
    print(f"\n{session_string}\n")
    print("=" * 50)
    print("\nCopy the session string above and add it as SESSION_SECRET in your secrets.")
    print("Then the userbot will start automatically without requiring login.\n")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
