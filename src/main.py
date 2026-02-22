# Process emails every 5 minutes
# 
# This application uses a priority queue system for LLM requests to prevent
# multiple LLM instances from being created simultaneously (which would cause
# memory issues). Email requests get priority 1 (high), while moltbook requests
# get priority 2 (low). The LLM is instantiated once globally and all requests
# go through the priority queue system defined in llm/priority_queue.py
from clients.gmail import GmailClient
import os
from tasks import heartbeat, use_moltbook, respond_to_email
from utils.tracking_api import login, status_update
import threading

if __name__ == "__main__":
    # start threads
    threading.Thread(target=heartbeat.main, daemon=True).start()
    threading.Thread(target=use_moltbook.main, daemon=True).start()
    threading.Thread(target=respond_to_email.main, daemon=True).start()
