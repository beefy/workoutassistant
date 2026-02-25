import time
import datetime

from llm.prompts import build_crypto_prompt
from utils.tracking_api import login, refresh_indicators, get_indicators, get_indicator_cache_stats
import os

token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
if not token:
    print("Failed to log in to tracking API. Please check your credentials.")
    exit(1)

cache_stats_before = get_indicator_cache_stats(token)
print("Cache stats before refresh:", cache_stats_before)

newest_entry = cache_stats_before['newest_entry']
print("Newest cache entry timestamp:", newest_entry)

# refresh if cache is older than 1 hour
if (datetime.datetime.now(datetime.UTC) - datetime.datetime.fromisoformat(newest_entry)).total_seconds() > 3600:
    print("Cache is older than 1 hour, refreshing indicators...")
    refresh_indicators(token)
else:
    print("Cache is fresh, no need to refresh indicators.")

cache_stats_after = get_indicator_cache_stats(token)
print("Cache stats after refresh:", cache_stats_after)

indicators = get_indicators(token)
print("Fetched indicators:", indicators)

prompt = build_crypto_prompt("None", "None", indicators)
print(prompt)
