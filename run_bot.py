import logging
import sys
import argparse
from trading.bot import TradingBot

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the trading bot')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no real trades)')
    parser.add_argument('--single-run', action='store_true', help='Run a single analysis cycle and exit')
    args = parser.parse_args()

    try:
        # Initialize and start the bot
        bot = TradingBot(test_mode=args.test)
        if args.test:
            logging.info("Starting bot in TEST MODE - No real trades will be executed")
        else:
            logging.info("Starting bot in LIVE MODE - Real trades will be executed")

        if args.single_run:
            logging.info("Running single analysis cycle...")
            bot.analyze_all_symbols()
        else:
            bot.start()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot stopped due to error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
