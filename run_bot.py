import argparse
import json
import os
import sys
from dotenv import load_dotenv
from trading.bots.crypto_bot import CryptoBot

def main():
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description='Run the trading bot')
    parser.add_argument('--single-run', action='store_true', help='Run a single analysis')
    parser.add_argument('--get-trades', action='store_true', help='Get recent trades')
    args = parser.parse_args()

    # Get API credentials from environment variables
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL')

    if not api_key or not api_secret:
        print(json.dumps({
            'error': 'Missing API credentials. Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.'
        }))
        sys.exit(1)

    bot = CryptoBot(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
        test_mode=True  # Always use test mode for safety
    )

    if args.get_trades:
        # Get recent trades from all symbols
        all_trades = []
        for symbol in bot.get_trading_pairs():
            trades = bot.data_engine.get_recent_trades(symbol, limit=10)
            if trades is not None:
                for _, trade in trades.iterrows():
                    all_trades.append({
                        'id': f"{trade['timestamp'].isoformat()}-{symbol}",
                        'timestamp': trade['timestamp'].isoformat(),
                        'symbol': symbol,
                        'side': trade['side'],
                        'price': float(trade['price']),
                        'quantity': float(trade['size'])
                    })

        # Sort trades by timestamp, most recent first
        all_trades.sort(key=lambda x: x['timestamp'], reverse=True)

        # Print as JSON to stdout
        print(json.dumps({'trades': all_trades}))
        return

    if args.single_run:
        bot.run_single_analysis()
    else:
        bot.run()

if __name__ == '__main__':
    main()
