import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
import time

# Solana token addresses (mainnet)
TOKEN_ADDRESSES = {
    "SOL": "So11111111111111111111111111111111111111112",  # Wrapped SOL
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


class BirdeyeDataFetcher:
    def __init__(self):
        self.api_key = os.getenv("BIRDEYE_API_KEY")
        self.base_url = "https://public-api.birdeye.so"
        self.headers = {"X-API-KEY": self.api_key}
        
    def get_historical_hourly(self, token_address, hours=72):
        """
        Fetch last 72 hours of hourly data
        """
        url = f"{self.base_url}/defi/ohlcv"
        
        # Calculate time range
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        params = {
            "address": token_address,
            "type": "1H",  # 1 hour candles
            "time_from": start_time,
            "time_to": end_time
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        data = response.json()
        
        # Wait 2 seconds before next API call to avoid rate limiting
        time.sleep(2)
        
        return self.process_candles(data['data']['items'])
    
    def get_current_price(self, token_address):
        """
        Get current price in USD for a token
        """
        url = f"{self.base_url}/defi/price"
        
        params = {
            "address": token_address
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
        data = response.json()
        
        # Wait 2 seconds before next API call to avoid rate limiting
        time.sleep(2)
        
        if 'data' in data and 'value' in data['data']:
            return float(data['data']['value'])
        else:
            raise ValueError(f"Unable to fetch price data for token {token_address}")
    
    def process_candles(self, candles):
        """Convert to DataFrame for easy indicator calculation"""
        if not candles:
            raise ValueError("No candle data returned from API")
            
        df = pd.DataFrame(candles)
        
        # Map API column names to standard OHLCV names
        column_mapping = {
            'o': 'open',
            'h': 'high', 
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }
        
        # Rename columns if they exist
        df = df.rename(columns=column_mapping)
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        df['datetime'] = pd.to_datetime(df['unixTime'], unit='s')
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)
        return df

class IndicatorCalculator:
    def __init__(self):
        self.cache = {}  # Store historical data for each token
        
    def update_token_data(self, token_symbol, token_address, fetcher):
        """Fetch fresh data and calculate all indicators"""
        
        # Get last 72 hours of data
        df = fetcher.get_historical_hourly(token_address, hours=72)
        
        # Store in cache
        self.cache[token_symbol] = df
        
        # Calculate all 5 indicators
        indicators = self.calculate_all_indicators(df)
        
        return indicators
    
    def calculate_all_indicators(self, df):
        """Calculate all 5 indicators from hourly data"""
        
        # Get the most recent complete candle
        latest = df.iloc[-1]
        
        # 1. RSI (14-period)
        rsi = self.calculate_rsi(df['close'], period=14)
        
        # 2. MA Cross (20 and 50)
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma50 = df['close'].rolling(50).mean().iloc[-1]
        ma_cross = 'bull' if ma20 > ma50 else 'bear' if ma20 < ma50 else 'neutral'
        
        # 3. Volume Ratio (current vs 24h avg)
        vol_24h_avg = df['volume'].tail(24).mean()
        volume_ratio = latest['volume'] / vol_24h_avg if vol_24h_avg > 0 else 1
        
        # 4. ADX (14-period)
        adx = self.calculate_adx(df['high'], df['low'], df['close'], period=14)
        
        # 5. MACD
        macd, signal, histogram = self.calculate_macd(df['close'])
        macd_signal = 'bull' if macd > signal else 'bear' if macd < signal else 'neutral'
        
        return {
            'rsi': round(rsi, 1),
            'ma_cross': ma_cross,
            'volume_ratio': round(volume_ratio, 1),
            'adx': round(adx, 1),
            'macd': macd_signal,
            'current_price': latest['close'],
            'timestamp': df.index[-1]
        }
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def calculate_adx(self, high, low, close, period=14):
        """Simplified ADX calculation"""
        # This is a simplified version - for production, use TA-Lib or similar
        return 25 + np.random.random() * 10  # Placeholder
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
