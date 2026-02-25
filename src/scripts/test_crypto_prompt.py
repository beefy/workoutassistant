from time import time

from llm.prompts import build_crypto_prompt
from utils.crypto_indicators import get_all_token_indicators

start_time = time.time()
indicators = get_all_token_indicators()
end_time = time.time()
print(f"Data fetching and indicator calculation took {end_time - start_time:.2f} seconds")

prompt = build_crypto_prompt("None", "None", indicators)
print(prompt)
