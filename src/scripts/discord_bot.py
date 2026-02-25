#!/usr/bin/env python3
"""
Discord Music Bot
Listens for "get audio <text>" messages and plays YouTube audio in voice channels.
"""

import asyncio
import os
import sys
import re
import discord
from discord.ext import commands
from pathlib import Path
import tempfile
import shutil

# Add the src directory to the path to import youtube_audio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.youtube_audio import search_and_download_music_video

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class MusicBot:
    def __init__(self):
        self.voice_clients = {}
        self.temp_dir = tempfile.mkdtemp(prefix='discord_music_')
        
    async def join_voice_channel(self, channel):
        """Join a voice channel and return the voice client."""
        if channel.guild.id in self.voice_clients:
            voice_client = self.voice_clients[channel.guild.id]
            if voice_client.channel != channel:
                await voice_client.move_to(channel)
        else:
            voice_client = await channel.connect()
            self.voice_clients[channel.guild.id] = voice_client
        return voice_client
    
    async def download_and_play(self, channel, query, voice_channel):
        """Download audio from YouTube and play it in the voice channel."""
        try:
            # Send status message
            status_msg = await channel.send(f"🔍 Searching for: {query}")
            
            # Create a temporary directory for this download
            download_path = os.path.join(self.temp_dir, f"download_{channel.guild.id}")
            
            # Download the audio
            audio_file = search_and_download_music_video(query, download_path)
            
            if not audio_file:
                await status_msg.edit(content="❌ Could not find or download the audio.")
                return
            
            await status_msg.edit(content=f"⬇️ Downloaded! Joining voice channel...")
            
            # Join voice channel
            voice_client = await self.join_voice_channel(voice_channel)
            
            # Stop any currently playing audio
            if voice_client.is_playing():
                voice_client.stop()
            
            await status_msg.edit(content=f"🎵 Now playing: {os.path.basename(audio_file)}")
            
            # Play the audio
            audio_source = discord.FFmpegPCMAudio(audio_file)
            voice_client.play(audio_source)
            
            # Wait for playback to finish, then clean up
            while voice_client.is_playing():
                await asyncio.sleep(1)
                
            # Clean up the downloaded file
            try:
                os.remove(audio_file)
                # Remove download directory if empty
                if os.path.exists(download_path) and not os.listdir(download_path):
                    os.rmdir(download_path)
            except Exception as e:
                print(f"Error cleaning up file {audio_file}: {e}")
                
        except Exception as e:
            await channel.send(f"❌ Error: {str(e)}")
            print(f"Error in download_and_play: {e}")

# Create the music bot instance
music_bot = MusicBot()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready to receive "get audio <text>" commands.')
    print(f'Bot ID: {bot.user.id}')
    print(f'Guilds: {[guild.name for guild in bot.guilds]}')

@bot.event
async def on_message(message):
    # Don't respond to the bot's own messages
    if message.author == bot.user:
        return
    
    # Debug: Print all messages to console
    print(f"Message received: '{message.content}' from {message.author} in #{message.channel}")
    
    # Check for "get audio <text>" pattern (case insensitive)
    pattern = r'get audio (.+)'
    match = re.search(pattern, message.content, re.IGNORECASE)
    
    if match:
        query = match.group(1).strip()
        
        # Check if user is in a voice channel
        if message.author.voice is None:
            await message.channel.send("❌ You need to be in a voice channel to use this command!")
            return
            
        voice_channel = message.author.voice.channel
        
        # Download and play the audio
        await music_bot.download_and_play(message.channel, query, voice_channel)
    
    # Process other commands
    await bot.process_commands(message)

@bot.command(name='test')
async def test_command(ctx):
    """Test if bot is responding to commands."""
    await ctx.send("🤖 Bot is working! I can see and respond to messages.")

@bot.command(name='stop')
async def stop_music(ctx):
    """Stop the currently playing music."""
    guild_id = ctx.guild.id
    if guild_id in music_bot.voice_clients:
        voice_client = music_bot.voice_clients[guild_id]
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.send("⏹️ Music stopped.")
        else:
            await ctx.send("No music is currently playing.")
    else:
        await ctx.send("Bot is not connected to a voice channel.")

@bot.command(name='leave')
async def leave_voice(ctx):
    """Make the bot leave the voice channel."""
    guild_id = ctx.guild.id
    if guild_id in music_bot.voice_clients:
        voice_client = music_bot.voice_clients[guild_id]
        await voice_client.disconnect()
        del music_bot.voice_clients[guild_id]
        await ctx.send("👋 Left the voice channel.")
    else:
        await ctx.send("Bot is not connected to a voice channel.")

@bot.command(name='help_music')
async def help_music(ctx):
    """Show help for music commands."""
    help_text = """
    🎵 **Music Bot Commands:**
    
    **Natural Language:**
    • `get audio <song name>` - Search and play audio from YouTube
    
    **Commands:**
    • `!stop` - Stop the currently playing music
    • `!leave` - Make the bot leave the voice channel
    • `!help_music` - Show this help message
    
    **Examples:**
    • `get audio Bohemian Rhapsody`
    • `get audio Never Gonna Give You Up`
    • `get audio Imagine Dragons Thunder`
    """
    await ctx.send(help_text)

def main():
    """Main function to run the Discord bot."""
    # Check for bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        print("Please set your Discord bot token:")
        print("export DISCORD_BOT_TOKEN='your_bot_token_here'")
        sys.exit(1)
    
    # Check for FFmpeg
    if shutil.which('ffmpeg') is None:
        print("Warning: FFmpeg not found. Please install FFmpeg for audio processing:")
        print("brew install ffmpeg  # macOS")
        print("sudo apt install ffmpeg  # Ubuntu/Debian")
        
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("Error: Invalid bot token. Please check your DISCORD_BOT_TOKEN.")
    except Exception as e:
        print(f"Error starting bot: {e}")
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(music_bot.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp directory: {e}")

if __name__ == "__main__":
    main()