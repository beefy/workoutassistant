# Process emails every 5 minutes
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
