import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
import time
from .sanity_checks import SanityChecker
from sentiment_analyzer import SentimentAnalyzer
from config import (
    ALPACA_CONFIG,
    MAX_POSITION_SIZE,
    MAX_PORTFOLIO_EXPOSURE,
    MIN_PRICE_MOVEMENT,
    MAX_PRICE_MOVEMENT,
    VOLUME_MULTIPLIER_THRESHOLD,
    PRICE_WINDOW,
    SENTIMENT_CORRELATION_THRESHOLD
)

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TradingBot:
    """
    TradingBot class that implements a sentiment-driven trading strategy.

    This bot monitors StockTwits for trending stocks and analyzes them for trading
    opportunities based on price movements, social sentiment, and technical indicators.
    It uses the Alpaca API for market data and trade execution.

    Attributes:
        test_mode (bool): Whether the bot is running in test mode (no real trades)
        trading_api (alpaca_trade_api.REST): Alpaca API client for trading
        data_api (alpaca_trade_api.REST): Alpaca API client for market data
        sentiment_analyzer (SentimentAnalyzer): Analyzer for social media sentiment
        sanity_checker (SanityChecker): Checker for trade safety conditions
        symbols (list): List of symbols currently being monitored
        running (bool): Whether the bot is currently running
        logger (logging.Logger): Logger for bot activities

    Configuration:
        The bot's behavior is controlled by parameters in config.py, including:
        - Trading capital and position limits
        - Price movement thresholds
        - Sentiment analysis parameters
        - Safety check thresholds
    """

    def __init__(self, test_mode=False):
        """
        Initialize the trading bot.

        Args:
            test_mode (bool): Whether to run in test mode (no real trades)
        """
        self.logger = logging.getLogger(__name__)
        self.test_mode = test_mode
        self._setup_apis()
        self._setup_components()
        self.update_symbols()
        self.logger.info("Initialization complete. Ready to start trading.")

    def _setup_apis(self):
        """Initialize API connections for trading and market data."""
        # Initialize Trading API
        self.trading_api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )

        # Initialize Data API with sandbox URL
        self.data_api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['DATA_URL']
        )

        self.logger.info("APIs initialized successfully")

    def _setup_components(self):
        """Initialize sentiment analyzer and sanity checker components."""
        self.sentiment_analyzer = SentimentAnalyzer()
        self.sanity_checker = SanityChecker(self.trading_api)

    def update_symbols(self):
        """
        Update the list of symbols to monitor.

        Fetches trending stocks from StockTwits and filters them based on
        trading criteria. Falls back to default symbols if no trending stocks
        are found or in test mode.
        """
        try:
            # Get trending stocks from StockTwits
            trending_stocks = self.sentiment_analyzer.get_trending_stocks()

            if trending_stocks:
                self.logger.info(f"Found {len(trending_stocks)} trending stocks on StockTwits")
                self.symbols = trending_stocks
            else:
                self.logger.warning("No trending stocks found, using default list")
                self.symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
                              'NVDA', 'TSLA', 'JPM', 'BAC', 'GS']

            if self.test_mode:
                self.logger.info(f"Test mode: Using first 10 symbols")
                self.symbols = self.symbols[:10]

            self.logger.info(f"Monitoring {len(self.symbols)} symbols: {', '.join(self.symbols)}")

        except Exception as e:
            self.logger.error(f"Error updating symbols: {e}")
            # Fall back to default symbols
            self.symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
                          'NVDA', 'TSLA', 'JPM', 'BAC', 'GS']

    def get_price_data(self, symbol, window):
        """
        Get historical price data for analysis.

        Args:
            symbol (str): The stock symbol to get data for
            window (str): Time window for historical data (e.g., "2h")

        Returns:
            pd.DataFrame: DataFrame with OHLCV data, or None if data unavailable
        """
        try:
            self.logger.info(f"{symbol}: Fetching price data...")

            # Calculate time window
            end = pd.Timestamp.now(tz='America/New_York')
            start = end - pd.Timedelta(days=1)  # Get last 24 hours of data

            # Get bars from Alpaca Data API
            bars = self.data_api.get_bars(
                symbol,
                TimeFrame.Hour,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                adjustment='raw',
                feed='iex'  # Use IEX feed explicitly
            ).df

            if bars is None or len(bars) == 0:
                self.logger.info(f"{symbol}: ❌ No price data available")
                return None

            # Add some debug info
            self.logger.info(f"{symbol}: Got {len(bars)} bars")
            self.logger.info(f"{symbol}: Price range: ${bars['low'].min():.2f} - ${bars['high'].max():.2f}")
            self.logger.info(f"{symbol}: Current price: ${bars['close'].iloc[-1]:.2f}")

            return bars

        except Exception as e:
            self.logger.error(f"{symbol}: ❌ Error getting price data: {str(e)}")
            return None

    def analyze_price_movement(self, price_data):
        """Analyze price movement and volume"""
        try:
            if price_data is None or len(price_data) < 2:
                return False, 0

            # Calculate price change
            current_price = price_data['close'].iloc[-1]
            start_price = price_data['close'].iloc[0]
            price_change = (current_price - start_price) / start_price

            # Calculate volume change
            current_volume = price_data['volume'].iloc[-1]
            avg_volume = price_data['volume'].mean()

            # Avoid division by zero
            if avg_volume > 0:
                volume_multiplier = current_volume / avg_volume
            else:
                volume_multiplier = 0

            # Check if movement is significant
            is_significant = (
                abs(price_change) >= MIN_PRICE_MOVEMENT and
                abs(price_change) <= MAX_PRICE_MOVEMENT and
                volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD
            )

            return is_significant, price_change

        except Exception as e:
            self.logger.error(f"Error analyzing price movement: {e}")
            return False, 0

    def calculate_position_size(self, correlation, price, equity):
        """Calculate position size based on correlation strength"""
        try:
            # Base size on correlation strength
            correlation_factor = abs(correlation) / SENTIMENT_CORRELATION_THRESHOLD

            # Calculate maximum position value
            max_position = equity * MAX_POSITION_SIZE

            # Scale position by correlation
            position_value = max_position * correlation_factor

            # Calculate number of shares
            shares = int(position_value / price)

            return shares

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0

    def check_portfolio_exposure(self):
        """Check current portfolio exposure"""
        try:
            account = self.trading_api.get_account()
            positions = self.trading_api.list_positions()

            # Calculate total exposure
            total_position_value = sum(float(p.market_value) for p in positions)
            equity = float(account.equity)

            exposure = total_position_value / equity
            return exposure <= MAX_PORTFOLIO_EXPOSURE

        except Exception as e:
            self.logger.error(f"Error checking portfolio exposure: {e}")
            return False

    def execute_trade(self, symbol, side, shares, correlation):
        """Execute trade with proper risk management"""
        try:
            # Get current price for stop loss/take profit
            last_quote = self.trading_api.get_last_quote(symbol)
            current_price = (last_quote.askprice + last_quote.bidprice) / 2

            # Calculate stop loss and take profit based on correlation
            correlation_abs = abs(correlation)
            stop_distance = 0.02 * (1 + correlation_abs)  # Dynamic based on correlation
            profit_distance = 0.04 * (1 + correlation_abs)

            stop_price = current_price * (1 - stop_distance) if side == 'buy' else current_price * (1 + stop_distance)
            take_profit = current_price * (1 + profit_distance) if side == 'buy' else current_price * (1 - profit_distance)

            # Place the main order
            order = self.trading_api.submit_order(
                symbol=symbol,
                qty=shares,
                side=side,
                type='limit',
                time_in_force='day',
                limit_price=current_price,
                order_class='bracket',
                stop_loss={'stop_price': stop_price},
                take_profit={'limit_price': take_profit}
            )

            self.logger.info(f"Executed {side} order for {shares} shares of {symbol}")
            self.logger.info(f"Entry: {current_price}, Stop: {stop_price}, Target: {take_profit}")

            return order

        except Exception as e:
            self.logger.error(f"Error executing trade for {symbol}: {e}")
            return None

    def analyze_trading_opportunity(self, symbol, price_data):
        """
        Analyze a symbol for trading opportunities.

        Performs comprehensive analysis including:
        - Price movement analysis
        - Social sentiment analysis
        - Safety checks

        Args:
            symbol (str): The stock symbol to analyze
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
            is_active, activity_score = self.sentiment_analyzer.analyze_social_activity(symbol)
            if not is_active:
                self.logger.info(f"{symbol}: ❌ Low social activity (Score: {activity_score:.2f})")
                return False, None

            self.logger.info(f"{symbol}: ✓ High social activity detected (Score: {activity_score:.2f})")

            # Run sanity checks
            self.logger.info(f"{symbol}: Running sanity checks...")
            passes_checks, check_results = self.sanity_checker.run_all_checks(symbol, price_data)
            if not passes_checks:
                self.logger.info(f"{symbol}: ❌ Failed sanity checks")
                for check, result in check_results.items():
                    self.logger.info(f"  - {check}: {'✓' if result else '❌'}")
                return False, None

            self.logger.info(f"{symbol}: ✓ Passed all sanity checks")

            # Check for sentiment correlation
            self.logger.info(f"{symbol}: Analyzing sentiment correlation...")
            is_overreaction, correlation = self.sentiment_analyzer.detect_overreaction(symbol, price_data)
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

    def run_trading_logic(self):
        """Main trading logic"""
        self.logger.info("Starting trading bot...")

        while True:
            try:
                # Check if market is open
                clock = self.trading_api.get_clock()
                if not clock.is_open:
                    self.logger.info("Market is closed. Waiting...")
                    time.sleep(60)
                    continue

                # Check portfolio exposure
                if not self.check_portfolio_exposure():
                    self.logger.warning("Maximum portfolio exposure reached")
                    time.sleep(60)
                    continue

                # Get fresh list of stocks to monitor
                self.symbols = self._initialize_symbols()

                # Analyze each symbol
                for symbol in self.symbols:
                    try:
                        self.logger.info(f"\n{'='*50}")
                        self.logger.info(f"Analyzing {symbol}...")

                        # Get price data
                        price_data = self.get_price_data(symbol, PRICE_WINDOW)
                        if price_data is None:
                            continue

                        # Analyze for trading opportunity
                        has_opportunity, signal = self.analyze_trading_opportunity(symbol, price_data)

                        if has_opportunity:
                            # Calculate position size
                            account = self.trading_api.get_account()
                            shares = self.calculate_position_size(
                                signal['correlation'],
                                price_data['close'].iloc[-1],
                                float(account.equity)
                            )

                            if shares > 0:
                                # Execute the trade
                                order = self.execute_trade(
                                    symbol,
                                    signal['side'],
                                    shares,
                                    signal['correlation']
                                )
                                if order:
                                    self.logger.info(f"✓ Successfully placed {signal['side']} order for {symbol}")

                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")
                        continue

                self.logger.info("\nWaiting for next analysis cycle...")
                time.sleep(60)  # Wait 1 minute before next cycle

            except Exception as e:
                self.logger.error(f"Error in main trading loop: {e}")
                time.sleep(60)

    def _is_market_open(self):
        """Check if the market is currently open"""
        try:
            clock = self.trading_api.get_clock()
            return clock.is_open
        except Exception as e:
            self.logger.error(f"Error checking market hours: {e}")
            return False

    def analyze_symbol(self, symbol):
        """
        Analyze a single symbol for trading opportunities.

        Args:
            symbol (str): The stock symbol to analyze
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

    def start(self):
        """
        Start the trading bot.

        Main loop that:
        1. Updates symbol list
        2. Checks market hours
        3. Analyzes each symbol
        4. Executes trades if opportunities found
        """
        self.logger.info("Starting trading bot...")
        self.running = True

        while self.running:
            try:
                # Update symbol list every hour
                self.update_symbols()

                # Check if market is open
                is_open = self._is_market_open()
                if not is_open and not self.test_mode:
                    self.logger.info("Market is closed. Waiting...")
                    time.sleep(60)  # Check again in 1 minute
                    continue

                if not is_open:
                    self.logger.info("Market is closed but running analysis in test mode...")

                # Analyze each symbol
                self.logger.info(f"Analyzing {len(self.symbols)} symbols...")
                for symbol in self.symbols:
                    if not self.running:
                        break

                    self.analyze_symbol(symbol)

                # Wait before next iteration
                time.sleep(60)  # Run analysis every minute

            except KeyboardInterrupt:
                self.logger.info("Shutting down trading bot...")
                self.running = False
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying
