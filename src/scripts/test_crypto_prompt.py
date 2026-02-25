import datetime

from llm.prompts import build_crypto_prompt
from utils.crypto_indicators import get_all_token_indicators

start_time = datetime.datetime.now()
indicators = get_all_token_indicators()
end_time = datetime.datetime.now()
print(f"Data fetching and indicator calculation took {(end_time - start_time).total_seconds():.2f} seconds")

prompt = build_crypto_prompt("None", "None", indicators)
print(prompt)
