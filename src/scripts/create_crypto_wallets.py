#!/usr/bin/env python3
"""
Crypto Wallet Generator
Creates new wallets for Ethereum and Solana blockchains.
"""

import os
import json
import secrets
from typing import Dict, Optional
from datetime import datetime
import logging

from eth_account import Account
from eth_account.hdaccount import generate_mnemonic
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from mnemonic import Mnemonic

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WalletGenerator:
    """Generates crypto wallets for different blockchain networks."""
    
    def __init__(self):
        self.ethereum_account = Account()
        self.mnemonic_generator = Mnemonic("english")
    
    def generate_ethereum_wallet(self, mnemonic: Optional[str] = None) -> Dict[str, str]:
        """
        Generate an Ethereum wallet.
        
        Args:
            mnemonic: Optional BIP39 mnemonic phrase. If None, generates a new one.
            
        Returns:
            Dictionary containing private key, public key, address, and mnemonic.
        """
        try:
            if mnemonic is None:
                # Generate a new mnemonic phrase
                mnemonic = generate_mnemonic(num_words=12, lang="english")
            
            # Enable HD wallet functionality
            Account.enable_unaudited_hdwallet_features()
            
            # Create account from mnemonic
            account = Account.from_mnemonic(mnemonic)
            
            return {
                "chain": "ethereum",
                "address": account.address,
                "private_key": account.key.hex(),
                "public_key": account._key_obj.public_key.to_hex(),
                "mnemonic": mnemonic,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating Ethereum wallet: {e}")
            raise
    
    def generate_solana_wallet(self) -> Dict[str, str]:
        """
        Generate a Solana wallet.
        
        Returns:
            Dictionary containing private key, public key, address, and other details.
        """
        try:
            # Generate a new keypair
            keypair = Keypair()
            
            # Get the public key (address)
            public_key = keypair.pubkey()
            
            # Convert private key to different formats
            private_key_bytes = bytes(keypair)
            
            return {
                "chain": "solana",
                "address": str(public_key),
                "private_key": list(private_key_bytes),
                "private_key_hex": private_key_bytes.hex(),
                "private_key_base58": str(keypair),  # Base58 format for crypto_trade.py
                "public_key": str(public_key),
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating Solana wallet: {e}")
            raise
    
    def generate_wallets_from_seed(self, seed: Optional[str] = None, count: int = 1) -> Dict[str, list]:
        """
        Generate multiple wallets from the same seed.
        
        Args:
            seed: Optional seed phrase. If None, generates a new one.
            count: Number of wallet pairs to generate.
            
        Returns:
            Dictionary containing lists of Ethereum and Solana wallets.
        """
        wallets = {
            "ethereum": [],
            "solana": [],
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "count": count,
                "seed_provided": seed is not None
            }
        }
        
        # Generate Ethereum wallets (can use same mnemonic for multiple derivations)
        base_mnemonic = seed or generate_mnemonic(num_words=12, lang="english")
        
        for i in range(count):
            # For Ethereum, we can derive multiple accounts from same mnemonic
            eth_wallet = self.generate_ethereum_wallet(base_mnemonic)
            wallets["ethereum"].append(eth_wallet)
            
            # For Solana, generate independent wallets
            sol_wallet = self.generate_solana_wallet()
            wallets["solana"].append(sol_wallet)
        
        return wallets
    
    def save_wallets_to_file(self, wallets: Dict, filename: str = None, 
                           encrypted: bool = False, password: str = None) -> str:
        """
        Save wallets to a JSON file.
        
        Args:
            wallets: Dictionary containing wallet information.
            filename: Output filename. If None, generates timestamp-based name.
            encrypted: Whether to encrypt the file (basic encryption).
            password: Password for encryption (required if encrypted=True).
            
        Returns:
            String path to the saved file.
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_wallets_{timestamp}.json"
        
        # Ensure we have a secure directory
        wallets_dir = os.path.join(os.path.expanduser("~"), ".crypto_wallets")
        os.makedirs(wallets_dir, exist_ok=True)
        os.chmod(wallets_dir, 0o700)  # Owner read/write/execute only
        
        filepath = os.path.join(wallets_dir, filename)
        
        wallet_data = {
            "wallets": wallets,
            "security_warning": "KEEP THIS FILE SECURE! Contains private keys.",
            "created_at": datetime.utcnow().isoformat()
        }
        
        if encrypted and password:    
            # Derive key from password
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Encrypt the data
            f = Fernet(key)
            encrypted_data = f.encrypt(json.dumps(wallet_data).encode())
            
            # Save encrypted data with salt
            encrypted_wallet_data = {
                "encrypted": True,
                "salt": base64.b64encode(salt).decode(),
                "data": base64.b64encode(encrypted_data).decode()
            }
            
            with open(filepath, 'w') as f:
                json.dump(encrypted_wallet_data, f, indent=2)
        else:
            # Save as plain JSON
            with open(filepath, 'w') as f:
                json.dump(wallet_data, f, indent=2)
        
        # Set file permissions to owner read/write only
        os.chmod(filepath, 0o600)
        
        logger.info(f"Wallets saved to: {filepath}")
        return filepath

def print_wallet_info(wallets: Dict):
    """Print wallet information in a formatted way."""
    print("\n" + "="*80)
    print("🔐 CRYPTO WALLETS GENERATED")
    print("="*80)
    print("⚠️  WARNING: Keep your private keys and mnemonic phrases secure!")
    print("⚠️  Never share them with anyone or store them online.")
    print("="*80)
    
    if isinstance(wallets.get("ethereum"), list):
        # Multiple wallets format
        for i, eth_wallet in enumerate(wallets["ethereum"]):
            print(f"\n📱 ETHEREUM WALLET #{i+1}")
            print(f"Address:     {eth_wallet['address']}")
            print(f"Private Key: {eth_wallet['private_key'][:10]}...{eth_wallet['private_key'][-8:]}")
            if "mnemonic" in eth_wallet:
                print(f"Mnemonic:    {eth_wallet['mnemonic']}")
        
        for i, sol_wallet in enumerate(wallets["solana"]):
            print(f"\n🌟 SOLANA WALLET #{i+1}")
            print(f"Address:        {sol_wallet['address']}")
            print(f"Private Key:    {sol_wallet['private_key_hex'][:10]}...{sol_wallet['private_key_hex'][-8:]} (hex)")
            print(f"Base58 Key:     {sol_wallet['private_key_base58'][:10]}...{sol_wallet['private_key_base58'][-8:]} (for SOLANA_PRIVATE_KEY)")
    else:
        # Single wallet format
        if wallets.get("chain") == "ethereum":
            print(f"\n📱 ETHEREUM WALLET")
            print(f"Address:     {wallets['address']}")
            print(f"Private Key: {wallets['private_key'][:10]}...{wallets['private_key'][-8:]}")
            if "mnemonic" in wallets:
                print(f"Mnemonic:    {wallets['mnemonic']}")
        elif wallets.get("chain") == "solana":
            print(f"\n🌟 SOLANA WALLET")
            print(f"Address:        {wallets['address']}")
            print(f"Private Key:    {wallets['private_key_hex'][:10]}...{wallets['private_key_hex'][-8:]} (hex)")
            print(f"Base58 Key:     {wallets['private_key_base58'][:10]}...{wallets['private_key_base58'][-8:]} (for SOLANA_PRIVATE_KEY)")
    
    print("\n" + "="*80)


def main():
    """Main function to demonstrate wallet generation."""
    generator = WalletGenerator()

    # Generate 1 Ethereum wallet and 3 Solana wallets
    wallet_eth = generator.generate_ethereum_wallet()
    print("Ethereum wallet generated:")
    print_wallet_info(wallet_eth)
    wallet_sol_1 = generator.generate_solana_wallet()
    print("Solana wallet 1 generated:")
    print_wallet_info(wallet_sol_1)
    wallet_sol_2 = generator.generate_solana_wallet()
    print("Solana wallet 2 generated:")
    print_wallet_info(wallet_sol_2)
    wallet_sol_3 = generator.generate_solana_wallet()
    print("Solana wallet 3 generated:")
    print_wallet_info(wallet_sol_3)

    # Save wallets to file
    wallets = {
        "ethereum": [wallet_eth],
        "solana": [wallet_sol_1, wallet_sol_2, wallet_sol_3]
    }
    generator.save_wallets_to_file(wallets, encrypted=False)


if __name__ == "__main__":
    # Security warning
    print("⚠️  SECURITY WARNING:")
    print("This script generates real crypto wallets with private keys.")
    print("Keep your private keys secure and never share them!")
    print("Consider running this on an offline/air-gapped computer for maximum security.")

    main()
