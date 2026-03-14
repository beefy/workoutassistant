import time

from utils.tracking_api import login, get_indicators, status_update
import os
from clients.crypto_trade import execute_crypto_trade
from utils.crypto_balance_with_value import get_crypto_balances_with_value
from utils.logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def process_indicators_alpha(indicators):
    """Process indicator data using momentum-focused strategy

    Alpha strategy prioritizes:
    - RSI (40% weight) - momentum oscillator
    - MACD (30% weight) - trend and momentum
    - Moving Average Cross (20% weight) - trend direction
    - Stochastic (10% weight) - momentum confirmation

    Example input:
    {'token_symbol': 'SOL', 'token_address': 'So11111111111111111111111111111111111111112', 'rsi': 55.2, 'ma_cross': 'bull', 'ma20': 90.6824, 'ma50': 87.5435, 'volume_ratio': 0.0, 'adx': None, 'macd': 'bear', 'macd_value': 1.187639, 'macd_signal_value': 1.426472, 'macd_histogram': -0.238833, 'stochastic_k': 39.6, 'stochastic_d': 46.1, 'stochastic_signal': 'bear', 'current_price': 90.7470565, 'volume_24h': 132743474.0, 'data_points': 73, 'data_start': '2026-03-02T01:00:00', 'data_end': '2026-03-05T01:00:00', 'timestamp': '2026-03-05T01:01:22.620859'}

    Args:
        indicators (dict): Indicator data for a specific token

    Returns:
        float: over 1 if buy signal, under 1 if sell signal. larger magnitude means stronger signal. 1 means hold.
    """
    signal_score = 0.0
    
    # RSI Analysis (40% weight)
    rsi = indicators.get('rsi')
    if rsi is not None:
        if rsi < 30:  # Oversold - strong buy
            signal_score += 0.8 * 0.4  # Strong buy signal
        elif rsi < 40:  # Moderately oversold
            signal_score += 0.4 * 0.4
        elif rsi > 70:  # Overbought - strong sell
            signal_score -= 0.8 * 0.4  # Strong sell signal
        elif rsi > 60:  # Moderately overbought
            signal_score -= 0.4 * 0.4
    
    # MACD Analysis (30% weight)
    macd_signal = indicators.get('macd')
    macd_histogram = indicators.get('macd_histogram')
    if macd_signal:
        if macd_signal == 'bull':
            signal_score += 0.6 * 0.3
        elif macd_signal == 'bear':
            signal_score -= 0.6 * 0.3
    
    # MACD histogram for momentum strength
    if macd_histogram is not None:
        if macd_histogram > 0:
            signal_score += min(abs(macd_histogram) * 0.1, 0.4) * 0.3
        else:
            signal_score -= min(abs(macd_histogram) * 0.1, 0.4) * 0.3
    
    # Moving Average Cross (20% weight)
    ma_cross = indicators.get('ma_cross')
    if ma_cross:
        if ma_cross == 'bull':
            signal_score += 0.5 * 0.2
        elif ma_cross == 'bear':
            signal_score -= 0.5 * 0.2
    
    # Stochastic Analysis (10% weight)
    stoch_signal = indicators.get('stochastic_signal')
    stoch_k = indicators.get('stochastic_k')
    if stoch_signal:
        if stoch_signal == 'bull':
            signal_score += 0.3 * 0.1
        elif stoch_signal == 'bear':
            signal_score -= 0.3 * 0.1
    
    # Additional confirmation from stochastic levels
    if stoch_k is not None:
        if stoch_k < 20:  # Oversold
            signal_score += 0.2 * 0.1
        elif stoch_k > 80:  # Overbought
            signal_score -= 0.2 * 0.1
    
    # Convert to final signal (centered around 1)
    final_signal = 1 + signal_score
    
    # Clamp between reasonable bounds
    return max(0.1, min(2.0, final_signal))


