from clients.crypto_trade import execute_crypto_trade

result = execute_crypto_trade(
    token_symbol="JUP", 
    action="buy",
    amount=0.01
)
