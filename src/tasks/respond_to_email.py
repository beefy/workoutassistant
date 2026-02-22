from utils.process_email import process_email
import time
from clients.gmail import GmailClient
import os
from utils.tracking_api import login, status_update


def main():
    try:
        while True:
            # Check and process emails
            process_email()
            time.sleep(900)  # Sleep for 15 minutes
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        admin_email = os.getenv("ADMIN_EMAIL")
        client = GmailClient()
        client.send_email_with_attachment(admin_email, "Bob encountered an Exception", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, "Error!")
