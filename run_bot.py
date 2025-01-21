import ssl
import urllib3

# Disable SSL verification (for testing only)
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

import argparse
import json
import os
import sys
import logging
from dotenv import load_dotenv
from trading.bots.crypto_bot import CryptoBot
from trading.bots.stock_bot import StockBot
from flask import Flask, jsonify, request
from waitress import serve
from functools import wraps

def setup_logging():
    """Configure logging to show all levels."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Initialize global variables
bot = None
bot_type = None

app = Flask(__name__)

def add_cors_headers(response):
    """Add CORS headers to the response."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'  # Cache preflight response for 1 hour
    return response

@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    return add_cors_headers(response)

@app.route('/health')
def health_check():
    """Handle OPTIONS request for health check."""
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))
    return jsonify({'status': 'healthy'})

@app.route('/trades', methods=['GET', 'OPTIONS'])
def get_trades():
    """Get recent trades from the bot."""
    logging.info("Trades endpoint called")  # Debug log

    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))

    if bot is None:
        logging.warning("Bot is not running")  # Debug log
        return jsonify({
            'success': False,
            'error': {
                'code': 'BOT_NOT_RUNNING',
                'message': 'Bot is not running'
            }
        }), 400

    try:
        logging.info("Fetching trades for symbols")  # Debug log
        # Get trades for all supported symbols
        trades = []
        for symbol in ['BTC', 'ETH']:  # Add more symbols as needed
            logging.info(f"Fetching trades for {symbol}")  # Debug log
            symbol_trades = bot.data_engine.get_recent_trades(symbol)
            if symbol_trades is not None:
                for _, trade in symbol_trades.iterrows():
                    trades.append({
                        'id': f"{trade.name.strftime('%Y-%m-%dT%H:%M:%SZ')}-{symbol}",
                        'timestamp': trade.name.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'symbol': f"{symbol}/USD",
                        'side': trade['side'],
                        'price': float(trade['price']),
                        'quantity': float(trade['size'])
                    })

        logging.info(f"Found {len(trades)} trades")  # Debug log
        return jsonify({
            'success': True,
            'data': {
                'trades': sorted(trades, key=lambda x: x['timestamp'], reverse=True)
            }
        })
    except Exception as e:
        logging.error(f"Error fetching trades: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'FETCH_ERROR',
                'message': 'Error fetching trades',
                'details': str(e)
            }
        }), 500

@app.route('/start', methods=['POST', 'OPTIONS'])
def start_bot():
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))

    global bot
    if bot is None:
        try:
            # Load environment variables from .env file
            load_dotenv()

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
                return jsonify(error_response), 400

            # Create the bot based on type
            if bot_type == 'crypto':
                bot = CryptoBot(
                    api_key=api_key,
                    api_secret=api_secret,
                    base_url=base_url
                )
            elif bot_type == 'stock':
                bot = StockBot(
                    api_key=api_key,
                    api_secret=api_secret,
                    base_url=base_url
                )
            else:
                error_response = {
                    'success': False,
                    'error': {
                        'code': 'INVALID_BOT_TYPE',
                        'message': f'Invalid bot type: {bot_type}'
                    }
                }
                return jsonify(error_response), 400

            # Start the bot in a background thread
            import threading
            bot_thread = threading.Thread(target=bot.start, daemon=True)
            bot_thread.start()

            return jsonify({'success': True, 'message': 'Bot started successfully'})
        except Exception as e:
            error_response = {
                'success': False,
                'error': {
                    'code': 'UNEXPECTED_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }
            }
            return jsonify(error_response), 500
    else:
        return jsonify({'success': False, 'message': 'Bot is already running'}), 400

@app.route('/stop', methods=['POST', 'OPTIONS'])
def stop_bot():
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))

    global bot
    if bot is not None:
        try:
            bot.stop()
            bot = None
            return jsonify({'success': True, 'message': 'Bot stopped successfully'})
        except Exception as e:
            error_response = {
                'success': False,
                'error': {
                    'code': 'UNEXPECTED_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }
            }
            return jsonify(error_response), 500
    else:
        return jsonify({'success': False, 'message': 'Bot is not running'}), 400

@app.route('/status', methods=['GET', 'OPTIONS'])
def bot_status():
    """Handle OPTIONS request for status check."""
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))
    return jsonify({
        'success': True,
        'status': 'running' if bot is not None else 'stopped',
        'type': bot_type
    })

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    """Run analysis on all symbols."""
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))

    global bot
    if bot is None:
        return jsonify({
            'success': False,
            'error': {
                'code': 'BOT_NOT_RUNNING',
                'message': 'Bot is not running'
            }
        }), 400

    try:
        # Run analysis using the correct method
        if isinstance(bot, CryptoBot):
            bot.analyze_symbols()  # Use analyze_symbols for CryptoBot
        else:
            bot.analyze_all_symbols()  # Use analyze_all_symbols for other bots

        return jsonify({
            'success': True,
            'message': 'Analysis completed successfully'
        })
    except Exception as e:
        logging.error(f"Error running analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ANALYSIS_ERROR',
                'message': 'Error running analysis',
                'details': str(e)
            }
        }), 500

def run_bot(bot_type_arg, live_mode=False):
    global bot
    # Load environment variables from .env file
    load_dotenv()

    # Get API credentials from environment variables
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL')

    if not api_key or not api_secret:
        logging.error('Missing API credentials. Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.')
        sys.exit(1)

    # Create and start the bot
    try:
        if bot_type_arg == 'crypto':
            bot = CryptoBot(
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url,
                test_mode=not live_mode  # Set test_mode based on live_mode flag
            )
        elif bot_type_arg == 'stock':
            bot = StockBot(
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url,
                test_mode=not live_mode  # Set test_mode based on live_mode flag
            )
        else:
            logging.error(f'Invalid bot type: {bot_type_arg}')
            sys.exit(1)

        # Log the mode
        logging.info(f"Starting bot in {'LIVE' if live_mode else 'TEST'} mode")
        bot.start()
    except Exception as e:
        logging.error(f'Error starting bot: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    # Set up logging
    setup_logging()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run trading bot')
    parser.add_argument('--bot-type', choices=['crypto', 'stock'], help='Type of bot to run')
    parser.add_argument('--server-only', action='store_true', help='Run only the Flask server')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 8080)), help='Port to run the server on')
    parser.add_argument('--live', action='store_true', help='Run in live trading mode (default: test mode)')
    args = parser.parse_args()

    # Set the bot type from environment variable or command line argument
    bot_type = args.bot_type or os.getenv('BOT_TYPE')

    if args.server_only:
        # Run only the Flask server
        logging.info(f'Starting Flask server on port {args.port} with bot type: {bot_type}')
        # Log all registered routes
        logging.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logging.info(f"{rule.endpoint}: {rule.methods} {rule.rule}")
        serve(app, host='0.0.0.0', port=args.port)
    elif args.bot_type:
        # Run the specified bot
        run_bot(args.bot_type, live_mode=args.live)
    else:
        parser.print_help()
        sys.exit(1)
