from utils.process_email import process_email
import time


def main():
    while True:
        # Check and process emails
        process_email()
        time.sleep(300)  # Sleep for 5 minutes
