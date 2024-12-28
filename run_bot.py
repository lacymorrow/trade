import argparse
import json
import os
import sys
import logging
from dotenv import load_dotenv
from trading.bots.crypto_bot import CryptoBot

def setup_logging():
    """Configure logging to show all levels."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    # Set up logging
    setup_logging()

    try:
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
            error_response = {
                'success': False,
                'error': {
                    'code': 'MISSING_CREDENTIALS',
                    'message': 'Missing API credentials. Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.'
                }
            }
            print(json.dumps(error_response))
            sys.exit(1)

        bot = CryptoBot(
            api_key=api_key,
            api_secret=api_secret,
            base_url=base_url,
            test_mode=True  # Always use test mode for safety
        )

        if args.get_trades:
            try:
                # Get recent trades from all symbols
                all_trades = []
                errors = []

                for symbol in bot.get_trading_pairs():
                    try:
                        trades = bot.data_engine.get_recent_trades(symbol, limit=10)
                        if trades is not None:
                            for idx, trade in trades.iterrows():
                                try:
                                    all_trades.append({
                                        'id': f"{idx.isoformat()}-{symbol}",
                                        'timestamp': idx.isoformat(),
                                        'symbol': symbol,
                                        'side': trade['side'],
                                        'price': float(trade['price']),
                                        'quantity': float(trade['size'])
                                    })
                                except (KeyError, ValueError, TypeError) as e:
                                    errors.append({
                                        'symbol': symbol,
                                        'type': 'TRADE_PROCESSING_ERROR',
                                        'message': f"Error processing trade: {str(e)}"
                                    })
                                    logging.error(f"Error processing trade for {symbol}: {str(e)}")
                                    continue
                    except Exception as e:
                        errors.append({
                            'symbol': symbol,
                            'type': 'FETCH_ERROR',
                            'message': f"Error fetching trades: {str(e)}"
                        })
                        logging.error(f"Error fetching trades for {symbol}: {str(e)}")
                        continue

                # Sort trades by timestamp, most recent first
                all_trades.sort(key=lambda x: x['timestamp'], reverse=True)

                # Prepare response
                response = {
                    'success': True,
                    'data': {
                        'trades': all_trades
                    }
                }

                # Add errors if any occurred
                if errors:
                    response['warnings'] = errors

                # Ensure we have valid JSON data
                try:
                    # Validate JSON serialization
                    json_response = json.dumps(response)
                    print(json_response)
                except Exception as e:
                    error_response = {
                        'success': False,
                        'error': {
                            'code': 'SERIALIZATION_ERROR',
                            'message': 'Failed to serialize trades data',
                            'details': str(e)
                        }
                    }
                    print(json.dumps(error_response))
                    sys.exit(1)
                return

            except Exception as e:
                error_response = {
                    'success': False,
                    'error': {
                        'code': 'FETCH_ERROR',
                        'message': 'Failed to fetch trades',
                        'details': str(e)
                    }
                }
                print(json.dumps(error_response))
                sys.exit(1)

        if args.single_run:
            bot.run_single_analysis()
        else:
            bot.run()

    except Exception as e:
        error_response = {
            'success': False,
            'error': {
                'code': 'UNEXPECTED_ERROR',
                'message': 'An unexpected error occurred',
                'details': str(e)
            }
        }
        print(json.dumps(error_response))
        sys.exit(1)

if __name__ == '__main__':
    main()
