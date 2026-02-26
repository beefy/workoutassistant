#!/usr/bin/env python3
"""
Discord Bot Task
Task wrapper for the Discord bot to integrate with the main application task system.
"""

import asyncio
import os
from utils.discord_bot import run_discord_bot_async

def main():
    """Main function to run Discord bot task."""
    print("🤖 Starting Discord Bot Task...")
    username = os.getenv("TRACKING_API_USERNAME")
    if username != "bob":
        print("⚠️ Discord bot is only intended to run for user 'bob'. Skipping startup.")
        return
    
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the Discord bot
        loop.run_until_complete(run_discord_bot_async())
    except Exception as e:
        print(f"❌ Discord bot task error: {e}")
        raise e
    finally:
        loop.close()

if __name__ == "__main__":
    main()