import logging
import sys
import argparse
from trading.crypto_bot import CryptoBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the crypto trading bot')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no real trades)')
    parser.add_argument('--symbols', nargs='+', help='Specific crypto symbols to trade (e.g., BTC USD ETH)')
    args = parser.parse_args()

    try:
        # Initialize and start the bot
        bot = CryptoBot(
            test_mode=args.test,
            symbols=args.symbols
        )

        if args.test:
            logging.info("Starting crypto bot in TEST MODE - No real trades will be executed")
        else:
            logging.info("Starting crypto bot in LIVE MODE - Real trades will be executed")

        if args.symbols:
            logging.info(f"Trading specific symbols: {', '.join(args.symbols)}")
        else:
            logging.info("Trading all available crypto pairs")

        bot.start()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot stopped due to error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
