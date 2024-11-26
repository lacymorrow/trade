import logging
from crypto.bot import CryptoBot
from crypto_config import TRADING_PAIRS, DEFAULT_TIMEFRAME

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the crypto trading bot."""
    try:
        # Configure the bot
        config = {
            'trading_pairs': TRADING_PAIRS,
            'timeframe': DEFAULT_TIMEFRAME
        }

        # Initialize and run the bot
        bot = CryptoBot(config)
        bot.run()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
