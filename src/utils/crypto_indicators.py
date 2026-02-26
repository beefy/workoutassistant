import os
import logging
from clients.crypto_data import BirdeyeDataFetcher, IndicatorCalculator, TOKEN_ADDRESSES
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def get_all_token_indicators():
    """Fetch and display indicators for all tokens"""
    
    # Check if API key is set
    if not os.getenv("BIRDEYE_API_KEY"):
        logger.error("Error: BIRDEYE_API_KEY environment variable not set")
        return
    
    # Initialize components
    fetcher = BirdeyeDataFetcher()
    calculator = IndicatorCalculator()
    
    results = {}
    
    for symbol, address in TOKEN_ADDRESSES.items():
        try:
            logger.info(f"Processing {symbol}...")
            
            # Get indicators for this token
            indicators = calculator.update_token_data(symbol, address, fetcher)
            results[symbol] = indicators
            
            logger.info(f"✓ {symbol} completed successfully")
            
        except Exception as e:
            logger.error(f"✗ Error processing {symbol}: {str(e)}")
            logger.exception("Full traceback:")
            results[symbol] = None
    
    return results

# if __name__ == "__main__":
#     # Run the function
#     results = get_all_token_indicators()
#     logger.info(results)
