import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import ccxt
from .data_engine import CryptoDataEngine
from .signal_engine import CryptoSignalEngine
from crypto_config import (
    TRADING_CAPITAL, MAX_POSITION_SIZE,
    STOP_LOSS_PERCENTAGE, TAKE_PROFIT_PERCENTAGE,
    MIN_ORDER_SIZE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, initial_capital=TRADING_CAPITAL):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.trade_history = pd.DataFrame()
        self.data_engine = CryptoDataEngine()
        self.signal_engine = CryptoSignalEngine(self.data_engine)

    def fetch_historical_data(self, symbol, timeframe, start_date, end_date=None):
        """Fetch historical data for backtesting."""
        try:
            if end_date is None:
                end_date = datetime.now()

            # Calculate number of candles needed
            time_diff = end_date - start_date
            if timeframe == '1m':
                limit = time_diff.total_seconds() / 60
            elif timeframe == '15m':
                limit = time_diff.total_seconds() / (15 * 60)
            elif timeframe == '1h':
                limit = time_diff.total_seconds() / (60 * 60)
            else:
                limit = 1000  # Default limit

            # Fetch OHLCV data
            ohlcv = self.data_engine.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=int(start_date.timestamp() * 1000),
                limit=int(limit)
            )

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return None

    def calculate_position_size(self, symbol, price):
        """Calculate position size based on available capital."""
        max_position_value = self.capital * MAX_POSITION_SIZE
        position_size = max_position_value / price

        # Check minimum order size
        min_size = MIN_ORDER_SIZE.get(symbol, 0)
        if position_size < min_size:
            return None

        # Round to appropriate decimal places
        market = self.data_engine.exchange.market(symbol)
        precision = market['precision']['amount']
        position_size = round(position_size, precision)

        return position_size

    def execute_trade(self, symbol, side, price, size, timestamp):
        """Execute a trade in the backtest."""
        if side == 'buy':
            # Check if we have enough capital
            cost = price * size
            if cost > self.capital:
                return False

            # Open position
            self.positions[symbol] = {
                'size': size,
                'entry_price': price,
                'stop_loss': price * (1 - STOP_LOSS_PERCENTAGE),
                'take_profit': price * (1 + TAKE_PROFIT_PERCENTAGE),
                'timestamp': timestamp
            }
            self.capital -= cost

        elif side == 'sell' and symbol in self.positions:
            # Close position
            position = self.positions[symbol]
            pnl = (price - position['entry_price']) * position['size']
            self.capital += (price * position['size'])

            # Record trade
            self.trades.append({
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'exit_price': price,
                'size': position['size'],
                'pnl': pnl,
                'pnl_percentage': (pnl / (position['entry_price'] * position['size'])) * 100,
                'entry_time': position['timestamp'],
                'exit_time': timestamp,
                'duration': timestamp - position['timestamp']
            })

            del self.positions[symbol]

        return True

    def check_stop_loss_take_profit(self, symbol, current_price, timestamp):
        """Check and execute stop-loss or take-profit orders."""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        # Check stop-loss
        if current_price <= position['stop_loss']:
            self.execute_trade(symbol, 'sell', current_price, position['size'], timestamp)
            logger.info(f"Stop-loss triggered for {symbol} at {current_price}")

        # Check take-profit
        elif current_price >= position['take_profit']:
            self.execute_trade(symbol, 'sell', current_price, position['size'], timestamp)
            logger.info(f"Take-profit triggered for {symbol} at {current_price}")

    def run_backtest(self, symbol, timeframe, start_date, end_date=None):
        """Run backtest for a symbol."""
        try:
            # Fetch historical data
            df = self.fetch_historical_data(symbol, timeframe, start_date, end_date)
            if df is None or df.empty:
                return None

            # Calculate indicators
            df = self.signal_engine.calculate_indicators(df)

            # Initialize results
            results = []
            self.capital = self.initial_capital
            self.positions = {}
            self.trades = []

            # Iterate through each candle
            for timestamp, row in df.iterrows():
                # Check stop-loss and take-profit for open positions
                self.check_stop_loss_take_profit(symbol, row['close'], timestamp)

                # Generate trading signal
                signal = self.signal_engine.generate_signal(symbol, timeframe)
                if not signal:
                    continue

                # Execute trades based on signal
                if signal['action'] == 'BUY' and symbol not in self.positions:
                    size = self.calculate_position_size(symbol, row['close'])
                    if size:
                        self.execute_trade(symbol, 'buy', row['close'], size, timestamp)
                        logger.info(f"Buy signal executed for {symbol} at {row['close']}")

                elif signal['action'] == 'SELL' and symbol in self.positions:
                    self.execute_trade(symbol, 'sell', row['close'], self.positions[symbol]['size'], timestamp)
                    logger.info(f"Sell signal executed for {symbol} at {row['close']}")

                # Record state
                results.append({
                    'timestamp': timestamp,
                    'price': row['close'],
                    'capital': self.capital,
                    'position': self.positions.get(symbol, None),
                    'signal': signal['action']
                })

            # Close any remaining positions at the last price
            if symbol in self.positions:
                last_price = df['close'].iloc[-1]
                self.execute_trade(symbol, 'sell', last_price, self.positions[symbol]['size'], df.index[-1])

            # Calculate performance metrics
            self.trade_history = pd.DataFrame(self.trades)
            metrics = self.calculate_performance_metrics()

            return {
                'results': pd.DataFrame(results),
                'trades': self.trade_history,
                'metrics': metrics
            }

        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            return None

    def calculate_performance_metrics(self):
        """Calculate performance metrics from backtest results."""
        if self.trade_history.empty:
            return None

        total_trades = len(self.trade_history)
        winning_trades = len(self.trade_history[self.trade_history['pnl'] > 0])
        losing_trades = len(self.trade_history[self.trade_history['pnl'] < 0])

        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades) * 100 if total_trades > 0 else 0,
            'total_pnl': self.trade_history['pnl'].sum(),
            'total_pnl_percentage': ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            'average_trade_pnl': self.trade_history['pnl'].mean(),
            'max_drawdown': self.calculate_max_drawdown(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'average_trade_duration': self.trade_history['duration'].mean()
        }

        return metrics

    def calculate_max_drawdown(self):
        """Calculate maximum drawdown from trade history."""
        if self.trade_history.empty:
            return 0

        cumulative_returns = (1 + self.trade_history['pnl_percentage'] / 100).cumprod()
        rolling_max = cumulative_returns.expanding(min_periods=1).max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        return float(drawdowns.min() * 100)

    def calculate_sharpe_ratio(self, risk_free_rate=0.01):
        """Calculate Sharpe ratio from trade history."""
        if self.trade_history.empty:
            return 0

        returns = self.trade_history['pnl_percentage'] / 100
        excess_returns = returns - (risk_free_rate / 252)  # Assuming daily risk-free rate
        if excess_returns.std() == 0:
            return 0
        return float(np.sqrt(252) * excess_returns.mean() / excess_returns.std())
