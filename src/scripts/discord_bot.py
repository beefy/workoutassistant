#!/usr/bin/env python3
"""
Discord Music Bot Script
Standalone script to run the Discord bot.
"""

import os
import sys

# Add the src directory to the path to import utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.discord_bot import run_discord_bot

def main():
    """Main function to run the Discord bot."""
    print("🤖 Starting Discord Bot...")
    run_discord_bot()

if __name__ == "__main__":
    main()