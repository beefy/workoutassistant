from utils.tracking_api import login, status_update
import os
import time
from clients.gmail import GmailClient
from llm.priority_queue import submit_llm_request



def main():
    while True:
        llm_result = submit_llm_request("", priority=1, max_tokens=200, temperature=0.7, final_query=False, use_crypto_prompt=True)
        response = llm_result.get('response', '')
        print(f"LLM response for crypto trading: {response}")
        # Sleep for 1 hour before attempting to trade again
        time.sleep(3600)
