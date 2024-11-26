import logging
import time
from datetime import datetime
from crypto_config import TRADING_PAIRS, DEFAULT_TIMEFRAME
from .data_engine import CryptoDataEngine
from .signal_engine import CryptoSignalEngine
from .trade_engine import CryptoTradeEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoBot:
    def __init__(self, config=None):
        self.config = config or {}
        self.data_engine = CryptoDataEngine()
        self.signal_engine = CryptoSignalEngine(self.data_engine)
        self.trade_engine = CryptoTradeEngine()
        self.is_running = False
        self.trading_pairs = self.config.get('trading_pairs', TRADING_PAIRS)
        self.timeframe = self.config.get('timeframe', DEFAULT_TIMEFRAME)

    def initialize(self):
        """Initialize the bot and check all components."""
        try:
            logger.info("Initializing CryptoBot...")

            # Check exchange connection
            markets = self.data_engine.exchange.load_markets()
            logger.info(f"Connected to exchange. {len(markets)} markets available.")

            # Check account balance
            balance = self.trade_engine.get_balance()
            if balance:
                logger.info(f"Account balance: {balance['free']} USDT available")
            else:
                logger.error("Could not fetch account balance")
                return False

            # Validate trading pairs
            available_pairs = set(markets.keys())
            self.trading_pairs = [pair for pair in self.trading_pairs if pair in available_pairs]
            logger.info(f"Trading pairs validated. Trading on: {', '.join(self.trading_pairs)}")

            return True

        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}")
            return False

    def process_signals(self):
        """Process trading signals for all pairs."""
        try:
            for pair in self.trading_pairs:
                # Generate signal
                signal = self.signal_engine.generate_signal(pair, self.timeframe)
                if not signal:
                    continue

                # Log signal information
                logger.info(f"Signal for {pair}: {signal['action']} (Strength: {signal['strength']})")
                logger.info(f"Reasons: {', '.join(signal['reasons'])}")

                # Execute signal if strong enough
                if abs(signal['strength']) >= 3:
                    order = self.trade_engine.execute_signal(signal)
                    if order:
                        logger.info(f"Executed {signal['action']} order for {pair}")

        except Exception as e:
            logger.error(f"Error processing signals: {str(e)}")

    def monitor_positions(self):
        """Monitor and manage open positions."""
        try:
            positions = self.trade_engine.get_open_positions()
            for position in positions:
                symbol = position['symbol']
                current_price = self.data_engine.get_ticker(symbol)['last']
                entry_price = float(position['entryPrice'])

                # Calculate current P&L
                pnl_percent = (current_price - entry_price) / entry_price
                logger.info(f"Position {symbol}: Entry: {entry_price}, Current: {current_price}, PnL: {pnl_percent:.2%}")

        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}")

    def run(self):
        """Main bot loop."""
        if not self.initialize():
            logger.error("Bot initialization failed")
            return

        self.is_running = True
        logger.info("Bot started successfully")

        while self.is_running:
            try:
                # Process trading signals
                self.process_signals()

                # Monitor open positions
                self.monitor_positions()

                # Log account status
                balance = self.trade_engine.get_balance()
                if balance:
                    logger.info(f"Current balance: {balance['free']} USDT")

                # Wait for next iteration
                logger.info(f"Waiting {self.timeframe} for next update...")
                time.sleep(self._get_sleep_time())

            except KeyboardInterrupt:
                logger.info("Stopping bot...")
                self.stop()
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(10)  # Wait before retrying

    def stop(self):
        """Stop the bot."""
        self.is_running = False
        logger.info("Bot stopped")

    def _get_sleep_time(self):
        """Calculate sleep time based on timeframe."""
        timeframe_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        return timeframe_minutes.get(self.timeframe, 15) * 60  # Convert to seconds
