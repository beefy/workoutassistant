# Process emails every 5 minutes
import random
from process_email import process_email
from browse_moltbook import browse_moltbook
import time


if __name__ == "__main__":
    while True:
        # Check and process emails
        process_email()
        time.sleep(900)  # Sleep for 15 minutes

        # Randomly browse Moltbook once in a while
        if random.random() < 0.1:  # 10% chance every 10 minutes
            print("🔍 Randomly browsing Moltbook...")
            browse_moltbook()
