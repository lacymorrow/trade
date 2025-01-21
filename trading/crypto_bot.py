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

    def __init__(self, test_mode=True, symbols=None, force_trade=False):
        """
        Initialize the crypto trading bot.

        Args:
            test_mode (bool): Whether to run in test mode (no real trades)
            symbols (list): Optional list of specific symbols to trade
            force_trade (bool): Whether to force a trade decision
        """
        self.test_mode = test_mode
        self.force_trade = force_trade
        self.logger = logging.getLogger(__name__)
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

            # Get bars from Alpaca Crypto API using v1beta3 endpoint
            url = 'https://data.alpaca.markets/v1beta3/crypto/us/bars'
            headers = {
                'APCA-API-KEY-ID': ALPACA_CONFIG['API_KEY'],
                'APCA-API-SECRET-KEY': ALPACA_CONFIG['SECRET_KEY']
            }
            params = {
                'symbols': [symbol],  # API expects array of symbols
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
            bars = data['bars'].get(symbol, [])  # Get bars for the symbol
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
        Analyze if there's a trading opportunity for the given symbol.

        Args:
            symbol (str): The crypto symbol to analyze
            price_data (pd.DataFrame): Historical price data

        Returns:
            tuple: (should_trade, trade_type, reason)
        """
        if price_data is None or len(price_data) < 2:
            return False, None, "Insufficient price data"

        current_price = price_data['close'].iloc[-1]
        prev_price = price_data['close'].iloc[-2]
        price_change = (current_price - prev_price) / prev_price

        self.logger.info(f"{symbol}: Current price: ${current_price:.2f}")

        # Get current position
        try:
            position = self.trading_api.get_position(symbol.replace('/', ''))
            has_position = True
            position_size = float(position.qty)
            position_value = float(position.market_value)
        except Exception:
            has_position = False
            position_size = 0
            position_value = 0

        if not self.force_trade:
            # Normal trading logic
            if abs(price_change) < CRYPTO_CONFIG['MIN_PRICE_MOVEMENT']:
                return False, None, f"No significant movement (Change: {price_change:.2%})"

            if price_change > 0 and not has_position:
                return True, "buy", f"Price up {price_change:.2%}"
            elif price_change < 0 and has_position:
                return True, "sell", f"Price down {price_change:.2%}"

            return False, None, "No trading opportunity"
        else:
            # Forced trade logic - make a decision based on technical analysis
            self.logger.info(f"{symbol}: Force trade mode - Analyzing best trade option")

            # Calculate technical indicators
            closes = price_data['close']
            volumes = price_data['volume']

            # Calculate RSI
            rsi = self.calculate_rsi(closes)

            # Calculate MACD
            exp1 = closes.ewm(span=CRYPTO_CONFIG['MACD_FAST'], adjust=False).mean()
            exp2 = closes.ewm(span=CRYPTO_CONFIG['MACD_SLOW'], adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=CRYPTO_CONFIG['MACD_SIGNAL'], adjust=False).mean()

            # Calculate SMAs
            sma_short = closes.rolling(window=CRYPTO_CONFIG['SMA_SHORT_PERIOD']).mean().iloc[-1]
            sma_long = closes.rolling(window=CRYPTO_CONFIG['SMA_LONG_PERIOD']).mean().iloc[-1]

            # Calculate volume trend
            avg_volume = volumes.mean()
            current_volume = volumes.iloc[-1]
            volume_ratio = current_volume / avg_volume

            # Log technical analysis
            self.logger.info(f"{symbol}: Technical Analysis:")
            self.logger.info(f"- Price Change: {price_change:.2%}")
            self.logger.info(f"- RSI: {rsi:.2f}")
            self.logger.info(f"- MACD: {macd.iloc[-1]:.2f}")
            self.logger.info(f"- Signal: {signal.iloc[-1]:.2f}")

            # Score different factors
            trend_score = 1 if sma_short > sma_long else -1
            momentum_score = 1 if rsi > 50 else -1
            macd_score = 1 if macd.iloc[-1] > signal.iloc[-1] else -1
            volume_score = 1 if volume_ratio > 1 else -1

            # Calculate weighted score
            total_score = (
                trend_score * CRYPTO_CONFIG['WEIGHT_TREND'] +
                momentum_score * CRYPTO_CONFIG['WEIGHT_MOMENTUM'] +
                macd_score * CRYPTO_CONFIG['WEIGHT_MOMENTUM'] +
                volume_score * CRYPTO_CONFIG['WEIGHT_VOLUME']
            )

            self.logger.info(f"- Trend Score: {trend_score:.2f}")
            self.logger.info(f"- Volume Score: {volume_score:.2f}")
            self.logger.info(f"{symbol}: Total Analysis Score: {abs(total_score):.2f}")

            # Make trading decision
            if has_position:
                # We have a position - decide whether to hold or sell
                if total_score < -0.2:  # Threshold for selling
                    return True, "sell", f"Bearish signals (Score: {total_score:.2f})"
                else:
                    return False, None, f"Holding position (Score: {total_score:.2f})"
            else:
                # We don't have a position - decide whether to buy
                if total_score > 0.2:  # Threshold for buying
                    return True, "buy", f"Bullish signals (Score: {total_score:.2f})"
                else:
                    return False, None, f"No clear buy signal (Score: {total_score:.2f})"

    def calculate_technical_indicators(self, price_data):
        """Calculate technical indicators for analysis."""
        try:
            # RSI
            rsi = self.calculate_rsi(price_data['close'])

            # Moving Averages
            sma_short = price_data['close'].rolling(window=CRYPTO_CONFIG['SMA_SHORT_PERIOD']).mean()
            sma_long = price_data['close'].rolling(window=CRYPTO_CONFIG['SMA_LONG_PERIOD']).mean()

            # MACD
            ema_fast = price_data['close'].ewm(span=CRYPTO_CONFIG['MACD_FAST']).mean()
            ema_slow = price_data['close'].ewm(span=CRYPTO_CONFIG['MACD_SLOW']).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=CRYPTO_CONFIG['MACD_SIGNAL']).mean()

            # Volume analysis
            volume_sma = price_data['volume'].rolling(window=CRYPTO_CONFIG['SMA_SHORT_PERIOD']).mean()
            current_volume = price_data['volume'].iloc[-1]
            volume_ratio = current_volume / volume_sma.iloc[-1]

            # Volatility
            returns = price_data['close'].pct_change()
            volatility = returns.std()

            # Calculate scores
            trend_score = 1 if sma_short.iloc[-1] > sma_long.iloc[-1] else -1
            momentum_score = (
                (1 if rsi > 50 else -1) * 0.5 +
                (1 if macd.iloc[-1] > macd_signal.iloc[-1] else -1) * 0.5
            )
            volume_score = min(1, volume_ratio / CRYPTO_CONFIG['VOLUME_MULTIPLIER'])
            volatility_score = min(1, volatility * 100)  # Normalize volatility

            return {
                'rsi': rsi,
                'macd': macd.iloc[-1],
                'macd_signal': macd_signal.iloc[-1],
                'trend_score': trend_score,
                'momentum_score': momentum_score,
                'volume_score': volume_score,
                'volatility_score': volatility_score
            }

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {str(e)}")
            return {
                'rsi': 50,
                'macd': 0,
                'macd_signal': 0,
                'trend_score': 0,
                'momentum_score': 0,
                'volume_score': 0,
                'volatility_score': 0
            }

    def calculate_rsi(self, prices, periods=14):
        """Calculate RSI technical indicator."""
        try:
            deltas = np.diff(prices)
            seed = deltas[:periods+1]
            up = seed[seed >= 0].sum()/periods
            down = -seed[seed < 0].sum()/periods
            if down == 0:  # Handle division by zero
                rs = 100
            else:
                rs = up/down
            rsi = np.zeros_like(prices)
            rsi[:periods] = 100. - 100./(1. + rs)

            for i in range(periods, len(prices)):
                delta = deltas[i - 1]
                if delta > 0:
                    upval = delta
                    downval = 0.
                else:
                    upval = 0.
                    downval = -delta

                up = (up*(periods - 1) + upval)/periods
                down = (down*(periods - 1) + downval)/periods
                if down == 0:  # Handle division by zero
                    rs = 100
                else:
                    rs = up/down
                rsi[i] = 100. - 100./(1. + rs)

            return rsi[-1]  # Return the last RSI value

        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return 50  # Return neutral RSI on error

    def execute_trade(self, symbol, trade_type, price_data):
        """
        Execute a trade for the given symbol.

        Args:
            symbol (str): The crypto symbol to trade
            trade_type (str): Type of trade ('buy' or 'sell')
            price_data (pd.DataFrame): Historical price data

        Returns:
            bool: Whether the trade was successful
        """
        try:
            current_price = price_data['close'].iloc[-1]
            api_symbol = symbol.replace('/', '')

            # Calculate position size
            account = self.trading_api.get_account()
            buying_power = float(account.buying_power)
            position_size = min(
                buying_power * CRYPTO_CONFIG['MAX_POSITION_SIZE'],
                CRYPTO_CONFIG['MAX_TRADE_VALUE']
            )

            if trade_type == "buy":
                qty = position_size / current_price
                qty = round(qty, 8)  # Round to 8 decimal places for crypto

                if self.test_mode:
                    self.logger.info(f"TEST MODE - Would submit order: Buy {qty} {symbol} @ ${current_price:.2f}")
                    return True

                # Submit market buy order
                self.trading_api.submit_order(
                    symbol=api_symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                self.logger.info(f"✅ Submitted buy order for {qty} {symbol} @ ${current_price:.2f}")

            elif trade_type == "sell":
                try:
                    position = self.trading_api.get_position(api_symbol)
                    qty = float(position.qty)

                    if self.test_mode:
                        self.logger.info(f"TEST MODE - Would submit order: Sell {qty} {symbol} @ ${current_price:.2f}")
                        return True

                    # Submit market sell order
                    self.trading_api.submit_order(
                        symbol=api_symbol,
                        qty=qty,
                        side='sell',
                        type='market',
                        time_in_force='gtc'
                    )
                    self.logger.info(f"✅ Submitted sell order for {qty} {symbol} @ ${current_price:.2f}")

                except Exception as e:
                    self.logger.error(f"No position found for {symbol}: {str(e)}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to execute {trade_type} trade for {symbol}: {str(e)}")
            self.logger.exception("Detailed error information:")
            return False

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
            should_trade, trade_type, reason = self.analyze_trading_opportunity(symbol, price_data)

            if should_trade:
                self.logger.info(f"{symbol}: Trade opportunity found - {reason}")
                if self.test_mode:
                    self.logger.info(f"TEST MODE: Would execute {trade_type} trade for {symbol}")
                else:
                    success = self.execute_trade(symbol, trade_type, price_data)
                    if success:
                        self.logger.info(f"{symbol}: Successfully executed {trade_type} trade")
                    else:
                        self.logger.error(f"{symbol}: Failed to execute {trade_type} trade")
            else:
                self.logger.info(f"{symbol}: No trade opportunity - {reason}")

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")

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
