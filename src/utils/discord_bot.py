#!/usr/bin/env python3
"""
Discord Music Bot Utility
Provides Discord bot functionality that can be imported and used in different contexts.
"""

import asyncio
import os
import sys
import re
import math
import subprocess
import discord
from discord.ext import commands
from pathlib import Path
import tempfile
import shutil
import edge_tts
import logging
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Import other utilities
from scripts.youtube_audio import search_and_download_music_video, download_youtube_audio, download_youtube_video
from llm.priority_queue import LLMPriorityQueueManager
from clients.generate_image import HuggingFaceImageGenerator
from utils.voices import generate_voice_tts_file, get_voice_emoji, get_voice_display_name
from utils.convo import generate_convo, convo_to_audio, splice_audio_together
from clients.raspi_cluster_api import health_check_all_hosts, get_all_agents, get_healthy_hosts

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
                logger.error(f"Error cleaning up file {audio_file}: {e}")
                
        except Exception as e:
            await channel.send(f"❌ Error: {str(e)}")
            logger.error(f"Error in download_and_play: {e}")

    async def download_and_play_youtube_url(self, channel, video_url, voice_channel):
        """Download audio from a YouTube URL and play it in the voice channel."""
        try:
            # Send status message
            status_msg = await channel.send(f"🎬 Downloading from YouTube URL...")
            
            # Create a temporary directory for this download
            download_path = os.path.join(self.temp_dir, f"youtube_{channel.guild.id}")
            
            # Download the audio
            audio_file = download_youtube_audio(video_url, download_path)
            
            if not audio_file:
                await status_msg.edit(content="❌ Could not download the YouTube audio.")
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
                logger.error(f"Error cleaning up file {audio_file}: {e}")
                
        except Exception as e:
            await channel.send(f"❌ Error: {str(e)}")
            logger.error(f"Error in download_and_play_youtube_url: {e}")

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
                    logger.error(f"Error cleaning up image file {result}: {e}")
            else:
                await status_msg.edit(content="❌ Failed to generate image.")
                
        except Exception as e:
            await channel.send(f"❌ Error generating image: {str(e)}")
            logger.error(f"Error in generate_and_send_image: {e}")

    async def generate_tts_and_play(self, channel, text, voice_channel, voice="en-US-AriaNeural"):
        """Generate TTS audio and play it in the voice channel."""
        try:
            # Send status message
            status_msg = await channel.send(f"🔊 Generating TTS: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            # Create a temporary directory for this TTS
            download_path = os.path.join(self.temp_dir, f"tts_{channel.guild.id}")
            Path(download_path).mkdir(exist_ok=True)
            
            # Generate TTS audio file
            tts_file = os.path.join(download_path, f"tts_{channel.guild.id}.mp3")
            
            # Run TTS generation in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def generate_tts():
                """Generate TTS in separate thread"""
                try:
                    # Create TTS communication
                    communicate = edge_tts.Communicate(text, voice)
                    
                    # Use asyncio.run in thread since communicate.save is async
                    async def save_tts():
                        await communicate.save(tts_file)
                    
                    # Create new event loop for this thread
                    thread_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(thread_loop)
                    thread_loop.run_until_complete(save_tts())
                    thread_loop.close()
                    
                    return tts_file if os.path.exists(tts_file) else None
                except Exception as e:
                    logger.error(f"Error generating TTS: {e}")
                    return None
            
            # Generate TTS with timeout
            audio_file = await asyncio.wait_for(
                loop.run_in_executor(None, generate_tts),
                timeout=30.0  # 30 second timeout
            )
            
            if not audio_file or not os.path.exists(audio_file):
                await status_msg.edit(content="❌ Could not generate TTS audio.")
                return
            
            await status_msg.edit(content=f"🔊 Generated! Joining voice channel...")
            
            # Join voice channel
            voice_client = await self.join_voice_channel(voice_channel)
            
            # Stop any currently playing audio
            if voice_client.is_playing():
                voice_client.stop()
            
            await status_msg.edit(content=f"🗣️ Speaking: {text[:30]}{'...' if len(text) > 30 else ''}")
            
            # Play the TTS audio
            audio_source = discord.FFmpegPCMAudio(audio_file)
            voice_client.play(audio_source)
            
            # Wait for playback to finish, then clean up
            while voice_client.is_playing():
                await asyncio.sleep(1)
                
            # Clean up the TTS file
            try:
                os.remove(audio_file)
                # Remove download directory if empty
                if os.path.exists(download_path) and not os.listdir(download_path):
                    os.rmdir(download_path)
            except Exception as e:
                    logger.error(f"Error cleaning up TTS file {audio_file}: {e}")
            await status_msg.edit(content="✅ Finished speaking.")
                
        except asyncio.TimeoutError:
            await channel.send("⏱️ TTS generation timed out.")
        except Exception as e:
            await channel.send(f"❌ TTS Error: {str(e)}")
            logger.error(f"Error in generate_tts_and_play: {e}")

    async def generate_voice_tts_and_play(self, channel, text, voice_channel, voice_name):
        """Generate voice TTS audio using Minimax API and play it in the voice channel."""
        try:
            emoji = get_voice_emoji(voice_name)
            display_name = get_voice_display_name(voice_name)
            
            # Send status message
            status_msg = await channel.send(f"{emoji} Generating {display_name} TTS: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            # Create a temporary directory for this TTS  
            download_path = os.path.join(self.temp_dir, f"{voice_name}_tts_{channel.guild.id}")
            Path(download_path).mkdir(exist_ok=True)
            
            # Generate TTS audio file path
            tts_file = os.path.join(download_path, f"{voice_name}_tts_{channel.guild.id}.mp3")
            
            # Run voice TTS generation in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def generate_tts():
                """Generate voice TTS using Minimax API in separate thread"""
                return generate_voice_tts_file(text, voice_name, tts_file, max_wait_minutes=15)
            
            # Generate voice TTS with timeout
            success = await asyncio.wait_for(
                loop.run_in_executor(None, generate_tts),
                timeout=900.0  # 15 minute timeout
            )
            
            if not success or not os.path.exists(tts_file):
                await status_msg.edit(content=f"❌ Could not generate {display_name} TTS audio.")
                return
            
            await status_msg.edit(content=f"{emoji} Generated! Joining voice channel...")
            
            # Join voice channel
            voice_client = await self.join_voice_channel(voice_channel)
            
            # Stop any currently playing audio
            if voice_client.is_playing():
                voice_client.stop()
            
            await status_msg.edit(content=f"{emoji} {display_name} speaking: {text[:30]}{'...' if len(text) > 30 else ''}")
            
            # Play the voice TTS audio
            audio_source = discord.FFmpegPCMAudio(tts_file)
            voice_client.play(audio_source)
            
            # Wait for playback to finish, then clean up
            while voice_client.is_playing():
                await asyncio.sleep(1)
                
            # Clean up the TTS file
            try:
                os.remove(tts_file)
                # Remove download directory if empty
                if os.path.exists(download_path) and not os.listdir(download_path):
                    os.rmdir(download_path)
            except Exception as e:
                logger.error(f"Error cleaning up {display_name} TTS file {tts_file}: {e}")
            await status_msg.edit(content=f"✅ {display_name} finished speaking.")
                
        except asyncio.TimeoutError:
            await channel.send(f"⏱️ {get_voice_display_name(voice_name)} TTS generation timed out.")
        except Exception as e:
            await channel.send(f"❌ {get_voice_display_name(voice_name)} TTS Error: {str(e)}")
            logger.error(f"Error in generate_voice_tts_and_play for {voice_name}: {e}")

    async def generate_obama_tts_and_play(self, channel, text, voice_channel):
        """Generate Obama TTS audio and play it in the voice channel."""
        await self.generate_voice_tts_and_play(channel, text, voice_channel, "obama")

    async def generate_trump_tts_and_play(self, channel, text, voice_channel):
        """Generate Trump TTS audio and play it in the voice channel."""
        await self.generate_voice_tts_and_play(channel, text, voice_channel, "trump")

    async def generate_peter_tts_and_play(self, channel, text, voice_channel):
        """Generate Peter TTS audio and play it in the voice channel."""
        await self.generate_voice_tts_and_play(channel, text, voice_channel, "peter")

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
        logger.info(f'{bot.user} has connected to Discord!')
        logger.info(f'Bot is ready to receive commands.')
        logger.info(f'Bot ID: {bot.user.id}')
        logger.info(f'Guilds: {[guild.name for guild in bot.guilds]}')
    
    @bot.event
    async def on_message(message):
        # Don't respond to the bot's own messages
        if message.author == bot.user:
            return
        
        # Debug: Print all messages to console
        logger.info(f"Message received: '{message.content}' from {message.author} in #{message.channel}")
        
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
    
    @bot.command(name='youtube')
    async def youtube_command(ctx, *, url):
        """Download and play audio from a YouTube URL."""
        # Check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Basic validation to check if it's a YouTube URL
        if not any(domain in url.lower() for domain in ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']):
            await ctx.send("❌ Please provide a valid YouTube URL!")
            return
        
        # Download and play the audio
        await music_bot.download_and_play_youtube_url(ctx.channel, url, voice_channel)
    
    @bot.command(name='bob')
    async def llm_command(ctx, *, prompt):
        """Send a prompt to the LLM via priority queue."""
        try:
            await ctx.send(f"🧠 Adding to LLM queue: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Run the blocking LLM request in a separate thread to avoid blocking the Discord event loop
            loop = asyncio.get_event_loop()
            
            def submit_llm_request():
                """Submit request in separate thread"""
                try:
                    return music_bot.llm_queue.submit_request(prompt, priority=1, task="discord")
                except Exception as e:
                    logger.error(f"Error submitting LLM request: {e}")
                    return None
            
            # Run in executor with timeout to avoid blocking the event loop
            try:
                future = await asyncio.wait_for(
                    loop.run_in_executor(None, submit_llm_request),
                    timeout=2340.0  # 39 minute timeout
                )
                
                # Get the response
                if future:
                    response = future.result() if hasattr(future, 'result') else future
                    if response:
                        # Handle both string and dict responses
                        if isinstance(response, dict) and 'response' in response:
                            response_text = response['response']
                        elif isinstance(response, str):
                            response_text = response
                        else:
                            response_text = str(response)
                        
                        # Split long responses into chunks
                        max_length = 1900
                        if len(response_text) <= max_length:
                            await ctx.send(f"💭 {response_text}")
                        else:
                            # Send in chunks
                            chunks = [response_text[i:i+max_length] for i in range(0, len(response_text), max_length)]
                            for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
                                await ctx.send(f"💭 ({i+1}/{len(chunks)}) {chunk}")
                            if len(chunks) > 3:
                                await ctx.send("💭 Response truncated (too long)")
                    else:
                        await ctx.send("🤔 LLM returned empty response")
                else:
                    await ctx.send("🤔 LLM request failed")
            except asyncio.TimeoutError:
                await ctx.send("⏱️ LLM request timed out after 2340 seconds. The request may still be processing in the background.")
                
        except Exception as e:
            await ctx.send(f"❌ Error with LLM request: {str(e)}")
            logger.error(f"Error in llm_command: {e}")
    
    @bot.command(name='bob_talk')
    async def bob_talk_command(ctx, *, prompt):
        """Send a prompt to the LLM and speak the response in voice chat."""
        try:
            # Check if user is in a voice channel
            if ctx.author.voice is None:
                await ctx.send("❌ You need to be in a voice channel to use this command!")
                return
                
            voice_channel = ctx.author.voice.channel
            
            await ctx.send(f"🧠🔊 Adding to LLM queue and will speak response: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Run the blocking LLM request in a separate thread to avoid blocking the Discord event loop
            loop = asyncio.get_event_loop()
            
            def submit_llm_request():
                """Submit request in separate thread"""
                try:
                    return music_bot.llm_queue.submit_request(prompt, priority=1, task="discord")
                except Exception as e:
                    logger.error(f"Error submitting LLM request: {e}")
                    return None
            
            # Run in executor with timeout to avoid blocking the event loop
            try:
                future = await asyncio.wait_for(
                    loop.run_in_executor(None, submit_llm_request),
                    timeout=2340.0  # 39 minute timeout
                )
                
                # Get the response
                if future:
                    response = future.result() if hasattr(future, 'result') else future
                    if response:
                        # Handle both string and dict responses
                        if isinstance(response, dict) and 'response' in response:
                            response_text = response['response']
                        elif isinstance(response, str):
                            response_text = response
                        else:
                            response_text = str(response)
                        
                        # Limit text length for TTS to prevent abuse
                        if len(response_text) > 1000:
                            response_text = response_text[:1000]
                            await ctx.send("⚠️ Response truncated to 1000 characters for TTS.")
                        
                        # Generate TTS and play the response
                        await music_bot.generate_tts_and_play(ctx.channel, response_text, voice_channel)
                        
                    else:
                        await ctx.send("🤔 LLM returned empty response")
                else:
                    await ctx.send("🤔 LLM request failed")
            except asyncio.TimeoutError:
                await ctx.send("⏱️ LLM request timed out after 2340 seconds.")
                
        except Exception as e:
            await ctx.send(f"❌ Error with LLM talk request: {str(e)}")
            logger.error(f"Error in bob_talk_command: {e}")
    
    @bot.command(name='bob_talk_obama')
    async def bob_talk_obama_command(ctx, *, prompt):
        """Send a prompt to the LLM and speak the response using Obama voice in voice chat."""
        try:
            # Check if user is in a voice channel
            if ctx.author.voice is None:
                await ctx.send("❌ You need to be in a voice channel to use this command!")
                return
                
            voice_channel = ctx.author.voice.channel
            
            await ctx.send(f"🧠🇺🇸 Adding to LLM queue and will speak response with Obama voice: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Run the blocking LLM request in a separate thread to avoid blocking the Discord event loop
            loop = asyncio.get_event_loop()
            
            def submit_llm_request():
                """Submit request in separate thread"""
                try:
                    return music_bot.llm_queue.submit_request(prompt, priority=1, task="discord")
                except Exception as e:
                    logger.error(f"Error submitting LLM request: {e}")
                    return None
            
            # Run in executor with timeout to avoid blocking the event loop
            try:
                future = await asyncio.wait_for(
                    loop.run_in_executor(None, submit_llm_request),
                    timeout=2340.0  # 39 minute timeout
                )
                
                # Get the response
                if future:
                    response = future.result() if hasattr(future, 'result') else future
                    if response:
                        # Handle both string and dict responses
                        if isinstance(response, dict) and 'response' in response:
                            response_text = response['response']
                        elif isinstance(response, str):
                            response_text = response
                        else:
                            response_text = str(response)
                        
                        # Limit text length for TTS to prevent abuse
                        if len(response_text) > 1000:
                            response_text = response_text[:1000]
                            await ctx.send("⚠️ Response truncated to 1000 characters for Obama TTS.")
                        
                        # Generate Obama TTS and play the response
                        await music_bot.generate_obama_tts_and_play(ctx.channel, response_text, voice_channel)
                        
                    else:
                        await ctx.send("🤔 LLM returned empty response")
                else:
                    await ctx.send("🤔 LLM request failed")
            except asyncio.TimeoutError:
                await ctx.send("⏱️ LLM request timed out after 2340 seconds.")
                
        except Exception as e:
            await ctx.send(f"❌ Error with LLM Obama talk request: {str(e)}")
            logger.error(f"Error in bob_talk_obama_command: {e}")
    
    @bot.command(name='bob_talk_trump')
    async def bob_talk_trump_command(ctx, *, prompt):
        """Send a prompt to the LLM and speak the response using Trump voice in voice chat."""
        try:
            # Check if user is in a voice channel
            if ctx.author.voice is None:
                await ctx.send("❌ You need to be in a voice channel to use this command!")
                return
                
            voice_channel = ctx.author.voice.channel
            
            await ctx.send(f"🧠🔴 Adding to LLM queue and will speak response with Trump voice: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Run the blocking LLM request in a separate thread to avoid blocking the Discord event loop
            loop = asyncio.get_event_loop()
            
            def submit_llm_request():
                """Submit request in separate thread"""
                try:
                    return music_bot.llm_queue.submit_request(prompt, priority=1, task="discord")
                except Exception as e:
                    logger.error(f"Error submitting LLM request: {e}")
                    return None
            
            # Run in executor with timeout to avoid blocking the event loop
            try:
                future = await asyncio.wait_for(
                    loop.run_in_executor(None, submit_llm_request),
                    timeout=2340.0  # 39 minute timeout
                )
                
                # Get the response
                if future:
                    response = future.result() if hasattr(future, 'result') else future
                    if response:
                        # Handle both string and dict responses
                        if isinstance(response, dict) and 'response' in response:
                            response_text = response['response']
                        elif isinstance(response, str):
                            response_text = response
                        else:
                            response_text = str(response)
                        
                        # Limit text length for TTS to prevent abuse
                        if len(response_text) > 1000:
                            response_text = response_text[:1000]
                            await ctx.send("⚠️ Response truncated to 1000 characters for Trump TTS.")
                        
                        # Generate Trump TTS and play the response
                        await music_bot.generate_trump_tts_and_play(ctx.channel, response_text, voice_channel)
                        
                    else:
                        await ctx.send("🤔 LLM returned empty response")
                else:
                    await ctx.send("🤔 LLM request failed")
            except asyncio.TimeoutError:
                await ctx.send("⏱️ LLM request timed out after 2340 seconds.")
                
        except Exception as e:
            await ctx.send(f"❌ Error with LLM Trump talk request: {str(e)}")
            logger.error(f"Error in bob_talk_trump_command: {e}")
    
    @bot.command(name='bob_talk_peter')
    async def bob_talk_peter_command(ctx, *, prompt):
        """Send a prompt to the LLM and speak the response using Peter voice in voice chat."""
        try:
            # Check if user is in a voice channel
            if ctx.author.voice is None:
                await ctx.send("❌ You need to be in a voice channel to use this command!")
                return
                
            voice_channel = ctx.author.voice.channel
            
            await ctx.send(f"🧠🔷 Adding to LLM queue and will speak response with Peter voice: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Run the blocking LLM request in a separate thread to avoid blocking the Discord event loop
            loop = asyncio.get_event_loop()
            
            def submit_llm_request():
                """Submit request in separate thread"""
                try:
                    return music_bot.llm_queue.submit_request(prompt, priority=1, task="discord")
                except Exception as e:
                    logger.error(f"Error submitting LLM request: {e}")
                    return None
            
            # Run in executor with timeout to avoid blocking the event loop
            try:
                future = await asyncio.wait_for(
                    loop.run_in_executor(None, submit_llm_request),
                    timeout=2340.0  # 39 minute timeout
                )
                
                # Get the response
                if future:
                    response = future.result() if hasattr(future, 'result') else future
                    if response:
                        # Handle both string and dict responses
                        if isinstance(response, dict) and 'response' in response:
                            response_text = response['response']
                        elif isinstance(response, str):
                            response_text = response
                        else:
                            response_text = str(response)
                        
                        # Limit text length for TTS to prevent abuse
                        if len(response_text) > 1000:
                            response_text = response_text[:1000]
                            await ctx.send("⚠️ Response truncated to 1000 characters for Peter TTS.")
                        
                        # Generate Peter TTS and play the response
                        await music_bot.generate_peter_tts_and_play(ctx.channel, response_text, voice_channel)
                        
                    else:
                        await ctx.send("🤔 LLM returned empty response")
                else:
                    await ctx.send("🤔 LLM request failed")
            except asyncio.TimeoutError:
                await ctx.send("⏱️ LLM request timed out after 2340 seconds.")
                
        except Exception as e:
            await ctx.send(f"❌ Error with LLM Peter talk request: {str(e)}")
            logger.error(f"Error in bob_talk_peter_command: {e}")
    
    @bot.command(name='status')
    async def status_command(ctx):
        """Get the current status of the system and LLM queue."""
        try:
            # Get queue status
            queue_manager = music_bot.llm_queue
            queue_status = queue_manager.get_status()
            
            # Get basic system info
            import psutil
            import platform
            
            # CPU and Memory info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Format current request info
            current_info = "None"
            if queue_status['current_request']:
                req = queue_status['current_request']
                current_info = f"{req['task']} (priority {req['priority']})"
            
            # Get cluster health status using new discovery method
            try:
                cluster_health = health_check_all_hosts()
                healthy_hosts = get_healthy_hosts()
                cluster_status_lines = []
                
                if cluster_health:
                    cluster_status_lines.append(f"• Total Hosts: {len(cluster_health)} discovered")
                    for hostname, health_data in cluster_health.items():
                        agent_name = health_data.get('agent_name', "unknown")
                        if health_data.get('status') == 'healthy':
                            response_time = health_data.get('response_time', 0)
                            cluster_status_lines.append(f"• {agent_name}: ✅ Healthy ({response_time:.3f}s)")
                        else:
                            error = health_data.get('error', 'unreachable')
                            cluster_status_lines.append(f"• {agent_name}: ❌ {error}")
                    cluster_status_lines.append(f"• Healthy Nodes: {len(healthy_hosts)}/{len(cluster_health)}")
                else:
                    cluster_status_lines.append("• No cluster hosts discovered")
                
                cluster_status_text = "\n".join(cluster_status_lines)
            except Exception as e:
                cluster_status_text = f"• Error checking cluster: {str(e)[:100]}"
            
            # Build status message
            status_text = f"""
🤖 **System Status:**

**Hardware:**
• Platform: {platform.system()} {platform.release()}
• CPU Usage: {cpu_percent}%
• Memory: {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)
• Disk: {disk.percent}% ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)

**LLM Queue:**
• Queue Size: {queue_status['queue_size']} requests waiting
• Current Processing: {current_info}
• LLM Ready: {'Yes' if queue_status['llm_ready'] else 'No'}
• Queue Running: {'Yes' if queue_status['running'] else 'No'}

**Discord Bot:**
• Connected Servers: {len(ctx.bot.guilds)}
• Voice Channels: {len(music_bot.voice_clients)} active

**Raspberry Pi Cluster:**
{cluster_status_text}
            """
            
            # Split into chunks if too long
            if len(status_text) > 2000:
                chunks = [status_text[i:i+1900] for i in range(0, len(status_text), 1900)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(status_text)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting status: {str(e)}")
            logger.error(f"Error in status_command: {e}")

    @bot.command(name='image')
    async def image_command(ctx, *, prompt):
        """Generate an AI image based on the prompt."""
        await music_bot.generate_and_send_image(ctx.channel, prompt)
    
    @bot.command(name='say')
    async def say_command(ctx, *, text):
        """Use text-to-speech to speak in the voice channel."""
        # Check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Limit text length to prevent abuse
        if len(text) > 500:
            await ctx.send("❌ Text too long! Please limit to 500 characters.")
            return
        
        # Generate TTS and play
        await music_bot.generate_tts_and_play(ctx.channel, text, voice_channel)
    
    @bot.command(name='say_obama')
    async def say_obama_command(ctx, *, text):
        """Use Obama voice text-to-speech via Minimax API to speak in the voice channel."""
        # Check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Limit text length to prevent abuse
        if len(text) > 1000:
            await ctx.send("❌ Text too long! Please limit to 1000 characters.")
            return
        
        # Generate Obama TTS and play
        await music_bot.generate_obama_tts_and_play(ctx.channel, text, voice_channel)
    
    @bot.command(name='say_trump')
    async def say_trump_command(ctx, *, text):
        """Use Trump voice text-to-speech via Minimax API to speak in the voice channel."""
        # Check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Limit text length to prevent abuse
        if len(text) > 1000:
            await ctx.send("❌ Text too long! Please limit to 1000 characters.")
            return
        
        # Generate Trump TTS and play
        await music_bot.generate_trump_tts_and_play(ctx.channel, text, voice_channel)
    
    @bot.command(name='say_peter')
    async def say_peter_command(ctx, *, text):
        """Use Peter voice text-to-speech via Minimax API to speak in the voice channel."""
        # Check if user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Limit text length to prevent abuse
        if len(text) > 1000:
            await ctx.send("❌ Text too long! Please limit to 1000 characters.")
            return
        
        # Generate Peter TTS and play
        await music_bot.generate_peter_tts_and_play(ctx.channel, text, voice_channel)
    
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
    
    @bot.command(name='convo')
    async def convo_command(ctx, *, topic):
        """Generate a conversation chain with video about the given topic."""
        try:
            # Send initial status message
            status_msg = await ctx.send(f"🎭 Starting conversation video generation about: {topic}")
            
            # Create a temporary directory for this conversation
            convo_path = os.path.join(music_bot.temp_dir, f"convo_{ctx.guild.id}_{ctx.message.id}")
            Path(convo_path).mkdir(exist_ok=True)
            
            final_audio_path = os.path.join(convo_path, "final_convo.mp3")
            video_download_path = os.path.join(convo_path, "downloaded_video")
            final_video_path = os.path.join(convo_path, "final_convo_video.mp4")
            
            # Run the full process in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Update status for video download
            await status_msg.edit(content=f"📥 Downloading video and generating conversation about: {topic}...")
            
            # Generate conversation video with no timeout (this will take a while)
            try:
                def sync_generate_full_convo_video():
                    """Synchronous wrapper for generating the conversation video"""
                    try:
                        # Step 1: Download the YouTube video
                        video_file = download_youtube_video("https://www.youtube.com/watch?v=EtVOvPyuOjk", video_download_path)
                        
                        if not video_file or not os.path.exists(video_file):
                            raise Exception("Failed to download YouTube video")
                        
                        # Step 2: Generate conversation
                        convo = generate_convo(topic)
                        
                        # Step 3: Convert to audio
                        convo_to_audio(convo)
                        
                        # Step 4: Splice audio together
                        splice_audio_together(len(convo), final_audio_path)
                        
                        if not os.path.exists(final_audio_path):
                            raise Exception("Failed to generate conversation audio")
                        
                        # Step 5: Get audio duration for trimming
                        import subprocess
                        result = subprocess.run(
                            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', 
                             '-of', 'csv=p=0', final_audio_path],
                            capture_output=True, text=True
                        )
                        audio_duration = float(result.stdout.strip())
                        
                        # Step 6: Replace video audio with conversation audio and trim with compression and cropping
                        trim_cmd = [
                            'ffmpeg', '-i', video_file, '-i', final_audio_path,
                            '-c:v', 'libx264', '-crf', '26', '-preset', 'medium', 
                            '-vf', 'crop=ih*9/16:ih,scale=480:854',  # Crop to 9:16 aspect ratio and scale to phone size
                            '-c:a', 'aac', '-b:a', '128k',
                            '-map', '0:v:0', '-map', '1:a:0',
                            '-t', str(audio_duration), '-y', final_video_path
                        ]
                        
                        subprocess.run(trim_cmd, check=True)
                        
                        if not os.path.exists(final_video_path):
                            raise Exception("Failed to create final video")
                        
                        return final_video_path, len(convo), audio_duration
                        
                    except Exception as e:
                        logger.error(f"Error in sync_generate_full_convo_video: {e}")
                        raise
                
                result = await loop.run_in_executor(None, sync_generate_full_convo_video)
                video_file_path, convo_length, audio_duration = result
                
                if not video_file_path or not os.path.exists(video_file_path):
                    await status_msg.edit(content="❌ Failed to generate conversation video.")
                    return
                
                # Update status for chunking and upload
                await status_msg.edit(content=f"✅ Generated {convo_length} part conversation video! Splitting into chunks...")
                
                # Split video into 1-minute chunks
                def split_video_into_chunks():
                    """Split the video into 1-minute chunks"""
                    chunk_files = []
                    chunk_duration = 60  # 1 minute in seconds
                    total_chunks = math.ceil(audio_duration / chunk_duration)  # audio_duration is in seconds
                    
                    for i in range(total_chunks):
                        start_time = i * chunk_duration
                        chunk_file = os.path.join(os.path.dirname(video_file_path), f"conversation_chunk_{i+1}.mp4")
                        
                        chunk_cmd = [
                            'ffmpeg', '-i', video_file_path,
                            '-ss', str(start_time), '-t', str(min(chunk_duration, audio_duration - start_time)),
                            '-c', 'copy', '-avoid_negative_ts', 'make_zero',
                            '-y', chunk_file
                        ]
                        
                        subprocess.run(chunk_cmd, check=True)
                        
                        if os.path.exists(chunk_file):
                            chunk_files.append(chunk_file)
                    
                    return chunk_files
                
                # Split video into chunks
                chunk_files = await loop.run_in_executor(None, split_video_into_chunks)
                
                if not chunk_files:
                    await status_msg.edit(content="❌ Failed to split video into chunks.")
                    return
                
                # Upload each chunk
                await status_msg.edit(content=f"📤 Uploading {len(chunk_files)} video chunks...")
                
                for i, chunk_file in enumerate(chunk_files):
                    try:
                        # Check file size for each chunk
                        file_size = os.path.getsize(chunk_file)
                        file_size_mb = file_size / (1024 * 1024)
                        
                        chunk_number = i + 1
                        total_chunks = len(chunk_files)
                        
                        with open(chunk_file, 'rb') as f:
                            file = discord.File(f, filename=f"conversation_{topic.replace(' ', '_')[:20]}_part{chunk_number}.mp4")
                            await ctx.send(
                                f"🎭 **{topic}** - Part {chunk_number}/{total_chunks} ({file_size_mb:.1f}MB)\n"
                                f"Obama & Trump conversation ({convo_length} total parts):",
                                file=file
                            )
                        
                        # Small delay between uploads to avoid rate limits
                        if i < len(chunk_files) - 1:
                            await asyncio.sleep(1)
                            
                    except Exception as e:
                        await ctx.send(f"❌ Failed to upload part {i+1}: {str(e)[:50]}")
                        logger.error(f"Error uploading chunk {i+1}: {e}")
                
                # Clean up chunk files
                for chunk_file in chunk_files:
                    try:
                        os.remove(chunk_file)
                    except Exception as e:
                        logger.error(f"Error cleaning up chunk file {chunk_file}: {e}")
                
                # Clean up
                await status_msg.edit(content=f"🎭 Conversation video uploaded successfully in {len(chunk_files)} parts!")
                
            except Exception as e:
                await status_msg.edit(content=f"❌ Error during conversation video generation: {str(e)[:100]}")
                logger.error(f"Error in convo video generation: {e}")
            
            # Clean up temporary files
            try:
                if os.path.exists(convo_path):
                    shutil.rmtree(convo_path)
            except Exception as e:
                logger.error(f"Error cleaning up convo files: {e}")
                
        except Exception as e:
            await ctx.send(f"❌ Error with conversation command: {str(e)}")
            logger.error(f"Error in convo_command: {e}")
    
    @bot.command(name='help_bob')
    async def help_bob(ctx):
        """Show help for music commands."""
        help_text = """
🤖 **Bot Commands:**

**Music & Audio:**
• `!groovy <song name>` - Search and play audio from YouTube
• `!youtube <url>` - Play audio from a specific YouTube URL
• `!say <text>` - Speak text using standard text-to-speech
• `!say_obama <text>` - Speak text using Obama voice (Minimax API)
• `!say_trump <text>` - Speak text using Trump voice (Minimax API)
• `!say_peter <text>` - Speak text using Peter voice (Minimax API)
• `!stop` - Stop the currently playing music
• `!leave` - Make the bot leave the voice channel

**AI Features:**
• `!bob <prompt>` - Send a prompt to the LLM
• `!bob_talk <prompt>` - Send a prompt to the LLM and speak the response
• `!bob_talk_obama <prompt>` - Send a prompt to the LLM and speak with Obama voice
• `!bob_talk_trump <prompt>` - Send a prompt to the LLM and speak with Trump voice
• `!bob_talk_peter <prompt>` - Send a prompt to the LLM and speak with Peter voice
• `!image <description>` - Generate an AI image
• `!convo <topic>` - Generate a conversation video with Obama/Trump voices about a topic

**System:**
• `!status` - Show system status and LLM queue info
• `!test` - Test if bot is responding
• `!help_bob` - Show this help message

**Examples:**
• `!groovy Bohemian Rhapsody`
• `!youtube https://www.youtube.com/watch?v=fJ9rUzIMcZQ`
• `!say Hello everyone, how are you doing today?`
• `!say_obama My fellow Americans, we choose to go to the moon!`
• `!say_trump This is going to be tremendous, believe me!`
• `!say_peter Hey there, how's it going everybody?`
• `!bob What is the meaning of life?`
• `!bob_talk Tell me a joke`
• `!bob_talk_obama Tell me about the audacity of hope`
• `!bob_talk_trump Tell me about making America great again`
• `!bob_talk_peter Tell me something interesting`
• `!image a cute cat wearing sunglasses`
• `!convo the benefits of exercise` - Generate Obama/Trump conversation video
• `!status` - Check what's currently processing
        """
        await ctx.send(help_text)
    
    return bot, music_bot

def run_discord_bot():
    """Run the Discord bot (for standalone usage)."""
    # Check for bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        logger.error("Error: DISCORD_BOT_TOKEN environment variable not set.")
        logger.error("Please set your Discord bot token:")
        logger.error("export DISCORD_BOT_TOKEN='your_bot_token_here'")
        return None
    
    # Check for FFmpeg
    if shutil.which('ffmpeg') is None:
        logger.warning("Warning: FFmpeg not found. Please install FFmpeg for audio processing:")
        logger.warning("brew install ffmpeg  # macOS")
        logger.warning("sudo apt install ffmpeg  # Ubuntu/Debian")
    
    bot, music_bot = create_discord_bot()
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Error: Invalid bot token. Please check your DISCORD_BOT_TOKEN.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(music_bot.temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {e}")

async def run_discord_bot_async():
    """Run the Discord bot asynchronously (for thread usage)."""
    # Check for bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        logger.error("Error: DISCORD_BOT_TOKEN environment variable not set.")
        return
    
    bot, music_bot = create_discord_bot()
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Error: Invalid bot token. Please check your DISCORD_BOT_TOKEN.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(music_bot.temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {e}")