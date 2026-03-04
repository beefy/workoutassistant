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
    
    # Refresh balances after selling bearish tokens
    if trades_executed > 0:
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        logger.info(f"Updated balances after selling bearish tokens. New total USD value: ${max_value:.2f}")
    
    # Check if any tokens are bullish (score > 3)
    bullish_tokens = [token for token, score in sorted_tokens if score > 3]
    target_tokens = [token for token, score in sorted_tokens[:3] if score > 3]  # Top 3 bullish tokens
    
    # Rebalancing: Sell held tokens that are no longer in target list (but not bearish)
    currently_held = [token for token, data in balances.items() 
                     if token not in ['SOL', 'USDC'] and data.get('balance', 0) > 0]
    
    tokens_to_sell = [token for token in currently_held 
                     if token not in target_tokens and scores.get(token, 0) >= 0]
    
    for token_symbol in tokens_to_sell:
        token_data = balances.get(token_symbol, {})
        max_sell = token_data.get('max_sell', 0)
        balance = token_data.get('balance', 0)
        
        if max_sell > 0 and balance > 0:
            sell_amount = min(max_sell * 0.95, balance)
            logger.info(f"Alpha: Rebalancing - Selling {sell_amount:.6f} {token_symbol} (no longer in top 3, score: {scores.get(token_symbol, 'N/A')})")
            
            result = execute_crypto_trade(token_symbol, "sell", sell_amount, indicators['indicators'])
            logger.info(f"{token_symbol} rebalance sell result: {result}")
            trades_executed += 1
    
    # Refresh balances after rebalancing sells
    if tokens_to_sell:
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        logger.info(f"Updated balances after rebalancing. New total USD value: ${max_value:.2f}")
    
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
    
    if target_trades == 0:
        logger.info("No qualifying tokens for Alpha strategy")
        return
    
    logger.info(f"Alpha: Equal allocation strategy among {target_trades} tokens")
    
    for i in range(target_trades):
        token_symbol, score = sorted_tokens[i]
        
        # Refresh balances before each purchase (previous buys reduce SOL balance)
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        sol_data = balances.get('SOL', {})
        current_sol_available = sol_data.get('max_buy', 0)
        
        # Calculate equal allocation: remaining SOL divided by remaining trades
        remaining_trades = target_trades - i
        buy_amount_sol = (current_sol_available / remaining_trades) * 0.95
        
        logger.info(f"Alpha: Trade {i+1}/{target_trades} - Allocating {buy_amount_sol:.6f} SOL to {token_symbol}")
        
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
    
    # Refresh balances after selling bearish tokens
    sells_executed = trades_executed
    if sells_executed > 0:
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        logger.info(f"Updated balances after selling bearish tokens. New total USD value: ${max_value:.2f}")
    
    # Check if we have any bullish tokens
    bullish_tokens = [token for token, score in sorted_tokens if score > 1]
    target_tokens = [token for token, score in sorted_tokens[:5] if score > 1]  # Top 5 bullish tokens
    
    # Rebalancing: Sell held tokens that are no longer in target list (but not bearish)
    currently_held = [token for token, data in balances.items() 
                     if token not in ['SOL', 'USDC'] and data.get('balance', 0) > 0]
    
    tokens_to_sell = [token for token in currently_held 
                     if token not in target_tokens and scores.get(token, 0) >= 0]
    
    for token_symbol in tokens_to_sell:
        token_data = balances.get(token_symbol, {})
        max_sell = token_data.get('max_sell', 0)
        balance = token_data.get('balance', 0)
        
        if max_sell > 0 and balance > 0:
            sell_amount = min(max_sell * 0.95, balance)
            logger.info(f"Beta: Rebalancing - Selling {sell_amount:.6f} {token_symbol} (no longer in top 5, score: {scores.get(token_symbol, 'N/A')})")
            
            result = execute_crypto_trade(token_symbol, "sell", sell_amount, indicators['indicators'])
            logger.info(f"{token_symbol} rebalance sell result: {result}")
            trades_executed += 1
    
    # Refresh balances after rebalancing sells
    if tokens_to_sell:
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        logger.info(f"Updated balances after rebalancing. New total USD value: ${max_value:.2f}")
    
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
    
    # Calculate total score for remaining tokens
    remaining_tokens = list(top_tokens)
    logger.info(f"Beta: Score-weighted allocation strategy among {len(remaining_tokens)} tokens")
    
    for i, (token_symbol, score) in enumerate(top_tokens):
        # Refresh balances before each purchase (previous buys reduce SOL balance)
        balances, max_value = get_crypto_balances_with_value(indicators['indicators'])
        current_sol_data = balances.get('SOL', {})
        current_sol_available = current_sol_data.get('max_buy', 0) * 0.95
        
        # Recalculate weights based on remaining tokens to maintain proper proportional allocation
        remaining_total_score = sum(s for _, s in remaining_tokens[i:])
        if remaining_total_score <= 0:
            logger.warning(f"No remaining score for allocation. Skipping {token_symbol}")
            continue
        
        # Calculate this token's share of remaining SOL based on its score weight among remaining tokens
        weight_in_remaining = score / remaining_total_score
        buy_amount_sol = current_sol_available * weight_in_remaining
        
        logger.info(f"Beta: Trade {i+1}/{len(top_tokens)} - Allocating {buy_amount_sol:.6f} SOL ({weight_in_remaining:.1%}) to {token_symbol}")
        
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
