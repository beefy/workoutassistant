from utils.crypto_balance import get_crypto_balances
import logging
from utils.logging_config import setup_logging
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from solana.exceptions import SolanaRpcException
import httpx

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

TOKEN_ADDRESSES = {
    "SOL": "So11111111111111111111111111111111111111112",  # Wrapped SOL
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "PYTH": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
    "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
    "STEP": "StepAscQoEioFxxWGnh2sLBDFp9d8rvKz2Yp39iDpyT",
    "FIDA": "EchesyfXePKdLtoiZSL8pBe8Myagyy8ZRqsACNCFGnvp",
    "COPE": "8HGyAAB1yoM1ttS7pXjHMa3dukTFGQggnFFH3hJZgzQh",
    "SAMO": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    "MNGO": "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac",
    "ATLAS": "ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx"
}

# Reverse mapping for easy lookup
ADDRESS_TO_SYMBOL = {addr: sym for sym, addr in TOKEN_ADDRESSES.items()}

@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((SolanaRpcException, httpx.TimeoutException, httpx.HTTPStatusError, ConnectionError)),
    reraise=True
)
def get_crypto_balances_with_value(indicators):
    logger.info("🔄 Fetching crypto balances with USD values...")
    balances = get_crypto_balances()
    ret = {}

    for mint, balance in balances.items():
        # Get token symbol from mint address
        symbol = ADDRESS_TO_SYMBOL.get(mint, mint)
        
        # Get price from indicator data if available
        usd = indicators[symbol].get('current_price')
        
        ret[mint] = {
            "balance": balance,
            "usd_price": usd,
            "usd_value": balance * usd if usd is not None else None
        }

    logger.info(f"Crypto balances: {ret}")
    total_value = sum(item["usd_value"] for item in ret.values() if item["usd_value"] is not None)
    logger.info(f"Total value USD: {total_value}")
    logger.info("✅ Successfully calculated crypto balances with values")

    # Get SOL price and balance for max_buy calculations
    sol_mint = TOKEN_ADDRESSES["SOL"]
    sol_price_usd = indicators['SOL'].get('current_price')
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
            usd_price = None
            usd_price = indicators[sym].get('current_price')
            ret_filtered[sym] = {
                "balance": 0,
                "usd_price": usd_price,
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

    # Set max_buy and max_sell to 0 for SOL
    if "SOL" in ret_with_limits:
        ret_with_limits["SOL"]["max_buy"] = 0
        ret_with_limits["SOL"]["max_sell"] = 0

    logger.info(f"Balances with limits: {ret_with_limits}")
    return ret_with_limits, total_value
