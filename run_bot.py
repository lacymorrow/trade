import os
import logging
from trading.bot import TradingBot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        # Verify API credentials
        required_env_vars = [
            'ALPACA_API_KEY',
            'ALPACA_SECRET_KEY',
            'ALPACA_BASE_URL',
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET',
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET',
            'ALPHA_VANTAGE_API_KEY'
        ]

        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return

        # Create and run the trading bot
        bot = TradingBot()
        logger.info("Starting trading bot...")
        bot.run()

    except KeyboardInterrupt:
        logger.info("Shutting down trading bot...")
    except Exception as e:
        logger.error(f"Error running trading bot: {str(e)}")

if __name__ == "__main__":
    main()
