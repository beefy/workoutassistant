from utils.summarize_news import email_news_summary
import time
from datetime import datetime
import pytz
import os
from utils.tracking_api import login, status_update


def main():
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
