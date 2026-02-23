import os
import requests
import time
from typing import Dict, Optional, Union
from decimal import Decimal
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Commitment
import base64
import json
from utils.crypto_balance import get_sol_balance

# Solana token addresses (mainnet)
TOKEN_ADDRESSES = {
    "SOL": "So11111111111111111111111111111111111111112",  # Wrapped SOL (use this for trading)
    "WSOL": "So11111111111111111111111111111111111111112",  # Wrapped SOL
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "PYTH": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
}

# Token decimals for proper amount calculation
TOKEN_DECIMALS = {
    "SOL": 9,
    "WSOL": 9,
    "USDC": 6,
    "JUP": 6,
    "PYTH": 6,
    "RAY": 6,
    "JTO": 9,
    "BONK": 5,
    "WIF": 6
}

# Jupiter API endpoints - Updated for 2026
JUPITER_API_BASE = "https://api.jup.ag"
JUPITER_QUOTE_ENDPOINT = f"{JUPITER_API_BASE}/swap/v1/quote"
JUPITER_SWAP_ENDPOINT = f"{JUPITER_API_BASE}/swap/v1/swap"
JUPITER_PRICE_ENDPOINT = f"{JUPITER_API_BASE}/price/v3"

# def get_token_decimals(client, mint_address: str) -> int:
#     mint_pubkey = Pubkey.from_string(mint_address)
#     resp = client.get_token_supply(mint_pubkey)
#     return resp.value.decimals

def get_api_headers():
    """Get headers with API key for Jupiter API"""
    api_key = os.getenv('JUPITER_API_KEY')
    if not api_key:
        print("⚠️  Warning: JUPITER_API_KEY not set. API may be rate limited.")
        return {}
    return {'x-api-key': api_key}

