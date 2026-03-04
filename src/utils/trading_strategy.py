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
    Alpha Strategy: Concentrated Equal-Weight Strategy
    - Sells bearish tokens (score < 0) first
    - Buys top 3 most bullish tokens (score > 3) with EQUAL allocation
    - Divides available SOL equally among the 3 tokens (33% each)
    - High conviction, concentrated positions
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
                logger.info(f"Alpha: Selling {sell_amount:.6f} {token_symbol} (bearish score: {score})")
                
                result = execute_crypto_trade(token_symbol, "sell", sell_amount, indicators['indicators'])
                logger.info(f"{token_symbol} sell result: {result}")
                trades_executed += 1
    
    # Refresh balances after selling (max_buy amounts will have changed)
    if trades_executed > 0:
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        logger.info(f"Updated balances after selling. New total USD value: ${max_value:.2f}")
    
    # Check if any tokens are bullish (score > 3)
    bullish_tokens = [token for token, score in sorted_tokens if score > 3]
    
    if not bullish_tokens:
        logger.info("No strongly bullish tokens found. Buying USDC instead.")
        usdc_data = balances.get('USDC', {})
        max_buy = usdc_data.get('max_buy', 0)
        if max_buy > 0:
            # Use 95% of max_buy to account for price changes
            buy_amount = max_buy * 0.95
            logger.info(f"Alpha: Buying {buy_amount:.6f} USDC (95% of max_buy: {max_buy})")
            result = execute_crypto_trade("USDC", "buy", buy_amount, indicators['indicators'])
            logger.info(f"USDC trade result: {result}")
            trades_executed += 1
        else:
            logger.info("No available funds to buy USDC")
        logger.info(f"Alpha strategy completed. Executed {trades_executed} trades.")
        return
    
    # Alpha strategy: Equal allocation among top 3 most bullish tokens
    target_trades = min(3, len(bullish_tokens))
    
    # Get initial total SOL available for trading
    sol_data = balances.get('SOL', {})
    total_sol_available = sol_data.get('max_buy', 0)
    
    # Divide SOL equally among target trades (with 95% safety margin)
    sol_per_token = (total_sol_available / target_trades) * 0.95
    logger.info(f"Alpha: Allocating {sol_per_token:.6f} SOL to each of {target_trades} tokens")
    
    for i in range(target_trades):
        token_symbol, score = sorted_tokens[i]
        
        # Refresh balances before each purchase (previous buys reduce SOL balance)
        if i > 0:
            balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
            sol_data = balances.get('SOL', {})
            current_sol = sol_data.get('max_buy', 0)
            # Use remaining allocation or current SOL, whichever is smaller
            buy_amount_sol = min(sol_per_token, current_sol * 0.95)
        else:
            buy_amount_sol = sol_per_token
        
        if buy_amount_sol > 0:
            # Convert SOL amount to token amount using price data
            token_data = balances.get(token_symbol, {})
            sol_data = balances.get('SOL', {})
            
            if token_data.get('usd_price') and sol_data.get('usd_price'):
                token_price_sol = token_data['usd_price'] / sol_data['usd_price']
                token_amount = buy_amount_sol / token_price_sol
                
                logger.info(f"Alpha: Buying {token_amount:.6f} {token_symbol} with {buy_amount_sol:.6f} SOL (score: {score}, equal allocation)")
                
                result = execute_crypto_trade(token_symbol, "buy", token_amount, indicators['indicators'])
                logger.info(f"{token_symbol} trade result: {result}")
                trades_executed += 1
            else:
                logger.error(f"Could not find price data for {token_symbol}. Skipping trade.")
        else:
            logger.info(f"No available funds to buy {token_symbol}")
    
    logger.info(f"Alpha strategy completed. Executed {trades_executed} trades.")


def beta():
    """
    Beta Strategy: Score-Weighted Diversified Strategy  
    - Sells bearish tokens (score < 0) first
    - Buys top 5 bullish tokens (score > 1) with score-weighted allocation
    - Higher scoring tokens get proportionally more allocation
    - More diversified, risk-managed approach
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
    
    # Refresh balances after selling (max_buy amounts will have changed)
    sells_executed = trades_executed
    if sells_executed > 0:
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        logger.info(f"Updated balances after selling. New total USD value: ${max_value:.2f}")
    
    # Check if we have any bullish tokens
    bullish_tokens = [token for token, score in sorted_tokens if score > 1]
    
    if not bullish_tokens:
        logger.info("No bullish tokens found. Buying USDC instead.")
        usdc_data = balances.get('USDC', {})
        max_buy = usdc_data.get('max_buy', 0)
        if max_buy > 0:
            buy_amount = max_buy * 0.95
            logger.info(f"Beta: Buying {buy_amount:.6f} USDC (95% of max_buy: {max_buy})")
            result = execute_crypto_trade("USDC", "buy", buy_amount, indicators['indicators'])
            logger.info(f"USDC trade result: {result}")
            trades_executed += 1
        return
    
    # Beta strategy: Score-weighted allocation among top 5 bullish tokens
    target_trades = min(5, len(bullish_tokens))
    
    # Get the top tokens and their scores for weight calculation
    top_tokens = [(symbol, score) for symbol, score in sorted_tokens[:target_trades] if score > 1]
    
    if not top_tokens:
        logger.info("No qualifying tokens for Beta strategy")
        return
    
    # Calculate total score and weights
    total_score = sum(score for _, score in top_tokens)
    logger.info(f"Beta: Total score for weight calculation: {total_score}")
    
    # Get initial total SOL available for trading
    sol_data = balances.get('SOL', {})
    total_sol_available = sol_data.get('max_buy', 0) * 0.95  # 95% safety margin
    
    for i, (token_symbol, score) in enumerate(top_tokens):
        # Refresh balances before each purchase (previous buys reduce SOL balance)
        if i > 0:
            balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        
        # Calculate this token's allocation based on its score weight
        weight = score / total_score
        allocated_sol = total_sol_available * weight
        
        # Check current SOL availability
        current_sol_data = balances.get('SOL', {})
        current_sol_available = current_sol_data.get('max_buy', 0) * 0.95
        
        # Use the smaller of allocated amount or current availability
        buy_amount_sol = min(allocated_sol, current_sol_available)
        
        if buy_amount_sol > 0:
            # Convert SOL amount to token amount using price data
            token_data = balances.get(token_symbol, {})
            sol_data = balances.get('SOL', {})
            
            if token_data.get('usd_price') and sol_data.get('usd_price'):
                token_price_sol = token_data['usd_price'] / sol_data['usd_price']
                token_amount = buy_amount_sol / token_price_sol
                
                logger.info(f"Beta: Buying {token_amount:.6f} {token_symbol} with {buy_amount_sol:.6f} SOL (score: {score}, weight: {weight:.1%})")
                
                result = execute_crypto_trade(token_symbol, "buy", token_amount, indicators['indicators'])
                logger.info(f"{token_symbol} trade result: {result}")
                trades_executed += 1
            else:
                logger.error(f"Could not find price data for {token_symbol}. Skipping trade.")
        else:
            logger.info(f"Skipping {token_symbol} - insufficient funds available")
    
    logger.info(f"Beta strategy completed. Executed {trades_executed} trades.")
