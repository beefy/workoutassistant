# Process emails every 5 minutes
from process_email import process_email
import time


if __name__ == "__main__":
    while True:
        process_email()
        time.sleep(300)  # Sleep for 5 minutes
