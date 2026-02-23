from utils.crypto_indicators import get_all_token_indicators
from utils.crypto_balance_with_value import get_crypto_balances_with_value


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

def build_crypto_prompt():
    indicators = get_all_token_indicators()
    balance, _ = get_crypto_balances_with_value()
    tool_call_1 = '{"tool": "tool_name", "parameters": {"param1": "value1", "param2": "value2"}}'
    tool_call_2 = ' - Buy or Sell a token: {"tool": "trade_crypto", "parameters": {"token_symbol": "JUP", "action": "buy", "amount": 100}}'
    return f"""
<|system|>
Use these indicators to determine what to buy or sell:
{indicators}
Current crypto balances with USD value:
{balance}

To call a tool, output a JSON object with the format:
{tool_call_1}

Available tools:
{tool_call_2}

token_symbol: Symbol of the token to trade (e.g., 'JUP', 'BONK', 'PYTH')
action: 'buy' to purchase token with SOL, 'sell' to sell token for SOL
amount: Amount to trade
        - For 'buy': amount of SOL to spend (in SOL, e.g., 1.5 for 1.5 SOL)
        - For 'sell': amount of tokens to sell (in token units)

Tool calls should be valid json.
You must maintain at least 0.1 SOL in the wallet to cover transaction fees. If your SOL balance is below this, you MUST sell some of your other tokens to get at least $2 worth of SOL before you can make any other trades.

IMPORTANT: start your response with "Dear User, ..." and end your response with "Sincerely, Bob the Raspberry Pi"
<|end|>
<|user|>
Based on the current indicators and balances, determine if there are any good trading opportunities, and make a trade with a tool call if you think it's warranted. If you don't see any good opportunities, explain why and say "No trade executed at this time."
<|end|>
<|assistant|>
    """