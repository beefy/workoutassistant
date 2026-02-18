# Process emails every 15 minutes
from process_email import process_email
import time


if __name__ == "__main__":
    while True:
        process_email()
        time.sleep(900)  # Sleep for 15 minutes
