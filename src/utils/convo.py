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
        prompt=f"Start a conversation about the following topic: {topic}.",
        priority=1,
        max_tokens=100,
        temperature=0.9,
        task="Conversation"
    )
    convo.append(clean_text(response.get('response', '')))
    for _ in range(5):
        response = submit_llm_request(
            prompt=f"Make a short response to this comment in a conversational way: {convo[-1]}",
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
    # with a 1 second delay between each comment
    ffmpeg_command = "ffmpeg "
    for audio_file in audio_file_paths:
        ffmpeg_command += f"-i \"{audio_file}\" "
    ffmpeg_command += f"-filter_complex \""
    for i in range(convo_len):
        ffmpeg_command += f"[{i}:0]adelay={i*1000}|{i*1000}[a{i}];"
    for i in range(convo_len):
        ffmpeg_command += f"[a{i}]"
    ffmpeg_command += f"concat=n={convo_len}:v=0:a=1[out]\" -map \"[out]\" \"{output_file_path}\""
    os.system(ffmpeg_command)
    logger.info(f"Spliced audio files together into: {output_file_path}")


if __name__ == "__main__":
    convo = generate_convo("What are the benefits of exercise")
    convo_to_audio(convo)
    splice_audio_together(len(convo), "/app/audio/final_convo.mp3")
