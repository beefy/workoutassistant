# Process emails every 5 minutes
import random
from process_email import process_email
from browse_moltbook import browse_moltbook
from gmail import GmailClient
import os

import time


if __name__ == "__main__":
    try:
        while True:
            # Check and process emails
            process_email()
            time.sleep(900)  # Sleep for 15 minutes

            # Randomly browse Moltbook once in a while
            if random.random() < 0.2:  # 20% chance every 15 minutes
                print("🔍 Randomly browsing Moltbook...")
                browse_moltbook()
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        admin_email = os.getenv("ADMIN_EMAIL")
        client = GmailClient()
        client.send_email_with_attachment(admin_email, "Bob encountered an Exception", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
