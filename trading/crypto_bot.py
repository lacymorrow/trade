import logging
import time
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
import pandas as pd
import numpy as np
from config import (
    ALPACA_CONFIG,
    CRYPTO_CONFIG,
    TRADING_CAPITAL,
    MAX_POSITION_SIZE,
    MAX_PORTFOLIO_EXPOSURE,
    VOLUME_MULTIPLIER_THRESHOLD,
    PRICE_WINDOW,
    SENTIMENT_CORRELATION_THRESHOLD
)
from sentiment_analyzer import SentimentAnalyzer
from trading.sanity_checks import SanityChecker
import requests

class CryptoBot:
    """
    CryptoBot class for cryptocurrency trading.

    This bot monitors cryptocurrency markets 24/7 and analyzes them for trading
    opportunities based on price movements, social sentiment, and technical
    indicators. It uses the Alpaca API for market data and trade execution.

    Key differences from stock trading:
    - 24/7 market monitoring
    - Crypto-specific indicators
    - Higher volatility thresholds
    - No market hours restrictions
    - Different volume patterns

    Attributes:
        test_mode (bool): Whether the bot is running in test mode
        symbols (list): List of crypto symbols to trade
        trading_api (alpaca_trade_api.REST): Alpaca API client
        sentiment_analyzer (SentimentAnalyzer): Analyzer for social sentiment
        running (bool): Whether the bot is currently running
        logger (logging.Logger): Logger for bot activities
    """

    def __init__(self, test_mode=False, symbols=None):
        """
        Initialize the crypto trading bot.

        Args:
            test_mode (bool): Whether to run in test mode (no real trades)
            symbols (list): Optional list of specific symbols to trade
        """
        self.logger = logging.getLogger(__name__)
        self.test_mode = test_mode
        self.running = False

        # Initialize APIs and components
        self._setup_apis()
        self._setup_components()

        # Set up trading symbols
        self.update_symbols(symbols)

        self.logger.info("Crypto bot initialized successfully")

    def _setup_apis(self):
        """Initialize API connections for trading and market data."""
        # Initialize Trading API
        self.trading_api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )

        # Initialize Crypto Data API with correct base URL
        self.data_api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            'https://data.alpaca.markets/v2',  # Use v2 endpoint directly
            api_version='v2'
        )

        self.logger.info("APIs initialized successfully")

    def _setup_components(self):
        """Initialize sentiment analyzer and other components."""
        self.sentiment_analyzer = SentimentAnalyzer()

    def update_symbols(self, symbols=None):
        """
        Update the list of crypto symbols to monitor.

        Args:
            symbols (list): Optional list of specific symbols to trade
        """
        try:
            if symbols:
                # Use provided symbols
                self.symbols = [f"{s}/USD" for s in symbols]
            else:
                # Use default crypto pairs
                self.symbols = [s.replace('USD', '/USD') for s in CRYPTO_CONFIG['DEFAULT_PAIRS']]

            if self.test_mode:
                # Limit to first few pairs in test mode
                self.symbols = self.symbols[:3]

            self.logger.info(f"Monitoring {len(self.symbols)} crypto pairs: {', '.join(self.symbols)}")

        except Exception as e:
            self.logger.error(f"Error updating symbols: {e}")
            # Fall back to major cryptos
            self.symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']

    def get_price_data(self, symbol, window):
        """
        Get historical price data for analysis.

        Args:
            symbol (str): The crypto symbol to get data for
            window (str): Time window for historical data

        Returns:
            pd.DataFrame: DataFrame with OHLCV data, or None if unavailable
        """
        try:
            self.logger.info(f"{symbol}: Fetching price data...")

            # Calculate time window
            end = pd.Timestamp.now(tz='UTC')
            start = end - pd.Timedelta(days=1)  # Get last 24 hours of data

            self.logger.info(f"{symbol}: Requesting data from {start} to {end}")

            # Get bars from Alpaca Crypto API using v2 endpoint
            url = 'https://data.alpaca.markets/v1beta3/crypto/us/bars'  # Use v1beta3 crypto endpoint
            headers = {
                'APCA-API-KEY-ID': ALPACA_CONFIG['API_KEY'],
                'APCA-API-SECRET-KEY': ALPACA_CONFIG['SECRET_KEY']
            }
            params = {
                'symbols': symbol,  # API expects BTC/USD format
                'timeframe': '1H',  # Use correct timeframe format
                'start': start.isoformat(),
                'end': end.isoformat()
            }

            self.logger.info(f"{symbol}: Making request to {url} with params: {params}")
            response = requests.get(url, headers=headers, params=params)

            if response.status_code != 200:
                self.logger.error(f"{symbol}: API Error - Status: {response.status_code}, Response: {response.text}")
                return None

            data = response.json()

            if not data or 'bars' not in data:
                self.logger.info(f"{symbol}: ❌ No data returned from API")
                return None

            # Convert bars to DataFrame
            bars = data['bars'].get(symbol, [])  # Use original symbol format
            if not bars:
                self.logger.info(f"{symbol}: ❌ No price data available")
                return None

            df_data = []
            for bar in bars:
                df_data.append({
                    'timestamp': pd.Timestamp(bar['t']),
                    'open': float(bar['o']),
                    'high': float(bar['h']),
                    'low': float(bar['l']),
                    'close': float(bar['c']),
                    'volume': float(bar['v'])
                })

            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            df = df.sort_index()  # Ensure chronological order

            # Add some debug info
            self.logger.info(f"{symbol}: Got {len(df)} bars")
            self.logger.info(f"{symbol}: Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            self.logger.info(f"{symbol}: Current price: ${df['close'].iloc[-1]:.2f}")

            return df

        except Exception as e:
            self.logger.error(f"{symbol}: ❌ Error getting price data: {str(e)}")
            self.logger.exception("Detailed error information:")
            return None

    def analyze_price_movement(self, price_data):
        """
        Analyze price movement for trading signals.

        Args:
            price_data (pd.DataFrame): OHLCV data for analysis

        Returns:
            tuple: (bool, float) indicating if movement is significant and the change
        """
        try:
            # Calculate price change
            current_price = price_data['close'].iloc[-1]
            previous_price = price_data['close'].iloc[0]
            price_change = (current_price - previous_price) / previous_price

            # Check if movement is significant (using crypto threshold)
            is_significant = abs(price_change) >= CRYPTO_CONFIG['MIN_PRICE_MOVEMENT']

            # For crypto, we also check volume surge
            current_volume = price_data['volume'].iloc[-1]
            avg_volume = price_data['volume'].mean()
            volume_multiplier = current_volume / avg_volume if avg_volume > 0 else 0

            # Movement is significant if price change OR volume spike
            is_significant = is_significant or (volume_multiplier >= CRYPTO_CONFIG['VOLUME_MULTIPLIER'])

            return is_significant, price_change

        except Exception as e:
            self.logger.error(f"Error analyzing price movement: {e}")
            return False, 0

    def analyze_trading_opportunity(self, symbol, price_data):
        """
        Analyze a crypto pair for trading opportunities.

        Performs comprehensive analysis including:
        - Price movement analysis
        - Social sentiment analysis
        - Volume analysis
        - Technical indicators

        Args:
            symbol (str): The crypto symbol to analyze
            price_data (pd.DataFrame): OHLCV data for the symbol

        Returns:
            tuple: (bool, dict) indicating if opportunity exists and trade details
        """
        try:
            current_price = price_data['close'].iloc[-1]
            self.logger.info(f"{symbol}: Current price: ${current_price:.2f}")

            # Check for significant price movement
            is_significant, price_change = self.analyze_price_movement(price_data)
            if not is_significant:
                self.logger.info(f"{symbol}: ❌ No significant movement (Change: {price_change:.2%})")
                return False, None

            self.logger.info(f"{symbol}: ✓ Significant movement detected (Change: {price_change:.2%})")

            # Check social activity
            self.logger.info(f"{symbol}: Checking social activity...")
            base_symbol = symbol.replace('USD', '')  # Remove USD suffix for sentiment analysis
            is_active, activity_score = self.sentiment_analyzer.analyze_social_activity(base_symbol)
            if not is_active:
                self.logger.info(f"{symbol}: ❌ Low social activity (Score: {activity_score:.2f})")
                return False, None

            self.logger.info(f"{symbol}: ✓ High social activity detected (Score: {activity_score:.2f})")

            # Check for sentiment correlation
            self.logger.info(f"{symbol}: Analyzing sentiment correlation...")
            is_overreaction, correlation = self.sentiment_analyzer.detect_overreaction(base_symbol, price_data)
            if not is_overreaction:
                self.logger.info(f"{symbol}: ❌ No sentiment overreaction (Correlation: {correlation:.2f})")
                return False, None

            self.logger.info(f"{symbol}: ✓ Sentiment overreaction detected!")
            self.logger.info(f"  - Correlation: {correlation:.2f}")

            # Trading opportunity found!
            self.logger.info(f"\n🎯 TRADING OPPORTUNITY FOUND FOR {symbol}")
            self.logger.info(f"Summary:")
            self.logger.info(f"- Price: ${current_price:.2f}")
            self.logger.info(f"- Price Change: {price_change:.2%}")
            self.logger.info(f"- Social Activity Score: {activity_score:.2f}")
            self.logger.info(f"- Sentiment Correlation: {correlation:.2f}")

            # Prepare trading signal
            signal = {
                'symbol': symbol,
                'price_change': price_change,
                'activity_score': activity_score,
                'correlation': correlation,
                'side': 'sell' if correlation > 0 else 'buy'
            }

            self.logger.info(f"Recommended Action: {signal['side'].upper()}")
            return True, signal

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return False, None

    def analyze_symbol(self, symbol):
        """
        Analyze a single crypto pair for trading opportunities.

        Args:
            symbol (str): The crypto symbol to analyze
        """
        try:
            # Get price data
            price_data = self.get_price_data(symbol, PRICE_WINDOW)
            if price_data is None:
                return

            # Analyze for trading opportunities
            has_opportunity, signal = self.analyze_trading_opportunity(symbol, price_data)

            if has_opportunity and not self.test_mode:
                self.execute_trade(signal)
            elif has_opportunity and self.test_mode:
                self.logger.info(f"TEST MODE: Would execute {signal['side']} trade for {symbol}")

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")

    def execute_trade(self, signal):
        """
        Execute a crypto trade based on the signal.

        Args:
            signal (dict): Trading signal with trade details
        """
        try:
            symbol = signal['symbol']
            side = signal['side']

            # Get current price
            quote = self.trading_api.get_latest_crypto_quote(symbol)
            price = float(quote.ask_price if side == 'buy' else quote.bid_price)

            # Calculate position size
            max_position = min(
                TRADING_CAPITAL * MAX_POSITION_SIZE,
                TRADING_CAPITAL * MAX_PORTFOLIO_EXPOSURE
            )

            # Ensure minimum trade size
            if max_position < CRYPTO_CONFIG['MIN_TRADE_SIZE']:
                self.logger.warning(f"Position size {max_position:.2f} below minimum {CRYPTO_CONFIG['MIN_TRADE_SIZE']}")
                return

            # Check spread
            spread = (quote.ask_price - quote.bid_price) / quote.ask_price
            if spread > CRYPTO_CONFIG['MAX_SPREAD_PCT']:
                self.logger.warning(f"Spread {spread:.2%} too high (max {CRYPTO_CONFIG['MAX_SPREAD_PCT']:.2%})")
                return

            # For crypto, we use notional value instead of shares
            qty = max_position / price

            # Place the order
            self.trading_api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )

            self.logger.info(f"Executed {side.upper()} order for {symbol}")
            self.logger.info(f"Quantity: {qty:.8f}")
            self.logger.info(f"Price: ${price:.2f}")
            self.logger.info(f"Total Value: ${qty * price:.2f}")

        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")

    def start(self):
        """
        Start the crypto trading bot.

        Main loop that:
        1. Updates symbol list
        2. Analyzes each crypto pair
        3. Executes trades if opportunities found

        Note: Crypto markets are 24/7, so no market hours check needed
        """
        self.logger.info("Starting crypto trading bot...")
        self.running = True

        while self.running:
            try:
                # Update symbol list periodically
                self.update_symbols()

                # Analyze each symbol
                self.logger.info(f"Analyzing {len(self.symbols)} crypto pairs...")
                for symbol in self.symbols:
                    if not self.running:
                        break

                    self.analyze_symbol(symbol)

                # Wait before next iteration
                time.sleep(60)  # Run analysis every minute

            except KeyboardInterrupt:
                self.logger.info("Shutting down crypto trading bot...")
                self.running = False
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying
