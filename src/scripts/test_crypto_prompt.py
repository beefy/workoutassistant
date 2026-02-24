from llm.prompts import build_crypto_prompt
from utils.crypto_indicators import get_all_token_indicators


indicators = get_all_token_indicators()
prompt = build_crypto_prompt("None", "None", indicators)
print(prompt)
