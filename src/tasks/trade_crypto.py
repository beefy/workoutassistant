import time
from llm.priority_queue import submit_llm_request
from utils.last_run import get_last_run_time, update_last_run_time


def main():
    while True:
        last_run_time = get_last_run_time("trade_crypto")
        current_time = time.time()
        # Check if it's been more than 1 hour since the last run
        if not last_run_time or (current_time - last_run_time) > 3600:
            # Update last run time BEFORE processing to prevent duplicate runs
            update_last_run_time("trade_crypto", current_time)
            
            llm_result = submit_llm_request("", priority=1, max_tokens=1000, temperature=0.7, final_query=False, use_crypto_prompt=True)
            response = llm_result.get('response', '')
            print(f"LLM response for crypto trading: {response}")
            
            # Sleep for 1 hour before attempting to trade again
            time.sleep(3600)
        else:
            # Sleep for 5 minutes before checking again
            time.sleep(300)
