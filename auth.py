"""
One-time authentication script to generate a session string.
Run this once to get your SESSION_SECRET, then update config.py.
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 25458518
API_HASH = "e0a73353c37306f9fa68b1e2a4ba6eab"

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
    print("SESSION STRING (update this in config.py):")
    print("=" * 50)
    print(f"\n{session_string}\n")
    print("=" * 50)
    print("\nCopy the session string above and update SESSION_SECRET in config.py.")
    print("Then the userbot will start automatically without requiring login.\n")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