def process_indicators_beta(indicators):
    """Process indicator data using trend-following strategy

    Beta strategy prioritizes:
    - Moving Average Cross (35% weight) - primary trend direction
    - ADX (25% weight) - trend strength
    - Stochastic (20% weight) - entry/exit timing
    - Volume Ratio (15% weight) - confirmation
    - RSI (5% weight) - extreme level filter

    Example input:
    {'token_symbol': 'SOL', 'token_address': 'So11111111111111111111111111111111111111112', 'rsi': 55.2, 'ma_cross': 'bull', 'ma20': 90.6824, 'ma50': 87.5435, 'volume_ratio': 0.0, 'adx': None, 'macd': 'bear', 'macd_value': 1.187639, 'macd_signal_value': 1.426472, 'macd_histogram': -0.238833, 'stochastic_k': 39.6, 'stochastic_d': 46.1, 'stochastic_signal': 'bear', 'current_price': 90.7470565, 'volume_24h': 132743474.0, 'data_points': 73, 'data_start': '2026-03-02T01:00:00', 'data_end': '2026-03-05T01:00:00', 'timestamp': '2026-03-05T01:01:22.620859'}

    Args:
        indicators (dict): Indicator data for a specific token

    Returns:
        float: over 1 if buy signal, under 1 if sell signal. larger magnitude means stronger signal. 1 means hold.
    """
    signal_score = 0.0
    
    # Moving Average Cross Analysis (35% weight) - Primary trend
    ma_cross = indicators.get('ma_cross')
    ma20 = indicators.get('ma20')
    ma50 = indicators.get('ma50')
    current_price = indicators.get('current_price')
    
    if ma_cross:
        if ma_cross == 'bull':
            signal_score += 0.7 * 0.35
        elif ma_cross == 'bear':
            signal_score -= 0.7 * 0.35
    
    # Price position relative to MAs
    if current_price and ma20 and ma50:
        if current_price > ma20 > ma50:  # Strong uptrend
            signal_score += 0.3 * 0.35
        elif current_price < ma20 < ma50:  # Strong downtrend
            signal_score -= 0.3 * 0.35
    
    # ADX Analysis (25% weight) - Trend strength
    adx = indicators.get('adx')
    if adx is not None:
        if adx > 25:  # Strong trend
            trend_strength = min((adx - 25) / 50, 1.0)  # Normalize to 0-1
            if ma_cross == 'bull':
                signal_score += trend_strength * 0.6 * 0.25
            elif ma_cross == 'bear':
                signal_score -= trend_strength * 0.6 * 0.25
        elif adx < 20:  # Weak trend - reduce confidence
            signal_score *= 0.8
    
    # Stochastic Analysis (20% weight) - Timing
    stoch_signal = indicators.get('stochastic_signal')
    stoch_k = indicators.get('stochastic_k')
    stoch_d = indicators.get('stochastic_d')
    
    if stoch_signal:
        if stoch_signal == 'bull':
            signal_score += 0.5 * 0.2
        elif stoch_signal == 'bear':
            signal_score -= 0.5 * 0.2
    
    # Stochastic divergence for timing
    if stoch_k is not None and stoch_d is not None:
        if stoch_k > stoch_d and stoch_k < 80:  # Bullish momentum, not overbought
            signal_score += 0.3 * 0.2
        elif stoch_k < stoch_d and stoch_k > 20:  # Bearish momentum, not oversold
            signal_score -= 0.3 * 0.2
    
    # Volume Analysis (15% weight) - Confirmation
    volume_ratio = indicators.get('volume_ratio')
    if volume_ratio is not None:
        if volume_ratio > 1.5:  # High volume confirmation
            signal_score *= 1.2  # Amplify existing signal
        elif volume_ratio < 0.5:  # Low volume - reduce confidence
            signal_score *= 0.8
    
    # RSI Filter (5% weight) - Extreme level filter
    rsi = indicators.get('rsi')
    if rsi is not None:
        if rsi < 25:  # Extremely oversold - potential reversal
            signal_score += 0.3 * 0.05
        elif rsi > 75:  # Extremely overbought - potential reversal
            signal_score -= 0.3 * 0.05
        elif 45 <= rsi <= 55:  # Neutral RSI - good for trend following
            signal_score += 0.1 * 0.05 if signal_score > 0 else -0.1 * 0.05
    
    # Convert to final signal (centered around 1)
    final_signal = 1 + signal_score
    
    # Clamp between reasonable bounds
    return max(0.1, min(2.0, final_signal))


