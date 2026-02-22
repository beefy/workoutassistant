from utils.summarize_news import email_news_summary
from utils.process_email import process_email
import time
from datetime import datetime
import pytz
from clients.gmail import GmailClient
import os
from utils.tracking_api import login, status_update


def main():
    try:
        while True:
            # send email newsletter every day at 8am EST
            est = pytz.timezone('US/Eastern')
            now = datetime.now(est)
            if now.hour == 8 and now.minute == 0:
                email_news_summary()
                token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
                if token:
                    status_update(token, "Sent daily newsletter email")

            time.sleep(60)  # Sleep for 1 minute to check the time again
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        admin_email = os.getenv("ADMIN_EMAIL")
        client = GmailClient()
        client.send_email_with_attachment(admin_email, "Bob encountered an Exception", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, "Error!")
