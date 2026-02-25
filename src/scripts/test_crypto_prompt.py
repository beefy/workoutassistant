import time

from llm.prompts import build_crypto_prompt
from utils.tracking_api import login, refresh_indicators, get_indicators, get_indicator_cache_stats
import os

token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
if not token:
    print("Failed to log in to tracking API. Please check your credentials.")
    exit(1)

cache_stats_before = get_indicator_cache_stats(token)
print("Cache stats before refresh:", cache_stats_before)

refresh_indicators(token)
print("Waiting 3 minutes for indicators to refresh...")
time.sleep(180)

cache_stats_after = get_indicator_cache_stats(token)
print("Cache stats after refresh:", cache_stats_after)

indicators = get_indicators(token)
print("Fetched indicators:", indicators)

prompt = build_crypto_prompt("None", "None", indicators)
print(prompt)
