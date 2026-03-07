#!/usr/bin/env python3
"""
Voice TTS Utility Module
Provides centralized voice TTS functionality using Minimax API.
"""

import os
import logging
from pathlib import Path
from clients.minimax import create_speech_gen_task, check_speech_gen_task_status, retrieve_file_content

# Setup logging
logger = logging.getLogger(__name__)

# Voice ID constants
OBAMA_VOICE_ID = "moss_audio_8dd65fdb-19a0-11f1-a9eb-d68e15ebe5cd"
TRUMP_VOICE_ID = "moss_audio_9561203c-19b4-11f1-a01c-32006e4c0821"
PETER_VOICE_ID = "moss_audio_ddb8ca95-19ba-11f1-b623-469aaa213a1a"

# Voice configuration mapping
VOICE_CONFIGS = {
    "obama": {
        "voice_id": OBAMA_VOICE_ID,
        "emoji": "🇺🇸",
        "name": "Obama"
    },
    "trump": {
        "voice_id": TRUMP_VOICE_ID,
        "emoji": "🔴",
        "name": "Trump"
    },
    "peter": {
        "voice_id": PETER_VOICE_ID,
        "emoji": "🔷",
        "name": "Peter"
    }
}

def generate_voice_tts_file(text: str, voice_name: str, output_file_path: str, max_wait_minutes: int = 15) -> bool:
    """
    Generate TTS audio file using Minimax API for a specific voice.
    
    Args:
        text (str): Text to convert to speech
        voice_name (str): Voice name ("obama", "trump", "peter")
        output_file_path (str): Path where the MP3 file should be saved
        max_wait_minutes (int): Maximum time to wait for generation (default 15 minutes)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate voice name
        if voice_name.lower() not in VOICE_CONFIGS:
            logger.error(f"Invalid voice name: {voice_name}. Available: {list(VOICE_CONFIGS.keys())}")
            return False
        
        voice_config = VOICE_CONFIGS[voice_name.lower()]
        voice_id = voice_config["voice_id"]
        voice_display_name = voice_config["name"]
        
        # Create speech generation task
        logger.info(f"Creating {voice_display_name} speech generation task for text: {text[:100]}...")
        response = create_speech_gen_task(voice_id, text)
        task_id = response["task_id"]
        logger.info(f"Created {voice_display_name} TTS task with ID: {task_id}")
        
        # Poll for completion (check every 5 seconds)
        import time
        max_attempts = max_wait_minutes * 12  # 12 attempts per minute (5 second intervals)
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(5)  # Wait 5 seconds between checks
            status_response = check_speech_gen_task_status(task_id)
            status = status_response.get("status", "")
            
            logger.info(f"Task {task_id} status check {attempt + 1}/{max_attempts}: {status}")
            
            if status == "Success":
                file_id = status_response["file_id"]
                logger.info(f"Task completed, retrieving file content for file_id: {file_id}")
                
                # Retrieve and save the file content
                file_content = retrieve_file_content(file_id)
                
                # Ensure output directory exists
                Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file_path, "wb") as f:
                    f.write(file_content)
                
                logger.info(f"{voice_display_name} TTS file saved: {output_file_path}")
                return True
                
            elif status == "Failed":
                logger.error(f"{voice_display_name} TTS task failed: {status_response}")
                return False
                
            attempt += 1
        
        logger.error(f"{voice_display_name} TTS task timed out after {max_attempts} attempts ({max_wait_minutes} minutes)")
        return False
        
    except Exception as e:
        logger.error(f"Error generating {voice_name} TTS: {e}")
        return False

def get_voice_emoji(voice_name: str) -> str:
    """Get the emoji for a specific voice."""
    return VOICE_CONFIGS.get(voice_name.lower(), {}).get("emoji", "🗣️")

def get_voice_display_name(voice_name: str) -> str:
    """Get the display name for a specific voice."""
    return VOICE_CONFIGS.get(voice_name.lower(), {}).get("name", voice_name.title())

def is_valid_voice(voice_name: str) -> bool:
    """Check if a voice name is valid."""
    return voice_name.lower() in VOICE_CONFIGS

def get_available_voices() -> list:
    """Get list of available voice names."""
    return list(VOICE_CONFIGS.keys())