from utils.crypto_balance_with_value import get_crypto_balances_with_value

# TODO: get indicators data from tracking API and pass it to the balance function for price reference

balance, total_usd_value = get_crypto_balances_with_value()
print(balance)
print(f"Total USD Value: ${total_usd_value:.2f}")
