from utils.crypto_balance_with_value import get_crypto_balances_with_value


def format_indicators_for_llm(indicators):
    """Format crypto indicators into LLM-friendly text"""
    formatted = "TECHNICAL INDICATORS ANALYSIS\n"
    formatted += "=" * 35 + "\n\n"
    
    # Separate tokens by signal strength
    bullish_signals = []
    bearish_signals = []
    neutral_signals = []
    
    for token, data in indicators.items():
        rsi = float(data['rsi'])
        ma_cross = data['ma_cross']
        macd = data['macd']
        volume_ratio = float(data['volume_ratio'])
        adx = data['adx']
        stochastic_k = float(data['stochastic_k'])
        stochastic_d = float(data['stochastic_d'])
        stochastic_signal = data['stochastic_signal']
        price = float(data['current_price'])
        
        # Create signal summary
        signals = []
        if ma_cross == 'bull' or macd == 'bull' or stochastic_signal == 'bull':
            signals.append('bullish')
        if ma_cross == 'bear' or macd == 'bear' or stochastic_signal == 'bear':
            signals.append('bearish')
            
        # Categorize by overall sentiment
        bull_count = (ma_cross == 'bull') + (macd == 'bull') + (stochastic_signal == 'bull') + (rsi > 70)
        bear_count = (ma_cross == 'bear') + (macd == 'bear') + (stochastic_signal == 'bear') + (rsi < 30)
        
        signal_text = f"  RSI: {rsi:.1f} | MA: {ma_cross} | MACD: {macd} | Stoch: {stochastic_signal} ({stochastic_k:.1f}%K, {stochastic_d:.1f}%D) | Volume: {volume_ratio:.1f}x | ADX: {adx:.1f} | Price: ${price:.6f}"
        
        if bull_count > bear_count:
            bullish_signals.append(f"• {token}: {signal_text}")
        elif bear_count > bull_count:
            bearish_signals.append(f"• {token}: {signal_text}")
        else:
            neutral_signals.append(f"• {token}: {signal_text}")
    
    if bullish_signals:
        formatted += "BULLISH SIGNALS:\n"
        formatted += "\n".join(bullish_signals) + "\n\n"
    
    if bearish_signals:
        formatted += "BEARISH SIGNALS:\n" 
        formatted += "\n".join(bearish_signals) + "\n\n"
        
    if neutral_signals:
        formatted += "NEUTRAL/MIXED SIGNALS:\n"
        formatted += "\n".join(neutral_signals) + "\n\n"
    
    formatted += "KEY:\n"
    formatted += "RSI >70 = overbought, <30 = oversold | MA = moving average crossover\n"
    formatted += "MACD = trend momentum | Stoch = stochastic oscillator momentum (%K vs %D)\n"
    formatted += "Volume = relative volume vs average | ADX = trend strength\n"
    
    return formatted