def alpha():
    logger.info("=== Running Alpha Strategy ===")
    
    api_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    if not api_token:
        logger.error("Failed to log in to tracking API. Please check your credentials.")
        return
    
    indicators = get_indicators(api_token)
    if not indicators:
        logger.error("Failed to fetch indicators.")
        return
    
    logger.info("Fetched indicators: %s", indicators['indicators'])
    signals = {}
    for token in indicators['indicators']:
        signal = process_indicators_alpha(indicators['indicators'][token])
        signals[token] = signal

    logger.info("Generated trading signals: %s", signals)
    tokens_to_buy = {}
    for token, signal in signals.items():
        if signal > 1 and token != "USDC":
            current_signals = min(tokens_to_buy.values(), default=0)
            if signal > current_signals:
                tokens_to_buy[token] = signal
                if len(tokens_to_buy) > 3:  # Limit to top 3 tokens
                    tokens_to_buy = dict(sorted(tokens_to_buy.items(), key=lambda item: item[1], reverse=True)[:3])

    logger.info("Tokens prioritized for buying: %s", tokens_to_buy)
    balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
    logger.info("Crypto balances with USD value: %s", balances)
    logger.info(f"Total USD value of crypto holdings: ${max_value:.2f}")
    current_holdings = {}
    for token in balances:
        if balances[token]['usd_value'] > 0.01:
            current_holdings[token] = balances[token]['usd_value']
    
    # sell all and buy USDC if no strong buy signals
    if not tokens_to_buy:
        for token in current_holdings:
            if token != "USDC" and token != "SOL":
                execute_crypto_trade(token, "sell", balances[token]['max_sell'], indicators['indicators'])

        time.sleep(10)  # wait for sells to process
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])

        if balances["USDC"]["max_buy"] > 0.01:
            execute_crypto_trade("USDC", "buy", balances["USDC"]["max_buy"], indicators['indicators'])
        
        api_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        status_update(api_token, "Bought USDC")
        return
    
    # sell any tokens not in buy list
    for token in current_holdings:
        if token not in tokens_to_buy and token != "SOL":
            execute_crypto_trade(token, "sell", balances[token]['max_sell'], indicators['indicators'])
    
    time.sleep(10)  # wait for sells to process
    balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
    # buy tokens in buy list
    for token in tokens_to_buy:
        buy_amount = balances[token]['max_buy'] / len(tokens_to_buy)
        if token in balances and token != "SOL" and token not in current_holdings and buy_amount > 0:
            execute_crypto_trade(token, "buy", buy_amount, indicators['indicators'])

    api_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    status_update(api_token, f"Investing in {', '.join(tokens_to_buy.keys())}")


def beta():
    logger.info("=== Running Beta Strategy ===")
    
    api_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    if not api_token:
        logger.error("Failed to log in to tracking API. Please check your credentials.")
        return
    
    indicators = get_indicators(api_token)
    if not indicators:
        logger.error("Failed to fetch indicators.")
        return
    
    logger.info("Fetched indicators: %s", indicators['indicators'])
    signals = {}
    for token in indicators['indicators']:
        signal = process_indicators_beta(indicators['indicators'][token])
        signals[token] = signal

    logger.info("Generated trading signals: %s", signals)
    tokens_to_buy = {}
    for token, signal in signals.items():
        if signal > 1 and token != "USDC":
            current_signals = min(tokens_to_buy.values(), default=0)
            if signal > current_signals:
                tokens_to_buy[token] = signal
                if len(tokens_to_buy) > 3:  # Limit to top 3 tokens
                    tokens_to_buy = dict(sorted(tokens_to_buy.items(), key=lambda item: item[1], reverse=True)[:3])

    logger.info("Tokens prioritized for buying: %s", tokens_to_buy)
    balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
    logger.info("Crypto balances with USD value: %s", balances)
    logger.info(f"Total USD value of crypto holdings: ${max_value:.2f}")
    current_holdings = {}
    for token in balances:
        if balances[token]['usd_value'] > 0.01:
            current_holdings[token] = balances[token]['usd_value']
    
    # sell all and buy USDC if no strong buy signals
    if not tokens_to_buy:
        for token in current_holdings:
            if token != "USDC" and token != "SOL":
                execute_crypto_trade(token, "sell", balances[token]['max_sell'], indicators['indicators'])

        time.sleep(10)  # wait for sells to process
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        
        if balances["USDC"]["max_buy"] > 0.01:
            execute_crypto_trade("USDC", "buy", balances["USDC"]["max_buy"], indicators['indicators'])
 
        api_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        status_update(api_token, "Bought USDC")
        return
    
    # sell any tokens not in buy list
    for token in current_holdings:
        if token not in tokens_to_buy and token != "SOL":
            execute_crypto_trade(token, "sell", balances[token]['max_sell'], indicators['indicators'])
    
    time.sleep(10)  # wait for sells to process
    balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
    # buy tokens in buy list
    for token in tokens_to_buy:
        buy_amount = balances[token]['max_buy'] / len(tokens_to_buy)
        if token in balances and token != "SOL" and token not in current_holdings and buy_amount > 0:
            execute_crypto_trade(token, "buy", buy_amount, indicators['indicators'])

    api_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    status_update(api_token, f"Investing in {', '.join(tokens_to_buy.keys())}")
