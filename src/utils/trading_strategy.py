from utils.tracking_api import login, get_indicators
import os
from clients.crypto_trade import execute_crypto_trade
from utils.crypto_balance_with_value import get_crypto_balances_with_value
from utils.logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def calculate_bullishness_score(indicators_data):
    """Calculate bullishness score for each token based on technical indicators"""
    scores = {}
    
    for token, data in indicators_data.items():
        if token == 'USDC':  # Skip USDC from bullishness calculation
            continue
            
        score = 0
        
        # RSI scoring (0-100, higher is more bullish in current context)
        rsi = data.get('rsi', 50)
        if rsi > 70:
            score += 3  # Strong bullish
        elif rsi > 60:
            score += 2  # Moderate bullish
        elif rsi > 50:
            score += 1  # Mild bullish
        else:
            score -= 1  # Bearish
            
        # Moving Average Cross
        ma_cross = data.get('ma_cross', 'neutral')
        if ma_cross == 'bull':
            score += 2
        elif ma_cross == 'bear':
            score -= 2
            
        # MACD
        macd = data.get('macd', 'neutral')
        if macd == 'bull':
            score += 2
        elif macd == 'bear':
            score -= 2
            
        # Stochastic signal
        stoch_signal = data.get('stochastic_signal', 'neutral')
        if stoch_signal == 'bull':
            score += 1
        elif stoch_signal == 'bear':
            score -= 1
            
        # Volume ratio bonus (higher volume = more conviction)
        volume_ratio = data.get('volume_ratio', 0)
        if volume_ratio > 1.0:
            score += 1
        elif volume_ratio > 0.5:
            score += 0.5
            
        scores[token] = score
        
    return scores


def alpha():
    """
    Alpha Strategy: Aggressive Momentum Strategy
    - Focuses on tokens with highest RSI and strongest bull signals
    - Buys top 3 most bullish tokens with available max_buy amounts
    - Uses 95% of max_buy to account for price changes
    """
    logger.info("=== Running Alpha Strategy (Aggressive Momentum) ===")
    
    token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    if not token:
        logger.error("Failed to log in to tracking API. Please check your credentials.")
        return
    
    indicators = get_indicators(token)
    if not indicators:
        logger.error("Failed to fetch indicators.")
        return
    
    balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
    logger.info("Crypto balances with USD value: %s", balances)
    logger.info(f"Total USD value of crypto holdings: ${max_value:.2f}")
    
    # Calculate bullishness scores
    scores = calculate_bullishness_score(indicators['indicators'])
    logger.info(f"Bullishness scores: {scores}")
    
    # Sort tokens by bullishness score (highest first)
    sorted_tokens = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"Tokens sorted by bullishness: {sorted_tokens}")
    
    # Check if any tokens are bullish (score > 3)
    bullish_tokens = [token for token, score in sorted_tokens if score > 3]
    
    if not bullish_tokens:
        logger.info("No strongly bullish tokens found. Buying USDC instead.")
        usdc_data = balances.get('USDC', {})
        max_buy = usdc_data.get('max_buy', 0)
        if max_buy > 0:
            # Use 95% of max_buy to account for price changes
            buy_amount = max_buy * 0.95
            logger.info(f"Buying {buy_amount:.6f} USDC (95% of max_buy: {max_buy})")
            result = execute_crypto_trade("USDC", "buy", buy_amount, indicators['indicators'])
            logger.info(f"USDC trade result: {result}")
        else:
            logger.info("No available funds to buy USDC")
        return
    
    # Alpha strategy: Buy top 3 most bullish tokens
    trades_executed = 0
    target_trades = min(3, len(bullish_tokens))
    
    for i in range(target_trades):
        token_symbol, score = sorted_tokens[i]
        token_data = balances.get(token_symbol, {})
        max_buy = token_data.get('max_buy', 0)
        
        if max_buy > 0:
            # Use 95% of max_buy to account for price changes
            buy_amount = max_buy * 0.95
            logger.info(f"Alpha: Buying {buy_amount:.6f} {token_symbol} (score: {score}, 95% of max_buy: {max_buy})")
            
            result = execute_crypto_trade(token_symbol, "buy", buy_amount, indicators['indicators'])
            logger.info(f"{token_symbol} trade result: {result}")
            trades_executed += 1
        else:
            logger.info(f"No available funds to buy {token_symbol}")
    
    logger.info(f"Alpha strategy completed. Executed {trades_executed} trades.")


