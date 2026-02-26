from clients.crypto_trade import execute_crypto_trade

# TODO: get indicators data from tracking API and pass it to the trade function for price reference

result = execute_crypto_trade(
    token_symbol="JUP", 
    action="buy",
    amount=0.01
)