class CryptoTrader:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        """
        Initialize the crypto trader.
        
        Args:
            rpc_url: Solana RPC endpoint URL
        
        Environment Variables Required:
            SOLANA_PRIVATE_KEY: Base58 encoded private key for the wallet
            JUPITER_API_KEY: Jupiter API key for authenticated requests (optional but recommended)
        """
        private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if not private_key:
            raise ValueError("SOLANA_PRIVATE_KEY environment variable is required")
        
        try:
            self.keypair = Keypair.from_base58_string(private_key)
        except Exception as e:
            raise ValueError(f"Invalid SOLANA_PRIVATE_KEY format: {e}")
        
        # Initialize client with proper commitment level
        self.client = Client(rpc_url, commitment=Commitment("confirmed"), timeout=30)
        self.wallet_address = str(self.keypair.pubkey())
        
        print(f"🎯 Wallet address: {self.wallet_address}")
    
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
            "restrictIntermediateTokens": "true"  # Must be string "true", not boolean
        }
        
        try:
            headers = get_api_headers()
            response = requests.get(JUPITER_QUOTE_ENDPOINT, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get quote from Jupiter API: {e}")
    
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
            
            # Additional parameters to optimize for transaction landing (2026 API)
            "dynamicComputeUnitLimit": True,
            "dynamicSlippage": True,
            "prioritizationFeeLamports": {
                "priorityLevelWithMaxLamports": {
                    "maxLamports": 1000000,  # Max 1 SOL worth of priority fees
                    "priorityLevel": "high"  # Can be: low, medium, high, veryHigh
                }
            }
        }
        
        try:
            headers = get_api_headers()
            headers['Content-Type'] = 'application/json'  # Required for POST requests
            response = requests.post(JUPITER_SWAP_ENDPOINT, json=swap_payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            swap_response = response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute swap via Jupiter API: {e}")
        
        # Check if swap response has the expected transaction data
        if "swapTransaction" not in swap_response:
            raise Exception(f"Jupiter API response missing 'swapTransaction' field. Response: {swap_response}")
        
        # Deserialize the transaction with better error handling
        try:
            transaction_data = swap_response["swapTransaction"]
            
            # Validate transaction data
            if not transaction_data or len(transaction_data) == 0:
                raise Exception("Empty transaction data received from Jupiter API")
            
            print(f"📦 Transaction data length: {len(transaction_data)} characters")
            
            # Decode base64 transaction data
            transaction_bytes = base64.b64decode(transaction_data)
            print(f"🔍 Decoded transaction length: {len(transaction_bytes)} bytes")
            
            # Deserialize as VersionedTransaction (Jupiter uses this format)
            transaction = VersionedTransaction.from_bytes(transaction_bytes)
            print("✅ VersionedTransaction deserialized successfully")
                
        except Exception as deserialize_error:
            raise Exception(f"Failed to deserialize transaction: {deserialize_error}. Transaction data length: {len(transaction_data) if 'transaction_data' in locals() else 'unknown'}")
        
        # Sign and send the transaction
        try:
            print("🚀 Sending transaction to Solana network...")
            
            # Sign the VersionedTransaction
            print("📝 Signing VersionedTransaction...")
            
            # Deserialize
            transaction = VersionedTransaction.from_bytes(transaction_bytes)

            # Create a NEW signed transaction
            signed_transaction = VersionedTransaction(
                transaction.message,
                [self.keypair]
            )

            # signed_transaction = transaction
            
            # Send the transaction with proper options
            tx_opts = TxOpts(
                skip_preflight=False,  # Set to True if having preflight issues
                preflight_commitment=Commitment("confirmed"),
                max_retries=3
            )
            
            result = self.client.send_transaction(
                signed_transaction, 
                opts=tx_opts
            )
            
            # Check if transaction was successful
            if hasattr(result, 'value') and result.value:
                print("✅ Transaction sent successfully")
                signature = str(result.value)
            else:
                raise Exception(f"Transaction failed: {result}")
                
        except Exception as send_error:
            # If preflight failed, try with skip_preflight=True
            if "preflight" in str(send_error).lower():
                try:
                    print("⚠️  Preflight failed, retrying with skip_preflight=True...")
                    tx_opts_skip = TxOpts(
                        skip_preflight=True,
                        preflight_commitment=Commitment("confirmed"),
                        max_retries=3
                    )
                    result = self.client.send_transaction(
                        signed_transaction,
                        opts=tx_opts_skip
                    )
                    if hasattr(result, 'value') and result.value:
                        print("✅ Transaction sent successfully (with skip_preflight)")
                        signature = str(result.value)
                    else:
                        raise Exception(f"Transaction failed even with skip_preflight: {result}")
                except Exception as retry_error:
                    raise Exception(f"Failed to send transaction even with skip_preflight: {retry_error}")
            else:
                raise Exception(f"Failed to send transaction: {send_error}")
        
        return {
            "signature": signature,
            "quote": quote,
            "transaction": transaction_data,
            "lastValidBlockHeight": swap_response.get("lastValidBlockHeight"),
            "prioritizationFeeLamports": swap_response.get("prioritizationFeeLamports"),
            "computeUnitLimit": swap_response.get("computeUnitLimit"),
            "dynamicSlippageReport": swap_response.get("dynamicSlippageReport")
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
        JUPITER_API_KEY: Jupiter API key for authenticated requests (optional but recommended)
    
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
    
    sol_balance = get_sol_balance()

    trader = CryptoTrader(rpc_url)
    print(f"Current SOL balance: {sol_balance:.6f} SOL")
    minimum_sol_balance = Decimal('0.01')  # Keep at least 0.01 SOL for transaction fees
    # Don't allow buying if it would exceed balance
    if action.lower() == 'buy':
        if Decimal(str(amount)) > Decimal(str(sol_balance - minimum_sol_balance)):
            raise ValueError(f"Insufficient SOL balance to buy {amount} {token_symbol}. Current balance: {sol_balance:.6f} SOL")
    
    try:
        if action.lower() == 'buy':
            # Buy token with SOL
            input_token = "SOL"
            output_token = token_symbol.upper()
            # Convert SOL amount to lamports using correct decimals
            sol_decimals = TOKEN_DECIMALS["SOL"]
            amount_lamports = int(Decimal(str(amount)) * Decimal(10 ** sol_decimals))
            
        else:  # sell
            # Sell token for SOL
            input_token = token_symbol.upper()
            output_token = "SOL"
            # Use the correct decimals for the input token
            token_decimals = TOKEN_DECIMALS.get(input_token, 6)  # Fallback to 6 if not found
            amount_lamports = int(Decimal(str(amount)) * Decimal(10 ** token_decimals))
        
        print(f"Getting quote for {action} {amount} {input_token} -> {output_token}")
        
        # Get quote
        quote = trader.get_quote(input_token, output_token, amount_lamports)
        
        if not quote:
            raise Exception("Failed to get quote from Jupiter API")
        
        # Display quote information with correct decimal handling
        input_decimals = TOKEN_DECIMALS.get(input_token, 6)
        output_decimals = TOKEN_DECIMALS.get(output_token, 6)
        
        input_amount = int(quote["inAmount"]) / (10 ** input_decimals)
        output_amount = int(quote["outAmount"]) / (10 ** output_decimals)
        
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

