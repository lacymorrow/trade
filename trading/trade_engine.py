import logging
from datetime import datetime
import alpaca_trade_api as tradeapi
from config import ALPACA_CONFIG, MAX_POSITION_SIZE, STOP_LOSS_PERCENTAGE, TAKE_PROFIT_PERCENTAGE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeEngine:
    def __init__(self):
        self.api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )

    def get_account(self):
        """Get account information."""
        try:
            return self.api.get_account()
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None

    def get_position(self, symbol):
        """Get position for a symbol."""
        try:
            return self.api.get_position(symbol)
        except:
            return None

    def calculate_position_size(self, price, conviction='medium'):
        """Calculate position size based on account equity and conviction."""
        try:
            account = self.get_account()
            if not account:
                return 0

            equity = float(account.equity)
            max_position_value = equity * MAX_POSITION_SIZE

            # Adjust position size based on conviction
            if conviction == 'high':
                position_value = max_position_value
            else:  # medium conviction
                position_value = max_position_value * 0.7

            return int(position_value / price)
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0

    def execute_trade(self, signal):
        """Execute a trade based on the signal."""
        try:
            symbol = signal['symbol']
            action = signal['action']
            conviction = signal['conviction']
            price = signal['price']

            # Check if we already have a position
            position = self.get_position(symbol)
            if position is not None:
                logger.info(f"Already have position in {symbol}, skipping trade")
                return False

            # Calculate position size
            qty = self.calculate_position_size(price, conviction)
            if qty <= 0:
                logger.warning(f"Invalid position size calculated for {symbol}")
                return False

            # Place the main order
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )

            logger.info(f"Placed {action} order for {qty} shares of {symbol}")

            # Place stop loss order
            stop_price = price * (1 - STOP_LOSS_PERCENTAGE)
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='stop',
                time_in_force='gtc',
                stop_price=stop_price
            )

            # Place take profit order
            limit_price = price * (1 + TAKE_PROFIT_PERCENTAGE)
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='limit',
                time_in_force='gtc',
                limit_price=limit_price
            )

            logger.info(f"Placed stop loss at {stop_price:.2f} and take profit at {limit_price:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error executing trade for {signal['symbol']}: {str(e)}")
            return False

    def close_position(self, symbol):
        """Close a position for a given symbol."""
        try:
            position = self.get_position(symbol)
            if position is None:
                return False

            # Cancel any existing orders
            orders = self.api.list_orders(status='open', symbols=[symbol])
            for order in orders:
                self.api.cancel_order(order.id)

            # Close the position
            self.api.close_position(symbol)
            logger.info(f"Closed position in {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {str(e)}")
            return False

    def get_portfolio_status(self):
        """Get current portfolio status."""
        try:
            account = self.get_account()
            positions = self.api.list_positions()

            return {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'qty': int(pos.qty),
                        'market_value': float(pos.market_value),
                        'unrealized_pl': float(pos.unrealized_pl),
                        'unrealized_plpc': float(pos.unrealized_plpc)
                    }
                    for pos in positions
                ]
            }
        except Exception as e:
            logger.error(f"Error getting portfolio status: {str(e)}")
            return None
