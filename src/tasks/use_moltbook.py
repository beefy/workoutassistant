import os

from utils.tracking_api import login, status_update
from utils.browse_moltbook import browse_moltbook
import random
import time
from clients.gmail import GmailClient


def main():
    try:
        while True:
            tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))

            # Randomly browse Moltbook once in a while
            if random.random() < 0.2:  # 20% chance every 15 minutes
                if tracking_token:
                    status_update(tracking_token, "Browsing Moltbook")

                print("🔍 Randomly browsing Moltbook...")
                browse_moltbook()

            time.sleep(900)  # Sleep for 15 minutes
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        admin_email = os.getenv("ADMIN_EMAIL")
        client = GmailClient()
        client.send_email_with_attachment(admin_email, "Bob encountered an Exception", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, "Error!")
