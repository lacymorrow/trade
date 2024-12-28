"""
Test script for trading bots.
"""

import os
import logging
from dotenv import load_dotenv
from trading.bots.stock_bot import StockBot
from trading.bots.crypto_bot import CryptoBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_stock_bot():
    """Test stock trading bot."""
    try:
        # Initialize bot with test mode
        bot = StockBot(
            api_key=os.getenv('ALPACA_API_KEY'),
            api_secret=os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL'),
            test_mode=True
        )

        # Start bot
        logger.info("Starting stock bot test...")
        bot.start()

    except Exception as e:
        logger.error(f"Stock bot test failed: {str(e)}")

def test_crypto_bot():
    """Test crypto trading bot."""
    try:
        # Initialize bot with test mode
        bot = CryptoBot(
            api_key=os.getenv('ALPACA_API_KEY'),
            api_secret=os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL'),
            test_mode=True
        )

        # Start bot
        logger.info("Starting crypto bot test...")
        bot.start()

    except Exception as e:
        logger.error(f"Crypto bot test failed: {str(e)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test trading bots')
    parser.add_argument('--bot', choices=['stock', 'crypto', 'both'], default='both',
                      help='Which bot to test')

    args = parser.parse_args()

    if args.bot in ['stock', 'both']:
        test_stock_bot()

    if args.bot in ['crypto', 'both']:
        test_crypto_bot()
