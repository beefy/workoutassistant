#!/usr/bin/env python3
"""
Discord Bot Setup Test
Tests if all dependencies and requirements are met for the Discord music bot.
"""

import sys
import os
import subprocess
import shutil

def check_python_packages():
    """Check if required Python packages are installed."""
    required_packages = ['discord', 'yt_dlp']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            missing_packages.append(package)
    
    return missing_packages

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    if shutil.which('ffmpeg'):
        print("✅ FFmpeg is installed")
        return True
    else:
        print("❌ FFmpeg is NOT installed")
        return False

def check_environment():
    """Check if environment variables are set."""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if token:
        print("✅ DISCORD_BOT_TOKEN is set")
        return True
    else:
        print("❌ DISCORD_BOT_TOKEN environment variable is NOT set")
        return False

def test_youtube_download():
    """Test if YouTube downloading works."""
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from scripts.youtube_audio import search_and_download_music_video
        
        print("✅ YouTube audio module can be imported")
        return True
    except Exception as e:
        print(f"❌ YouTube audio module import failed: {e}")
        return False

def main():
    """Run all setup tests."""
    print("🔍 Discord Music Bot Setup Test")
    print("=" * 40)
    
    # Check Python packages
    print("\n📦 Checking Python packages:")
    missing_packages = check_python_packages()
    
    # Check FFmpeg
    print("\n🎵 Checking FFmpeg:")
    ffmpeg_ok = check_ffmpeg()
    
    # Check environment
    print("\n🔐 Checking environment:")
    env_ok = check_environment()
    
    # Test YouTube module
    print("\n📺 Testing YouTube module:")
    youtube_ok = test_youtube_download()
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 SETUP SUMMARY:")
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install discord.py yt-dlp PyNaCl")
    
    if not ffmpeg_ok:
        print("❌ FFmpeg not found")
        print("   Install with: brew install ffmpeg  # macOS")
        print("                sudo apt install ffmpeg  # Ubuntu/Debian")
    
    if not env_ok:
        print("❌ Bot token not set")
        print("   Set with: export DISCORD_BOT_TOKEN='your_token_here'")
    
    if not youtube_ok:
        print("❌ YouTube module not working")
        print("   Check if yt-dlp is properly installed")
    
    all_ok = not missing_packages and ffmpeg_ok and env_ok and youtube_ok
    
    if all_ok:
        print("🎉 ALL CHECKS PASSED! Bot is ready to run.")
        print("\nStart the bot with:")
        print("PYTHONPATH=src python src/scripts/discord_bot.py")
    else:
        print("⚠️  Some issues need to be resolved before running the bot.")
    
    print("\nSee DISCORD_BOT_README.md for detailed setup instructions.")

if __name__ == "__main__":
    main()