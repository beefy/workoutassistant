# Process emails every 5 minutes
from clients.gmail import GmailClient
import os
from tasks import heartbeat, use_moltbook, respond_to_email
from utils.tracking_api import login, status_update
import threading

import time


if __name__ == "__main__":
    try:
        # start threads
        threading.Thread(target=heartbeat.main, daemon=True).start()
        threading.Thread(target=use_moltbook.main, daemon=True).start()
        threading.Thread(target=respond_to_email.main, daemon=True).start()
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        admin_email = os.getenv("ADMIN_EMAIL")
        client = GmailClient()
        client.send_email_with_attachment(admin_email, "Bob encountered an Exception", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, "Error!")
