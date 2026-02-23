import os
import requests
import time
from typing import Dict, Optional, Union
from decimal import Decimal
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.transaction import Transaction
import base64

# Solana token addresses (mainnet)
TOKEN_ADDRESSES = {
    "SOL": "11111111111111111111111111111111",  # Native SOL
    "WSOL": "So11111111111111111111111111111111111111112",  # Wrapped SOL
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "PYTH": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
    "HNT": "hntV2VhymNHF6M73ooYqF4BojGPDcSvHjjr13DMMG1F",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "POPCAT": "7GCihgDB8fe6CRTnW6sKY6j6L3yqLpEvZ1mW6dGcmK2L"
}

# Jupiter API endpoints
JUPITER_API_BASE = "https://quote-api.jup.ag/v6"
JUPITER_SWAP_ENDPOINT = f"{JUPITER_API_BASE}/swap"
JUPITER_QUOTE_ENDPOINT = f"{JUPITER_API_BASE}/quote"

class CryptoTrader:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        """
        Initialize the crypto trader.
        
        Args:
            rpc_url: Solana RPC endpoint URL
        
        Environment Variables Required:
            SOLANA_PRIVATE_KEY: Base58 encoded private key for the wallet
        """
        private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if not private_key:
            raise ValueError("SOLANA_PRIVATE_KEY environment variable is required")
        
        self.keypair = Keypair.from_base58_string(private_key)
        self.client = Client(rpc_url)
        self.wallet_address = str(self.keypair.pubkey())
    
    def get_quote(self, input_token: str, output_token: str, amount: Union[int, float, Decimal]) -> Dict:
        """
        Get a quote for a token swap.
        
        Args:
            input_token: Symbol of the token to sell
            output_token: Symbol of the token to buy
            amount: Amount to trade (in the smallest unit, e.g., lamports for SOL)
        
        Returns:
            Quote response from Jupiter API
        """
        if input_token not in TOKEN_ADDRESSES:
            raise ValueError(f"Unknown input token: {input_token}")
        if output_token not in TOKEN_ADDRESSES:
            raise ValueError(f"Unknown output token: {output_token}")
        
        input_mint = TOKEN_ADDRESSES[input_token]
        output_mint = TOKEN_ADDRESSES[output_token]
        
        # Convert to integer for API call
        amount_int = int(amount)
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_int,
            "slippageBps": 50,  # 0.5% slippage tolerance
            "swapMode": "ExactIn"
        }
        
        response = requests.get(JUPITER_QUOTE_ENDPOINT, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def execute_swap(self, quote: Dict) -> Dict:
        """
        Execute a swap using a Jupiter quote.
        
        Args:
            quote: Quote response from get_quote()
        
        Returns:
            Transaction signature and details
        """
        swap_payload = {
            "quoteResponse": quote,
            "userPublicKey": self.wallet_address,
            "wrapAndUnwrapSol": True,  # Automatically handle SOL wrapping/unwrapping
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": "auto"
        }
        
        response = requests.post(JUPITER_SWAP_ENDPOINT, json=swap_payload)
        response.raise_for_status()
        
        swap_response = response.json()
        
        # Deserialize the transaction
        transaction_data = swap_response["swapTransaction"]
        transaction_bytes = base64.b64decode(transaction_data)
        transaction = Transaction.deserialize(transaction_bytes)
        
        # Sign the transaction
        transaction.sign(self.keypair)
        
        # Send the transaction
        result = self.client.send_transaction(transaction)
        
        return {
            "signature": str(result.value),
            "quote": quote,
            "transaction": transaction_data
        }


def execute_crypto_trade(
    token_symbol: str,
    action: str,
    amount: Union[int, float, Decimal],
    rpc_url: str = "https://api.mainnet-beta.solana.com"
) -> Dict:
    """
    Execute a crypto trade on Solana using Jupiter DEX aggregator.
    
    Args:
        token_symbol: Symbol of the token to trade (e.g., 'JUP', 'BONK', 'PYTH')
        action: 'buy' to purchase token with SOL, 'sell' to sell token for SOL
        amount: Amount to trade
                - For 'buy': amount of SOL to spend (in SOL, e.g., 1.5 for 1.5 SOL)
                - For 'sell': amount of tokens to sell (in token units)
        rpc_url: Solana RPC endpoint URL
    
    Environment Variables Required:
        SOLANA_PRIVATE_KEY: Base58 encoded private key for the wallet
    
    Returns:
        Dictionary containing transaction details and results
        
    Example:
        # Set environment variable first:
        # export SOLANA_PRIVATE_KEY="your_private_key"
        
        # Buy 1.5 SOL worth of JUP tokens
        result = execute_crypto_trade(
            token_symbol="JUP", 
            action="buy",
            amount=1.5
        )
        
        # Sell 100 JUP tokens for SOL
        result = execute_crypto_trade(
            token_symbol="JUP",
            action="sell", 
            amount=100
        )
    """
    if action.lower() not in ['buy', 'sell']:
        raise ValueError("Action must be 'buy' or 'sell'")
    
    if token_symbol.upper() == 'SOL':
        raise ValueError("Cannot trade SOL for SOL. Use a different token symbol.")
    
    if token_symbol.upper() not in TOKEN_ADDRESSES:
        raise ValueError(f"Unsupported token: {token_symbol}. Supported tokens: {list(TOKEN_ADDRESSES.keys())}")
    
    trader = CryptoTrader(rpc_url)
    
    try:
        if action.lower() == 'buy':
            # Buy token with SOL
            input_token = "SOL"
            output_token = token_symbol.upper()
            # Convert SOL amount to lamports (1 SOL = 1,000,000,000 lamports)
            amount_lamports = int(Decimal(str(amount)) * Decimal("1000000000"))
            
        else:  # sell
            # Sell token for SOL
            input_token = token_symbol.upper()
            output_token = "SOL"
            # For most tokens, use the amount directly
            # Note: You may need to adjust decimal places based on token specifics
            amount_lamports = int(Decimal(str(amount)) * Decimal("1000000"))  # Assuming 6 decimals for most tokens
        
        print(f"Getting quote for {action} {amount} {input_token} -> {output_token}")
        
        # Get quote
        quote = trader.get_quote(input_token, output_token, amount_lamports)
        
        if not quote:
            raise Exception("Failed to get quote from Jupiter API")
        
        # Display quote information
        input_amount = int(quote["inAmount"]) / (10**9 if quote["inputMint"] == TOKEN_ADDRESSES["SOL"] else 10**6)
        output_amount = int(quote["outAmount"]) / (10**9 if quote["outputMint"] == TOKEN_ADDRESSES["SOL"] else 10**6)
        
        print(f"Quote: {input_amount:.6f} {input_token} -> {output_amount:.6f} {output_token}")
        print(f"Price impact: {quote.get('priceImpactPct', 'N/A')}%")
        
        # Execute the swap
        print("Executing trade...")
        result = trader.execute_swap(quote)
        
        print(f"Trade executed successfully!")
        print(f"Transaction signature: {result['signature']}")
        
        return {
            "success": True,
            "transaction_signature": result["signature"],
            "input_token": input_token,
            "output_token": output_token,
            "input_amount": input_amount,
            "output_amount": output_amount,
            "price_impact": quote.get("priceImpactPct"),
            "quote": quote
        }
        
    except Exception as e:
        error_msg = f"Trade execution failed: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "input_token": input_token if 'input_token' in locals() else None,
            "output_token": output_token if 'output_token' in locals() else None,
        }

