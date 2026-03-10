import time
import datetime
from llm.priority_queue import submit_llm_request
from utils.tracking_api import login, refresh_indicators, status_update, get_indicators
import os
import logging
from utils.logging_config import setup_logging
from utils.trading_strategy import alpha, beta

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def bob():
    last_llm_request_hour = None
    
    while True:
        now = datetime.datetime.now()
        current_minute = now.minute
        current_hour = now.hour
        
        # Refresh indicators at the top of every hour
        if current_minute == 50:
            logger.info(f"Top of hour detected ({current_hour}:00), refreshing indicators...")
            # track time spent refreshing indicators in case it takes a while
            start_time = datetime.datetime.now()
            token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
            refresh_indicators(token)
            end_time = datetime.datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            logger.info(f"Indicators refreshed in {elapsed_time:.2f} seconds.")
            status_update(token, f"Refreshed indicators (took {elapsed_time:.2f} seconds)")

            # check that indicators look good
            indicators = get_indicators(token)
            retry_count = 0
            while not indicators['indicators']:
                retry_count += 1
                if retry_count > 3:
                    logger.error("Indicators are empty after multiple refresh attempts, giving up for this hour.")
                    status_update(token, "Failed to refresh indicators after multiple attempts")
                    break

                time.sleep(60)  # wait 1 minute before trying again
                logger.warning("Indicators are empty after refresh, trying again...")
                start_time = datetime.datetime.now()
                refresh_indicators(token)
                end_time = datetime.datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                indicators = get_indicators(token)
                status_update(token, f"Refreshed indicators again (took {elapsed_time:.2f} seconds)")

            # Check time again after refresh in case it took a while
            now = datetime.datetime.now()
            current_minute = now.minute
            current_hour = now.hour

        # Submit LLM request at 1+ minutes past the hour, but only once per hour
        if last_llm_request_hour is None:
            last_llm_request_hour = current_hour  # Initialize on first run and don't run until the next hour
        elif current_minute >= 58 and last_llm_request_hour != current_hour:
            logger.info(f"1+ minutes past hour detected ({current_hour}:{current_minute:02d}), submitting LLM request...")
            llm_result = submit_llm_request("", priority=1, max_tokens=1000, temperature=0.7, final_query=False, use_crypto_prompt=True, task="Crypto trading decision")
            response = llm_result.get('response', '')
            logger.info(f"LLM response for crypto trading: {response}")
            last_llm_request_hour = current_hour
        
        # Sleep for 1 minute before checking again
        time.sleep(60)


def bobby():
    last_llm_request_hour = None
    
    while True:
        now = datetime.datetime.now()
        current_minute = now.minute
        current_hour = now.hour
        
        # Submit LLM request at 1+ minutes past the hour, but only once per hour
        if last_llm_request_hour is None:
            last_llm_request_hour = current_hour
        elif current_minute >= 58 and last_llm_request_hour != current_hour:
            logger.info(f"1+ minutes past hour detected ({current_hour}:{current_minute:02d}), submitting LLM request...")
            beta()
            last_llm_request_hour = current_hour

        time.sleep(60)  # Sleep for 1 minute


def robert():
    last_llm_request_hour = None
    
    while True:
        now = datetime.datetime.now()
        current_minute = now.minute
        current_hour = now.hour
        
        # Submit LLM request at 1+ minutes past the hour, but only once per hour
        if last_llm_request_hour is None:
            last_llm_request_hour = current_hour
        elif current_minute >= 58 and last_llm_request_hour != current_hour:
            logger.info(f"1+ minutes past hour detected ({current_hour}:{current_minute:02d}), submitting LLM request...")
            alpha()
            last_llm_request_hour = current_hour

        time.sleep(60)  # Sleep for 1 minute
