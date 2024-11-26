import logging
from datetime import datetime, timedelta
import time
from .data_engine import DataEngine
from .signal_engine import SignalEngine
from .trade_engine import TradeEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.data_engine = DataEngine()
        self.signal_engine = SignalEngine(self.data_engine)
        self.trade_engine = TradeEngine()

    def run_market_scan(self):
        """Scan market for trading opportunities."""
        try:
            # Get market movers
            movers = self.data_engine.get_market_movers()

            # Analyze each mover
            signals = []
            for category in ['losers', 'gainers']:
                for mover in movers[category]:
                    signal = self.signal_engine.generate_trade_signal(mover['symbol'])
                    if signal:
                        signals.append(signal)

            return sorted(signals, key=lambda x: x['score'], reverse=True)
        except Exception as e:
            logger.error(f"Error in market scan: {str(e)}")
            return []

    def execute_signals(self, signals):
        """Execute trading signals."""
        try:
            executed = 0
            for signal in signals:
                if signal['conviction'] == 'high':
                    if self.trade_engine.execute_trade(signal):
                        executed += 1
                        if executed >= 2:  # Maximum 2 concurrent trades
                            break
            return executed
        except Exception as e:
            logger.error(f"Error executing signals: {str(e)}")
            return 0

    def manage_positions(self):
        """Manage existing positions."""
        try:
            status = self.trade_engine.get_portfolio_status()
            if not status:
                return

            logger.info(f"Current Portfolio Status:")
            logger.info(f"Equity: ${status['equity']:.2f}")
            logger.info(f"Cash: ${status['cash']:.2f}")
            logger.info(f"Buying Power: ${status['buying_power']:.2f}")

            for position in status['positions']:
                logger.info(f"Position: {position['symbol']}")
                logger.info(f"Quantity: {position['qty']}")
                logger.info(f"Market Value: ${position['market_value']:.2f}")
                logger.info(f"Unrealized P/L: ${position['unrealized_pl']:.2f} ({position['unrealized_plpc']:.2%})")

        except Exception as e:
            logger.error(f"Error managing positions: {str(e)}")

    def run_trading_cycle(self):
        """Run one complete trading cycle."""
        try:
            # Check if market is open
            market_hours = self.data_engine.get_market_hours()
            if not market_hours['is_open']:
                next_open = market_hours['next_open']
                logger.info(f"Market is closed. Next opening at {next_open}")
                return

            # Scan market
            logger.info("Scanning market for opportunities...")
            signals = self.run_market_scan()

            if signals:
                logger.info(f"Found {len(signals)} trading signals")
                executed = self.execute_signals(signals)
                logger.info(f"Executed {executed} trades")
            else:
                logger.info("No trading signals found")

            # Manage positions
            self.manage_positions()

        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")

    def run(self):
        """Run the trading bot continuously."""
        logger.info("Starting trading bot...")

        while True:
            try:
                self.run_trading_cycle()
                logger.info("Waiting for next cycle...")
                time.sleep(60 * 15)  # Wait 15 minutes between cycles

            except KeyboardInterrupt:
                logger.info("Shutting down trading bot...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute on error

def backtest(start_date, end_date, initial_capital=10000):
    """Run backtest simulation."""
    try:
        bot = TradingBot()
        # TODO: Implement backtesting logic
        pass
    except Exception as e:
        logger.error(f"Error in backtest: {str(e)}")
        return None
