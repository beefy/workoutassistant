from utils.crypto_balance import get_crypto_balances
from clients.crypto_data import BirdeyeDataFetcher


fetcher = BirdeyeDataFetcher()
balances = get_crypto_balances()
ret = {}

for mint, balance in balances.items():
    usd = fetcher.get_current_price(mint)
    ret[mint] = {
        "balance": balance,
        "usd_price": usd,
        "usd_value": balance * usd if usd is not None else None
    }

print(ret)

print("Total value USD:", sum(item["usd_value"] for item in ret.values() if item["usd_value"] is not None))
