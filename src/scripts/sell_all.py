from utils.tracking_api import login, get_indicators
from utils.crypto_balance_with_value import get_crypto_balances_with_value
from clients.crypto_trade import execute_crypto_trade
import time

import os

token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
if not token:
    print("Failed to log in to tracking API. Please check your credentials.")
    exit(1)

# refresh_indicators(token)

indicators = get_indicators(token)

print("Fetched indicators:", indicators)

balances, max_value = get_crypto_balances_with_value(indicators['indicators'])

print("Crypto balances with USD value:", balances)

# confirm before selling
confirm = input(f"Total USD value of crypto holdings: ${max_value:.2f}. Do you want to sell all eligible crypto holdings? (yes/no): ")
if confirm.lower() != "yes":
    print("Aborting sell all operation.")
    exit(0)

for balance in balances:
    print(f"{balance}: {balances[balance]['max_sell']}")
    if balances[balance]['max_sell'] > 0:
        time.sleep(5)
        execute_crypto_trade(balance, "sell", balances[balance]['max_sell'], indicators['indicators'])