def beta():
    """
    Beta Strategy: Balanced Risk-Adjusted Strategy  
    - Considers multiple factors with risk management
    - Buys more tokens but with smaller amounts
    - Sells tokens that become bearish
    - Uses 95% of max amounts to account for price changes
    """
    logger.info("=== Running Beta Strategy (Balanced Risk-Adjusted) ===")
    
    token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    if not token:
        logger.error("Failed to log in to tracking API. Please check your credentials.")
        return
    
    indicators = get_indicators(token)
    if not indicators:
        logger.error("Failed to fetch indicators.")
        return
    
    balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
    logger.info("Crypto balances with USD value: %s", balances)
    logger.info(f"Total USD value of crypto holdings: ${max_value:.2f}")
    
    # Calculate bullishness scores
    scores = calculate_bullishness_score(indicators['indicators'])
    logger.info(f"Bullishness scores: {scores}")
    
    # Sort tokens by bullishness score
    sorted_tokens = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"Tokens sorted by bullishness: {sorted_tokens}")
    
    trades_executed = 0
    
    # First, sell any bearish tokens we currently hold
    for token_symbol, score in sorted_tokens:
        if score < 0:  # Bearish token
            token_data = balances.get(token_symbol, {})
            max_sell = token_data.get('max_sell', 0)
            balance = token_data.get('balance', 0)
            
            if max_sell > 0 and balance > 0:
                # Use 95% of max_sell to account for price changes
                sell_amount = min(max_sell * 0.95, balance)
                logger.info(f"Beta: Selling {sell_amount:.6f} {token_symbol} (bearish score: {score})")
                
                result = execute_crypto_trade(token_symbol, "sell", sell_amount, indicators['indicators'])
                logger.info(f"{token_symbol} sell result: {result}")
                trades_executed += 1
    
    # Check if we have any bullish tokens
    bullish_tokens = [token for token, score in sorted_tokens if score > 1]
    
    if not bullish_tokens:
        logger.info("No bullish tokens found. Buying USDC instead.")
        usdc_data = balances.get('USDC', {})
        max_buy = usdc_data.get('max_buy', 0)
        if max_buy > 0:
            buy_amount = max_buy * 0.95
            logger.info(f"Buying {buy_amount:.6f} USDC (95% of max_buy: {max_buy})")
            result = execute_crypto_trade("USDC", "buy", buy_amount, indicators['indicators'])
            logger.info(f"USDC trade result: {result}")
            trades_executed += 1
        return
    
    # Beta strategy: Buy top 5 bullish tokens with scaled amounts
    target_trades = min(5, len(bullish_tokens))
    
    for i in range(target_trades):
        token_symbol, score = sorted_tokens[i]
        token_data = balances.get(token_symbol, {})
        max_buy = token_data.get('max_buy', 0)
        
        if max_buy > 0 and score > 1:  # Only buy if moderately bullish
            # Scale buy amount based on rank and score
            # Top ranked gets 95% of max, others get progressively less
            scale_factor = 0.95 * (0.8 ** i)  # 95%, 76%, 61%, 49%, 39%
            buy_amount = max_buy * scale_factor
            
            logger.info(f"Beta: Buying {buy_amount:.6f} {token_symbol} (score: {score}, {scale_factor*100:.0f}% of max_buy: {max_buy})")
            
            result = execute_crypto_trade(token_symbol, "buy", buy_amount, indicators['indicators'])
            logger.info(f"{token_symbol} trade result: {result}")
            trades_executed += 1
        else:
            logger.info(f"Skipping {token_symbol} - insufficient funds or low score")
    
    logger.info(f"Beta strategy completed. Executed {trades_executed} trades.")
