import time
import datetime
from llm.priority_queue import submit_llm_request
from utils.tracking_api import login, refresh_indicators
import os

def main():
    last_llm_request_hour = None
    
    while True:
        now = datetime.datetime.now()
        current_minute = now.minute
        current_hour = now.hour
        
        username = os.getenv("TRACKING_API_USERNAME")
        
        # Refresh indicators at the top of every hour
        if username == "bob" and current_minute == 0:
            print(f"Top of hour detected ({current_hour}:00), refreshing indicators...")
            token = login(username, os.getenv("TRACKING_API_PASSWORD"))
            refresh_indicators(token)
            print("Indicators refreshed.")
            
            # Check time again after refresh in case it took a while
            now = datetime.datetime.now()
            current_minute = now.minute
            current_hour = now.hour

        # Submit LLM request at 3+ minutes past the hour, but only once per hour
        if current_minute >= 3 and last_llm_request_hour != current_hour:
            print(f"3+ minutes past hour detected ({current_hour}:{current_minute:02d}), submitting LLM request...")
            llm_result = submit_llm_request("", priority=1, max_tokens=1000, temperature=0.7, final_query=False, use_crypto_prompt=True)
            response = llm_result.get('response', '')
            print(f"LLM response for crypto trading: {response}")
            last_llm_request_hour = current_hour
        
        # Sleep for 1 minute before checking again
        time.sleep(60)
