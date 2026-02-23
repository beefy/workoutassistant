from clients.crypto_data import BirdeyeDataFetcher

fetcher = BirdeyeDataFetcher()
price = fetcher.get_current_price("JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN")
print(price)
