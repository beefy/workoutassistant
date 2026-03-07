from llm.priority_queue import submit_llm_request
from clients.moltbook import MoltbookClient
from utils.tracking_api import status_update, login
from utils.logging_config import setup_logging
import os
import random
import logging
from utils.voices import generate_voice_tts_file

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def clean_text(text):
    # Remove "Dear User" and "Sincerely, Bob the Raspberry Pi"
    text = text.replace("Dear User,", "").strip().replace("Sincerely,", "").strip().replace("Bob the Raspberry Pi", "").strip()
    return text


def generate_convo(topic):
    convo = []
    response = submit_llm_request(
        prompt=f"Talk like Obama. Start a conversation about the following topic: {topic}.",
        priority=1,
        max_tokens=100,
        temperature=0.9,
        task="Conversation"
    )
    convo.append(clean_text(response.get('response', '')))
    for i in range(5):
        if i % 2 == 0:
            prefix = "Talk like Trump."
        else:
            prefix = "Talk like Obama."

        response = submit_llm_request(
            prompt=f"{prefix} Make a short response to this comment in a conversational way: {convo[-1]}",
            priority=1,
            max_tokens=100,
            temperature=0.9,
            task="Conversation"
        )
        convo.append(clean_text(response.get('response', '')))
    
    return convo


def convo_to_audio(convo):
    for i, comment in enumerate(convo):
        if i % 2 == 0:
            voice_name = "obama"
        else:
            voice_name = "trump"
        
        output_file_path = f"/app/audio/convo_part_{i+1}_{voice_name}.mp3"
        success = generate_voice_tts_file(comment, voice_name, output_file_path)
        if success:
            logger.info(f"Generated audio for comment {i+1} with {voice_name} voice: {output_file_path}")
        else:
            logger.error(f"Failed to generate audio for comment {i+1} with {voice_name} voice")


def splice_audio_together(convo_len, output_file_path):
    audio_file_paths = []
    for i in range(convo_len):
        if i % 2 == 0:
            voice_name = "obama"
        else:
            voice_name = "trump"
        
        audio_file_paths.append(f"/app/audio/convo_part_{i+1}_{voice_name}.mp3")
    
    # Use ffmpeg to splice audio files together
    # with a 1 second silence between each comment
    if convo_len == 1:
        # Simple case: just copy the single file
        ffmpeg_command = f"ffmpeg -y -i \"{audio_file_paths[0]}\" -c copy \"{output_file_path}\""
    else:
        # Build filter_complex to concat with 1 second silence between files
        ffmpeg_command = "ffmpeg -y "
        
        # Add all input files
        for audio_file in audio_file_paths:
            ffmpeg_command += f"-i \"{audio_file}\" "
        
        # Create a silence generator
        ffmpeg_command += "-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 "
        
        # Build the filter chain
        ffmpeg_command += "-filter_complex \""
        
        # Create 1 second silence clips for between audio
        silence_index = convo_len  # Index of the silence generator input
        for i in range(convo_len - 1):
            ffmpeg_command += f"[{silence_index}:0]atrim=0:1[silence{i}];"
        
        # Concatenate all audio with silence between them
        ffmpeg_command += "[0:0]"
        for i in range(convo_len - 1):
            ffmpeg_command += f"[silence{i}][{i+1}:0]"
        
        total_inputs = convo_len + (convo_len - 1)  # audio files + silence clips
        ffmpeg_command += f"concat=n={total_inputs}:v=0:a=1[out]\""
        
        ffmpeg_command += f" -map \"[out]\" \"{output_file_path}\""
    
    os.system(ffmpeg_command)
    logger.info(f"Spliced audio files together into: {output_file_path}")


if __name__ == "__main__":
    convo = generate_convo("What are the benefits of exercise")
    convo_to_audio(convo)
    splice_audio_together(len(convo), "/app/audio/final_convo.mp3")
