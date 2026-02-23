from utils.tracking_api import login, status_update
import os
import time
from clients.gmail import GmailClient
from llm.priority_queue import submit_llm_request



def main():
    try:
        while True:
            llm_result = submit_llm_request("", priority=1, max_tokens=200, temperature=0.7, final_query=False, use_crypto_prompt=True)
            response = llm_result.get('response', '')
            # Sleep for 1 hour before sending the next heartbeat
            time.sleep(3600)
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        admin_email = os.getenv("ADMIN_EMAIL")
        client = GmailClient()
        client.send_email_with_attachment(admin_email, "Bob encountered an Exception", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, "Error!")
