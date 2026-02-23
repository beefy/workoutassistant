from utils.crypto_balance import get_crypto_balances
from clients.crypto_data import BirdeyeDataFetcher

TOKEN_ADDRESSES = {
    "SOL": "So11111111111111111111111111111111111111112",  # Wrapped SOL
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "PYTH": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
}

# Reverse mapping for easy lookup
ADDRESS_TO_SYMBOL = {addr: sym for sym, addr in TOKEN_ADDRESSES.items()}

def get_crypto_balances_with_value():
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
    total_value = sum(item["usd_value"] for item in ret.values() if item["usd_value"] is not None)
    print("Total value USD:", total_value)

    # Replace mint addresses with token symbols for cleaner output
    ret_cleaned = {}
    for mint, data in ret.items():
        symbol = ADDRESS_TO_SYMBOL.get(mint, mint)
        ret_cleaned[symbol] = data
    
    # Filter out tokens not in the list
    ret_filtered = {sym: data for sym, data in ret_cleaned.items() if sym in TOKEN_ADDRESSES}

    # Add 0 value tokens that aren't in the balances but are in the TOKEN_ADDRESSES
    for sym in TOKEN_ADDRESSES.keys():
        if sym not in ret_filtered:
            ret_filtered[sym] = {
                "balance": 0,
                "usd_price": fetcher.get_current_price(TOKEN_ADDRESSES[sym]),
                "usd_value": 0
            }

    return ret_filtered, total_value
