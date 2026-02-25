# Discord Music Bot Setup Guide

## Prerequisites

1. **Install FFmpeg** (required for audio processing):
   ```bash
   brew install ffmpeg  # macOS
   # OR
   sudo apt install ffmpeg  # Ubuntu/Debian
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Discord Bot Setup

### 1. Create a Discord Application
1. Go to https://discord.com/developers/applications
2. Click "New Application" and give it a name
3. Go to the "Bot" tab
4. Click "Add Bot"
5. Copy the bot token (keep this secret!)

### 2. Bot Permissions
In the Discord Developer Portal:
1. Go to the "Bot" tab
2. Enable these Intents:
   - Message Content Intent
3. Go to the "OAuth2" > "URL Generator" tab
4. Select scopes: `bot`
5. Select bot permissions:
   - Send Messages
   - Read Messages
   - Connect (to voice channels)
   - Speak (in voice channels)
6. Copy the generated URL and use it to invite the bot to your server

### 3. Set Environment Variable
```bash
export DISCORD_BOT_TOKEN='your_bot_token_here'
```

Or create a `.env` file in the project root:
```
DISCORD_BOT_TOKEN=your_bot_token_here
```

## Running the Bot

```bash
cd /Users/nate/Code/workoutassistant
PYTHONPATH=src python src/scripts/discord_bot.py
```

## Usage

### Natural Language Commands
- `get audio Bohemian Rhapsody` - Downloads and plays the song
- `get audio Never Gonna Give You Up` - Rick roll anyone?
- `get audio Imagine Dragons Thunder` - Plays the specified song

### Bot Commands
- `!test` - Test if bot is responding
- `!stop` - Stops currently playing music
- `!leave` - Makes bot leave the voice channel
- `!help_music` - Shows help message

## How It Works

1. Bot listens for messages containing "get audio <text>"
2. Uses the existing YouTube downloader to search and download audio
3. Joins the user's voice channel
4. Plays the downloaded audio
5. Cleans up temporary files after playback

## Troubleshooting

### Bot Not Responding to Commands

1. **Check Console Output**
   - When you send a message, you should see it logged in the terminal
   - If no messages appear, the bot can't read messages in that channel

2. **Verify Bot Permissions**
   - Make sure the bot has these permissions in your server:
     - View Channels
     - Send Messages
     - Read Message History
     - Connect (for voice)
     - Speak (for voice)

3. **Check Message Content Intent**
   - In Discord Developer Portal → Bot tab
   - Enable "Message Content Intent" 
   - Restart the bot after enabling

4. **Test Basic Functionality**
   - Try `!test` command first
   - If this doesn't work, it's a permissions issue

5. **Bot Role Position**
   - In Discord server → Server Settings → Roles
   - Make sure the bot's role is not at the bottom
   - Move it above @everyone if needed

### "FFmpeg not found"
Install FFmpeg: `brew install ffmpeg`

### "You need to be in a voice channel"
Join a voice channel before requesting music.

### "Invalid bot token"
Check your `DISCORD_BOT_TOKEN` environment variable.

### Bot not responding to messages
Ensure "Message Content Intent" is enabled in the Discord Developer Portal.