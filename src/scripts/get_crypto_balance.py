from utils.crypto_balance_with_value import get_crypto_balances_with_value, TOKEN_ADDRESSES
from utils.crypto_balance import get_crypto_balances

# Simple version - just get balances without prices
print("=== CRYPTO BALANCES (without USD values) ===")
try:
    balances = get_crypto_balances()
    for mint, balance in balances.items():
        print(f"{mint}: {balance}")
    print(f"\nTotal tokens found: {len(balances)}")
except Exception as e:
    print(f"Error getting balances: {e}")

# For USD values, you need to pass indicators data
# This would require fetching from the tracking API or calculating indicators
print("\n=== TO GET USD VALUES ===")
print("You need to provide indicators data to get_crypto_balances_with_value(indicators)")
print("See usage in other files like trading_strategy.py or sell_all.py")