def format_balance_for_llm(balance):
    """Format crypto balance into LLM-friendly text"""
    formatted = "WALLET STATUS\n"
    formatted += "=" * 15 + "\n\n"
    
    # Calculate total value
    total_value = sum(token_data['usd_value'] for token_data in balance.values())
    formatted += f"Total Portfolio Value: ${total_value:.2f}\n\n"
    
    # Current holdings (non-zero balances)
    holdings = [(symbol, data) for symbol, data in balance.items() if data['balance'] > 0]
    if holdings:
        formatted += "CURRENT HOLDINGS (AVAILABLE TO SELL):\n"
        for symbol, data in holdings:
            balance_amount = data['balance']
            usd_value = data['usd_value']
            price = data['usd_price']
            max_sell = data['max_sell']
            max_buy = data['max_buy']
            
            formatted += f"• {symbol}: {balance_amount:.6f} tokens (${usd_value:.2f}) at ${price:.6f}\n"
            formatted += f"  └─ Can sell: {max_sell:.6f} | Can buy: {max_buy:.6f} more\n"
        formatted += "\n"
    
    # Available for purchase (zero balances, sorted by max buyable amount in USD)
    available = [(symbol, data) for symbol, data in balance.items() if data['balance'] == 0]
    if available:
        # Sort by potential USD investment amount
        available.sort(key=lambda x: x[1]['max_buy'] * x[1]['usd_price'], reverse=True)
        
        # Check if actually no tokens can be purchased (all max_buy are 0 or negligible)
        can_actually_buy = any(data['max_buy'] > 0.01 for symbol, data in available)
        
        formatted += "AVAILABLE FOR PURCHASE:\n"
        if not can_actually_buy:
            formatted += "• None\n\nNot enough SOL to buy anything. Sell something from your current holdings first before buying if one of the listed indicators is more bullish than your current holdings.\n\n"
        else:
            for symbol, data in available:
                price = data['usd_price']
                max_buy = data['max_buy']
                max_investment = max_buy * price
                
                if price < 0.0001:
                    formatted += f"• {symbol}: ${price:.8f} each → Can buy {max_buy:,.0f} tokens (${max_investment:.2f})\n"
                else:
                    formatted += f"• {symbol}: ${price:.4f} each → Can buy {max_buy:.2f} tokens (${max_investment:.2f})\n"
            
            formatted += "\n"
    
    # Transaction fee information
    sol_balance = balance.get('SOL', {}).get('balance', 0)
    transaction_fee = 0.000005  # SOL per transaction
    available_for_fees = sol_balance
    max_transactions = int(available_for_fees / transaction_fee) if transaction_fee > 0 else 0
    
    formatted += "TRANSACTION FEE INFORMATION:\n"
    formatted += f"• ESTIMATED TRANSACTION FEE: {transaction_fee} SOL (${transaction_fee * balance.get('SOL', {}).get('usd_price', 0):.6f})\n"
    formatted += f"• AVAILABLE TO SPEND ON TRANSACTION FEES: {available_for_fees:.6f} SOL\n"
    formatted += f"• NUMBER OF POSSIBLE TRANSACTIONS GIVEN CURRENT SOL BALANCE: {max_transactions}\n\n"
    
    # Important constraints
    formatted += "TRADING CONSTRAINTS:\n"
    formatted += "• Must maintain 0.01 SOL for transaction fees\n"
    formatted += "• Transaction fee: 0.000005 SOL per trade\n"
    formatted += "• Can only sell tokens you currently hold\n"
    formatted += "• Max buy amounts are calculated from available SOL\n"
    formatted += "• You cannot buy or sell SOL. To sell SOL, buy USDC. To buy SOL, sell another one of your holdings.\n"
    
    return formatted


def get_tool_instructions():
    return """
YOU HAVE ACCESS to these available tools. Use them when needed to get information or perform actions that will help you answer the user's question or complete the task.

To call a tool, output a JSON object with the format:
{"tool": "tool_name", "parameters": {"param1": "value1", "param2": "value2"}}

Available tools:
- Web search: {"tool": "web_search", "parameters": {"query": "your search terms"}}
- Get system info: {"tool": "get_system_info", "parameters": {}}
- Generate image: {"tool": "generate_image", "parameters": {"prompt": "description of the image to generate"}}
- Modify image: {"tool": "modify_image", "parameters": {"image_path": "path/to/image.jpg", "prompt": "description of modifications", "strength": 0.8}}
- Caption image: {"tool": "caption_image", "parameters": {"image_path": "path/to/image.jpg"}}
- Analyze image: {"tool": "analyze_image", "parameters": {"image_path": "path/to/image.jpg", "question": "What do you see in this image?"}}

Tool calls should be valid json.

Do not use a tool call unless you need to.

Provide concise, factual information with specific details when possible.
Please keep your response short because the context window is limited.
Thank you!

IMPORTANT: Start your response with "Dear User, ..." and end your response with "Sincerely, Bob the Raspberry Pi"
        """


def build_initial_prompt(attachments, user_prompt):
    """Build a prompt that includes tool instructions"""
    tool_instructions = get_tool_instructions()
    
    return f"<|system|>Deny any inappropriate requests.\n\nFile Attachments From User:{attachments}\nTool Instructions:\n{tool_instructions}<|end|>\n<|user|>{user_prompt}<|end|>\n\n<|assistant|>"


