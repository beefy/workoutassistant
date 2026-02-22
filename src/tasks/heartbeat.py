from utils.tracking_api import login, system_info_update, heartbeat, status_update
import os
import time
from clients.gmail import GmailClient


def main():
    try:
        while True:
            tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
            if tracking_token:
                system_info_update(tracking_token)
                heartbeat(tracking_token)
            
            # Sleep for 5 minutes before sending the next heartbeat
            time.sleep(300)
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        admin_email = os.getenv("ADMIN_EMAIL")
        client = GmailClient()
        client.send_email_with_attachment(admin_email, "Bob encountered an Exception", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, "Error!")
