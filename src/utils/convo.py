from llm.priority_queue import submit_llm_request
from clients.moltbook import MoltbookClient
from utils.tracking_api import status_update, login
from utils.logging_config import setup_logging
import os
import random
import logging

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


def convo_to_audio(convo):
    pass


if __name__ == "__main__":
    generate_convo("What are the benefits of exercise")
