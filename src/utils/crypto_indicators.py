import os
from clients.crypto_data import BirdeyeDataFetcher, IndicatorCalculator, TOKEN_ADDRESSES


def get_all_token_indicators():
    """Fetch and display indicators for all tokens"""
    
    # Check if API key is set
    if not os.getenv("BIRDEYE_API_KEY"):
        print("Error: BIRDEYE_API_KEY environment variable not set")
        return
    
    # Initialize components
    fetcher = BirdeyeDataFetcher()
    calculator = IndicatorCalculator()
    
    results = {}
    
    for symbol, address in TOKEN_ADDRESSES.items():
        try:
            print(f"Processing {symbol}...")
            
            # Get indicators for this token
            indicators = calculator.update_token_data(symbol, address, fetcher)
            results[symbol] = indicators
            
            print(f"✓ {symbol} completed successfully")
            
        except Exception as e:
            print(f"✗ Error processing {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            results[symbol] = None
    
    return results

# if __name__ == "__main__":
#     # Run the function
#     results = get_all_token_indicators()
#     print(results)
