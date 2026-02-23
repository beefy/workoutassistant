
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
import os


def get_sol_balance():
    wallet_address = os.getenv("SOLANA_ADDRESS")
    client = Client("https://api.mainnet-beta.solana.com")
    response = client.get_balance(Pubkey.from_string(wallet_address))
    lamports = response.value
    sol_balance = lamports / 1_000_000_000
    return sol_balance


def get_crypto_balances():
    wallet_address = os.getenv("SOLANA_ADDRESS")
    ret = {}

    client = Client("https://api.mainnet-beta.solana.com")

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

    return ret