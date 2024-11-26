import alpaca_trade_api as tradeapi
import logging
from datetime import datetime
from crypto_config import (
    ALPACA_CONFIG, MAX_POSITION_SIZE,
    STOP_LOSS_PERCENTAGE, TAKE_PROFIT_PERCENTAGE,
    MIN_ORDER_SIZE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoTradeEngine:
    def __init__(self):
        self.api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )
        self.positions = {}
        self.orders = {}

    def get_balance(self, currency='USD'):
        """Get balance for a specific currency."""
        try:
            account = self.api.get_account()
            return {
                'free': float(account.cash),
                'used': float(account.portfolio_value) - float(account.cash),
                'total': float(account.portfolio_value)
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return None

    def calculate_position_size(self, symbol, price):
        """Calculate position size based on available balance and risk parameters."""
        try:
            balance = self.get_balance()
            if not balance:
                return None

            # Get minimum order size for the symbol
            min_size = MIN_ORDER_SIZE.get(symbol, 0)

            # Calculate maximum position size based on available balance and risk parameters
            max_position_value = balance['free'] * MAX_POSITION_SIZE
            position_size = max_position_value / price

            # Ensure position size meets minimum requirements
            if position_size < min_size:
                logger.warning(f"Calculated position size {position_size} is below minimum {min_size} for {symbol}")
                return None

            # Round position size to appropriate decimal places
            if symbol.startswith('BTC'):
                position_size = round(position_size, 8)
            elif symbol.startswith('ETH'):
                position_size = round(position_size, 6)
            else:
                position_size = round(position_size, 4)

            return position_size

        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {str(e)}")
            return None

    def place_order(self, symbol, side, size=None, price=None, order_type='market'):
        """Place an order on the exchange."""
        try:
            # Validate order parameters
            if not symbol or not side:
                logger.error("Missing required order parameters")
                return None

            # Convert symbol format
            symbol = symbol.replace('/', '')  # Convert BTC/USD to BTCUSD

            # Get current market price if not provided
            if not price:
                quote = self.api.get_latest_crypto_quote(symbol, 'CBSE')
                price = float(quote.ap) if side == 'buy' else float(quote.bp)

            # Calculate position size if not provided
            if not size:
                size = self.calculate_position_size(symbol, price)
                if not size:
                    return None

            # Place the order
            order = self.api.submit_order(
                symbol=symbol,
                qty=size,
                side=side,
                type=order_type,
                time_in_force='gtc',
                limit_price=price if order_type == 'limit' else None
            )

            # Store order details
            self.orders[order.id] = {
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'type': order_type,
                'status': order.status,
                'timestamp': datetime.now()
            }

            logger.info(f"Placed {side} order for {size} {symbol} at {price}")
            return order

        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {str(e)}")
            return None

    def place_stop_loss(self, symbol, position_size, entry_price, side='buy'):
        """Place a stop loss order."""
        try:
            stop_price = entry_price * (1 - STOP_LOSS_PERCENTAGE if side == 'buy' else 1 + STOP_LOSS_PERCENTAGE)

            symbol = symbol.replace('/', '')  # Convert BTC/USD to BTCUSD
            order = self.api.submit_order(
                symbol=symbol,
                qty=position_size,
                side='sell' if side == 'buy' else 'buy',
                type='stop',
                time_in_force='gtc',
                stop_price=stop_price
            )

            logger.info(f"Placed stop loss order for {symbol} at {stop_price}")
            return order

        except Exception as e:
            logger.error(f"Error placing stop loss for {symbol}: {str(e)}")
            return None

    def place_take_profit(self, symbol, position_size, entry_price, side='buy'):
        """Place a take profit order."""
        try:
            take_profit_price = entry_price * (1 + TAKE_PROFIT_PERCENTAGE if side == 'buy' else 1 - TAKE_PROFIT_PERCENTAGE)

            symbol = symbol.replace('/', '')  # Convert BTC/USD to BTCUSD
            order = self.api.submit_order(
                symbol=symbol,
                qty=position_size,
                side='sell' if side == 'buy' else 'buy',
                type='limit',
                time_in_force='gtc',
                limit_price=take_profit_price
            )

            logger.info(f"Placed take profit order for {symbol} at {take_profit_price}")
            return order

        except Exception as e:
            logger.error(f"Error placing take profit for {symbol}: {str(e)}")
            return None

    def execute_signal(self, signal):
        """Execute a trading signal."""
        try:
            symbol = signal['symbol']
            action = signal['action']
            price = signal['price']

            if action == 'HOLD':
                return None

            # Check if we already have a position
            position = self.positions.get(symbol)

            if action == 'BUY' and not position:
                # Open long position
                size = self.calculate_position_size(symbol, price)
                if not size:
                    return None

                # Place market buy order
                order = self.place_order(symbol, 'buy', size)
                if not order:
                    return None

                # Place stop loss and take profit orders
                self.place_stop_loss(symbol, size, price, 'buy')
                self.place_take_profit(symbol, size, price, 'buy')

                # Update positions
                self.positions[symbol] = {
                    'side': 'buy',
                    'size': size,
                    'entry_price': price,
                    'timestamp': datetime.now()
                }

                return order

            elif action == 'SELL' and position:
                # Close position
                order = self.place_order(symbol, 'sell', position['size'])
                if order:
                    del self.positions[symbol]
                return order

        except Exception as e:
            logger.error(f"Error executing signal for {signal['symbol']}: {str(e)}")
            return None

    def get_open_positions(self):
        """Get all open positions."""
        try:
            positions = self.api.list_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'size': float(pos.qty),
                    'entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc)
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error fetching open positions: {str(e)}")
            return []

    def get_order_status(self, order_id):
        """Get the status of a specific order."""
        try:
            return self.api.get_order(order_id)
        except Exception as e:
            logger.error(f"Error fetching order status for {order_id}: {str(e)}")
            return None
