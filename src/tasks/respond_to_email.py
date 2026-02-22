from utils.process_email import process_email
import time


def main():
    while True:
        # Check and process emails
        process_email()
        time.sleep(900)  # Sleep for 15 minutes
