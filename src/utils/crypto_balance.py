
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
import os
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from solana.exceptions import SolanaRpcException
import httpx
import logging

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((SolanaRpcException, httpx.TimeoutException, httpx.HTTPStatusError, ConnectionError)),
    reraise=True
)
def get_sol_balance():
    wallet_address = os.getenv("SOLANA_ADDRESS")
    client = Client("https://api.mainnet-beta.solana.com")
    logger.info(f"🔌 Fetching SOL balance for wallet: {wallet_address}")
    response = client.get_balance(Pubkey.from_string(wallet_address))
    lamports = response.value
    sol_balance = lamports / 1_000_000_000
    logger.info(f"💰 SOL balance: {sol_balance:.6f}")
    return sol_balance


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((SolanaRpcException, httpx.TimeoutException, httpx.HTTPStatusError, ConnectionError)),
    reraise=True
)
def get_crypto_balances():
    wallet_address = os.getenv("SOLANA_ADDRESS")
    ret = {}

    client = Client("https://api.mainnet-beta.solana.com")
    logger.info(f"🔌 Fetching token balances for wallet: {wallet_address}")

    ret["So11111111111111111111111111111111111111112"] = get_sol_balance()

    response = client.get_token_accounts_by_owner_json_parsed(
        Pubkey.from_string(wallet_address),
        TokenAccountOpts(program_id=Pubkey.from_string(
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  # SPL Token Program
        ))
    )

    for account in response.value:
        data = account.account.data.parsed["info"]
        mint = data["mint"]
        amount = int(data["tokenAmount"]["amount"])
        decimals = int(data["tokenAmount"]["decimals"])

        ui_amount = amount / (10 ** decimals)
        ret[mint] = ui_amount

    logger.info(f"🪙 Found {len(ret)} token balances")
    return ret