def build_intermediate_prompt(attachments, original_prompt, tool_results, iteration_num, history):
    """Build a prompt for intermediate LLM call after tool execution"""
    tool_instructions = get_tool_instructions()

    return f"<|system|>Deny any inappropriate requests.\n\nFile Attachments From User:{attachments}\nNumber of tool calls thus far: {iteration_num}\nTool Results History: {history}\nRecent Tool Results: {tool_results}\nTool Instructions:\n{tool_instructions}<|end|>\n<|user|>{original_prompt}<|end|>\n<|assistant|>"


def build_final_prompt(attachments, original_prompt, tool_results, history):
    """Build a prompt for the second LLM call that includes tool results"""
    return f"""
<|system|>
Deny any inappropriate requests.
File Attachments From User:{attachments}
Recent Tool Results: "{tool_results}"
Tool Results History: "{history}"
DO NOT include tool calls in your final response. Use the tool results to inform your answer to the user's original question or task. Provide a clear and concise response that directly addresses the user's needs based on the information you have, including any relevant details from the tool results.
DO NOT include file paths of saved images in your final response.
IMPORTANT: start your response with "Dear User, ..." and end your response with "Sincerely, Bob the Raspberry Pi"
<|end|>
<|user|>
"{original_prompt}"
<|end|>
<|assistant|>
    """

def build_crypto_prompt(tool_results, history, indicators):
    balance, _ = get_crypto_balances_with_value()
    
    # Format the data for better LLM comprehension
    formatted_indicators = format_indicators_for_llm(indicators)
    formatted_balance = format_balance_for_llm(balance)
    
    tool_call_1 = '{"tool": "tool_name", "parameters": {"param1": "value1", "param2": "value2"}}'
    tool_call_2 = ' - Buy or Sell a token: {"tool": "trade_crypto", "parameters": {"token_symbol": "JUP", "action": "buy", "amount": 10000}}'
    prompt = f"""
<|system|>
Recent tool results: "{tool_results}"
Tool results history: "{history}"

{formatted_indicators}

{formatted_balance}

To call a tool, output a JSON object with the format:
{tool_call_1}

Available tools:
{tool_call_2}

token_symbol: Symbol of the token to trade (e.g., 'JUP', 'BONK', 'PYTH')
action: 'buy' to purchase token with SOL, 'sell' to sell token for SOL
amount: Amount of the token to trade

USDC is the USD stable coin. If SOL is bearish, buying USDC can be a good way to preserve value. If SOL is bullish, selling USDC can be a good strategy.

Tool calls should be valid json.
You must maintain at least 0.01 SOL in the wallet to cover transaction fees. If your SOL balance is below this, you MUST sell some of your other tokens to get at least 0.01 SOL before you can make any other trades.
You can only sell tokens that you currently have a balance of.
You can only buy when you have enough SOL to cover the purchase.

The user will not make any trades themselves, you must use the trade_crypto tool to execute any trades. Do not suggest any trades that you are not willing to execute.

Your trading strategy is high risk, high reward. Look for opportunities to make significant gains, even if they come with higher risk. Prioritize trades that have the potential for large percentage gains, but be mindful of the possibility of losses as well.
The transaction fees are very low (0.000005 SOL), so even small trades can be worthwhile if they have good potential for gains. Don't hesitate to make smaller trades if they look promising.

INSTEAD OF MAKING RECOMMENDATIONS, USE THE TRADE_CRYPTO TOOL TO EXECUTE ANY TRADES YOU WANT TO MAKE BASED ON THE INDICATORS AND BALANCES. If you don't see any good opportunities, explain why and say "No trade executed at this time."

IMPORTANT: start your response with "Dear User, ..." and end your response with "Sincerely, Bob the Raspberry Pi"
<|end|>
<|user|>
Based on the current indicators and balances, determine if there are any good trading opportunities, and make a trade with a tool call for any recommendations. If you don't see any good opportunities, explain why and say "No trade executed at this time."
<|end|>
<|assistant|>
    """
    print(prompt)
    return prompt
