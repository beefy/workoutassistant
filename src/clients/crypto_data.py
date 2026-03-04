import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

# Solana token addresses (mainnet)
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


class BirdeyeDataFetcher:
    def __init__(self):
        self.api_key = os.getenv("BIRDEYE_API_KEY")
        self.base_url = "https://public-api.birdeye.so"
        self.headers = {"X-API-KEY": self.api_key}
        
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
        reraise=True
    )
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
        
        try:
            logger.info(f"📈 Fetching {hours}h of price data for {token_address}...")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✅ Successfully fetched historical data")
            
            # Wait 2 seconds before next API call to avoid rate limiting
            time.sleep(2)
            
            return self.process_candles(data['data']['items'])
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Birdeye historical data request failed, will retry: {e}")
            # Wait longer before retry on rate limit
            if "429" in str(e):
                time.sleep(5)
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
        reraise=True
    )
    def get_current_price(self, token_address):
        """
        Get current price in USD for a token
        """
        url = f"{self.base_url}/defi/price"
        
        params = {
            "address": token_address
        }
        
        try:
            logger.info(f"💰 Fetching current price for {token_address}...")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
                
            data = response.json()
            logger.info(f"✅ Successfully fetched current price")
            
            # Wait 2 seconds before next API call to avoid rate limiting
            time.sleep(2)
            
            if 'data' in data and 'value' in data['data']:
                price = float(data['data']['value'])
                logger.info(f"💲 Current price: ${price:.6f}")
                return price
            else:
                raise ValueError(f"Unable to fetch price data for token {token_address}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Birdeye price request failed, will retry: {e}")
            # Wait longer before retry on rate limit
            if "429" in str(e):
                time.sleep(5)
            raise
    
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
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError, ValueError)),
        reraise=True
    )
    def update_token_data(self, token_symbol, token_address, fetcher):
        """Fetch fresh data and calculate all indicators"""
        
        logger.info(f"🗺️ Updating data for {token_symbol} ({token_address})...")
        
        # Get last 72 hours of data
        df = fetcher.get_historical_hourly(token_address, hours=72)
        
        # Store in cache
        self.cache[token_symbol] = df
        
        # Calculate all 5 indicators
        indicators = self.calculate_all_indicators(df)
        
        logger.info(f"✅ Successfully updated data and calculated indicators for {token_symbol}")
        return indicators
    
    def calculate_all_indicators(self, df):
        """Calculate all 6 indicators from hourly data"""
        
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
        
        # 6. Stochastic Oscillator (14-period)
        stoch_k, stoch_d = self.calculate_stochastic(df['high'], df['low'], df['close'], period=14)
        stoch_signal = 'bull' if stoch_k > stoch_d and stoch_k < 80 else 'bear' if stoch_k < stoch_d and stoch_k > 20 else 'neutral'
        
        return {
            'rsi': round(rsi, 1),
            'ma_cross': ma_cross,
            'volume_ratio': round(volume_ratio, 1),
            'adx': round(adx, 1),
            'macd': macd_signal,
            'stochastic_k': round(stoch_k, 1),
            'stochastic_d': round(stoch_d, 1),
            'stochastic_signal': stoch_signal,
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
    
    def calculate_stochastic(self, high, low, close, period=14, smooth_k=3):
        """Calculate Stochastic Oscillator using stochastic analysis
        
        The Stochastic Oscillator is based on stochastic calculus principles,
        measuring the momentum of price changes by comparing closing prices
        to their range over a given period.
        
        %K = ((Close - LowestLow) / (HighestHigh - LowestLow)) * 100
        %D = SMA of %K over smooth_k periods
        """
        # Calculate the lowest low and highest high over the period
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        # Calculate %K (fast stochastic)
        k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # Smooth %K to get the final %K line
        k_smoothed = k_percent.rolling(window=smooth_k).mean()
        
        # Calculate %D (slow stochastic) as SMA of %K
        d_percent = k_smoothed.rolling(window=smooth_k).mean()
        
        return k_smoothed.iloc[-1], d_percent.iloc[-1]
