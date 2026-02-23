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

    # Get SOL price and balance for max_buy calculations
    sol_mint = TOKEN_ADDRESSES["SOL"]
    sol_price_usd = fetcher.get_current_price(sol_mint)
    sol_balance = balances.get(sol_mint, 0)
    
    # Available SOL for buying (reserve 0.01 SOL for transaction fees)
    available_sol_balance = max(0, sol_balance - 0.01)
    available_sol_value_usd = available_sol_balance * sol_price_usd if sol_price_usd is not None else 0

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

    # Add max_buy and max_sell for each token
    ret_with_limits = {}
    for sym, data in ret_filtered.items():
        # max_sell is just the current balance
        data["max_sell"] = data["balance"]
        
        # max_buy is calculated based on available SOL balance
        if data["usd_price"] is not None and data["usd_price"] > 0 and sol_price_usd is not None and sol_price_usd > 0:
            # Calculate token price in SOL terms
            token_price_in_sol = data["usd_price"] / sol_price_usd
            data["max_buy"] = available_sol_balance / token_price_in_sol
        else:
            data["max_buy"] = 0

        ret_with_limits[sym] = data

    print("Balances with limits:", ret_with_limits)
    return ret_with_limits, total_value
