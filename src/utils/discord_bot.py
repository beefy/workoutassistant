#!/usr/bin/env python3
"""
Discord Music Bot Utility
Provides Discord bot functionality that can be imported and used in different contexts.
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

# Import other utilities
from scripts.youtube_audio import search_and_download_music_video
from llm.priority_queue import LLMPriorityQueueManager
from clients.generate_image import HuggingFaceImageGenerator

class MusicBot:
    def __init__(self):
        self.voice_clients = {}
        self.temp_dir = tempfile.mkdtemp(prefix='discord_music_')
        self.llm_queue = LLMPriorityQueueManager()
        
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
            status_msg = await channel.send(f"🎵 Searching for: {query}")
            
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

    async def generate_and_send_image(self, channel, prompt):
        """Generate an image using AI and send it to the channel."""
        try:
            status_msg = await channel.send(f"🎨 Generating image: {prompt}")
            
            # Generate image
            image_client = HuggingFaceImageGenerator()
            result = image_client.generate_and_save(prompt)
            
            if result and os.path.exists(result):
                await status_msg.edit(content=f"🖼️ Generated image for: {prompt}")
                
                # Send the image file
                with open(result, 'rb') as f:
                    file = discord.File(f, filename=f"generated_{prompt[:30]}.png")
                    await channel.send(file=file)
                
                # Clean up the image file
                try:
                    os.remove(result)
                except Exception as e:
                    print(f"Error cleaning up image file {result}: {e}")
            else:
                await status_msg.edit(content="❌ Failed to generate image.")
                
        except Exception as e:
            await channel.send(f"❌ Error generating image: {str(e)}")
            print(f"Error in generate_and_send_image: {e}")

def create_discord_bot():
    """Create and configure the Discord bot."""
    # Bot setup
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    # Create the music bot instance
    music_bot = MusicBot()
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        print(f'Bot is ready to receive commands.')
        print(f'Bot ID: {bot.user.id}')
        print(f'Guilds: {[guild.name for guild in bot.guilds]}')
    
    @bot.event
    async def on_message(message):
        # Don't respond to the bot's own messages
        if message.author == bot.user:
            return
        
        # Debug: Print all messages to console
        print(f"Message received: '{message.content}' from {message.author} in #{message.channel}")
        
        # Process other commands
        await bot.process_commands(message)
    
    @bot.command(name='test')
    async def test_command(ctx):
        """Test if bot is responding to commands."""
        await ctx.send("🤖 Bot is working! I can see and respond to messages.")
    
    @bot.command(name='groovy')
    async def groovy_command(ctx, *, query):
        """Download and play audio from YouTube."""
        # Check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Download and play the audio
        await music_bot.download_and_play(ctx.channel, query, voice_channel)
    
    @bot.command(name='llm')
    async def llm_command(ctx, *, prompt):
        """Send a prompt to the LLM via priority queue."""
        try:
            await ctx.send(f"🧠 Adding to LLM queue: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Run the blocking LLM request in a separate thread to avoid blocking the Discord event loop
            loop = asyncio.get_event_loop()
            
            def submit_llm_request():
                """Submit request in separate thread"""
                try:
                    return music_bot.llm_queue.submit_request(prompt, priority=3)
                except Exception as e:
                    print(f"Error submitting LLM request: {e}")
                    return None
            
            # Run in executor with timeout to avoid blocking the event loop
            try:
                future = await asyncio.wait_for(
                    loop.run_in_executor(None, submit_llm_request),
                    timeout=180.0  # 180 second timeout
                )
                
                # Get the response
                if future:
                    response = future.result() if hasattr(future, 'result') else str(future)
                    if response:
                        # Split long responses into chunks
                        max_length = 1900
                        if len(response) <= max_length:
                            await ctx.send(f"💭 {response}")
                        else:
                            # Send in chunks
                            chunks = [response[i:i+max_length] for i in range(0, len(response), max_length)]
                            for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
                                await ctx.send(f"💭 ({i+1}/{len(chunks)}) {chunk}")
                            if len(chunks) > 3:
                                await ctx.send("💭 Response truncated (too long)")
                    else:
                        await ctx.send("🤔 LLM returned empty response")
                else:
                    await ctx.send("🤔 LLM request failed")
            except asyncio.TimeoutError:
                await ctx.send("⏱️ LLM request timed out after 180 seconds. The request may still be processing in the background.")
                
        except Exception as e:
            await ctx.send(f"❌ Error with LLM request: {str(e)}")
            print(f"Error in llm_command: {e}")
    
    @bot.command(name='image')
    async def image_command(ctx, *, prompt):
        """Generate an AI image based on the prompt."""
        await music_bot.generate_and_send_image(ctx.channel, prompt)
    
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
🤖 **Bot Commands:**

**Music & Audio:**
• `!groovy <song name>` - Search and play audio from YouTube
• `!stop` - Stop the currently playing music
• `!leave` - Make the bot leave the voice channel

**AI Features:**
• `!llm <prompt>` - Send a prompt to the LLM
• `!image <description>` - Generate an AI image

**Utility:**
• `!test` - Test if bot is responding
• `!help_music` - Show this help message

**Examples:**
• `!groovy Bohemian Rhapsody`
• `!llm What is the meaning of life?`
• `!image a cute cat wearing sunglasses`
        """
        await ctx.send(help_text)
    
    return bot, music_bot

def run_discord_bot():
    """Run the Discord bot (for standalone usage)."""
    # Check for bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        print("Please set your Discord bot token:")
        print("export DISCORD_BOT_TOKEN='your_bot_token_here'")
        return None
    
    # Check for FFmpeg
    if shutil.which('ffmpeg') is None:
        print("Warning: FFmpeg not found. Please install FFmpeg for audio processing:")
        print("brew install ffmpeg  # macOS")
        print("sudo apt install ffmpeg  # Ubuntu/Debian")
    
    bot, music_bot = create_discord_bot()
    
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

async def run_discord_bot_async():
    """Run the Discord bot asynchronously (for thread usage)."""
    # Check for bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        return
    
    bot, music_bot = create_discord_bot()
    
    try:
        await bot.start(token)
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