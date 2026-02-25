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

### Option 1: With Main Application (Recommended)
```bash
cd /Users/nate/Code/workoutassistant
PYTHONPATH=src python src/main.py
```
This runs the Discord bot alongside all other application threads.

### Option 2: Standalone Bot Only
```bash
cd /Users/nate/Code/workoutassistant
PYTHONPATH=src python src/scripts/discord_bot.py
```
This runs only the Discord bot.

## Usage

### Music Commands
- `!groovy Bohemian Rhapsody` - Downloads and plays the song
- `!groovy Never Gonna Give You Up` - Rick roll anyone?
- `!groovy <any song name>` - Plays the specified song
- `!say Hello everyone!` - Speaks text using text-to-speech

### AI Commands  
- `!bob What is the meaning of life?` - Send prompt to LLM
- `!image a cute cat wearing sunglasses` - Generate AI image
- `!image futuristic cityscape at sunset` - Create custom artwork

### Bot Commands
- `!test` - Test if bot is responding
- `!stop` - Stops currently playing music
- `!leave` - Makes bot leave the voice channel
- `!help_bob` - Shows help message

## How It Works

### Music Functionality
1. **Music Playback**: User types `!groovy <song name>` in Discord
2. Bot searches YouTube using the existing YouTube downloader
3. Downloads the audio file
4. Joins the user's voice channel
5. Plays the audio
6. Automatically cleans up temporary files

### Text-to-Speech
1. **TTS**: User types `!say <text>` in Discord
2. Bot generates speech using Microsoft Edge TTS
3. Joins the user's voice channel
4. Plays the generated speech audio
5. Automatically cleans up temporary files

### AI Features
1. **LLM Integration**: `!bob <prompt>` adds requests to the priority queue system
2. **Image Generation**: `!image <description>` uses HuggingFace to generate and send images

### Integration
- Can run standalone or as part of the main application
- Integrates with existing LLM priority queue
- Uses existing image generation clients
- Auto-restart functionality when run with main.py

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
   - Try `!groovy bohemian rhapsody` for music
   - Try `!say hello world` for text-to-speech
   - Try `!bob hello` for LLM integration
   - Try `!image cute cat` for image generation
   - If these don't work, it's a permissions issue

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