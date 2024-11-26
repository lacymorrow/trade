from market_data import MarketData
from sentiment_analyzer import SentimentAnalyzer
from config import MAX_POSITION_SIZE, STOP_LOSS_PERCENTAGE, TAKE_PROFIT_PERCENTAGE
import logging
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self):
        self.market_data = MarketData()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.api = self.market_data.api

    def calculate_position_size(self, price):
        account = self.market_data.get_account()
        max_position_value = float(account.equity) * MAX_POSITION_SIZE
        return int(max_position_value / price)

    def place_trade(self, symbol, side, qty, price):
        try:
            stop_loss = price * (1 - STOP_LOSS_PERCENTAGE) if side == 'buy' else price * (1 + STOP_LOSS_PERCENTAGE)
            take_profit = price * (1 + TAKE_PROFIT_PERCENTAGE) if side == 'buy' else price * (1 - TAKE_PROFIT_PERCENTAGE)

            # Place the main order
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )

            # Place stop loss
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell' if side == 'buy' else 'buy',
                type='stop',
                time_in_force='gtc',
                stop_price=stop_loss
            )

            # Place take profit
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell' if side == 'buy' else 'buy',
                type='limit',
                time_in_force='gtc',
                limit_price=take_profit
            )

            logger.info(f"Placed {side} order for {qty} shares of {symbol}")
            return order
        except Exception as e:
            logger.error(f"Error placing trade: {str(e)}")
            return None

    def run_strategy(self):
        if not self.market_data.check_market_hours():
            logger.info("Market is closed")
            return

        # Get daily movers
        movers = self.market_data.get_daily_movers()

        for mover in movers:
            symbol = mover['symbol']
            current_price = mover['price']

            # Check if we already have a position
            position = self.market_data.get_position(symbol)
            if position is not None:
                continue

            # Analyze sentiment
            sentiment = self.sentiment_analyzer.get_combined_sentiment(symbol)
            if sentiment is None:
                continue

            # If sentiment is positive and price dropped, consider it a buying opportunity
            if sentiment > 0 and mover['return'] <= -0.05:
                qty = self.calculate_position_size(current_price)
                if qty > 0:
                    self.place_trade(symbol, 'buy', qty, current_price)

    def backtest(self, symbol, start_date, end_date):
        try:
            # Get historical data
            df = yf.download(symbol, start=start_date, end=end_date, interval='1d')

            # Initialize results
            portfolio_value = TRADING_CAPITAL
            position = None
            trades = []

            for date, row in df.iterrows():
                price = row['Close']

                # If we don't have a position, look for entry points
                if position is None:
                    daily_return = (row['Close'] - row['Open']) / row['Open']

                    if daily_return <= PRICE_DROP_THRESHOLD:
                        position = {
                            'entry_price': price,
                            'shares': int(portfolio_value * MAX_POSITION_SIZE / price)
                        }
                        trades.append({
                            'date': date,
                            'action': 'buy',
                            'price': price,
                            'shares': position['shares']
                        })

                # If we have a position, check exit conditions
                elif position is not None:
                    # Check stop loss
                    if price <= position['entry_price'] * (1 - STOP_LOSS_PERCENTAGE):
                        portfolio_value += position['shares'] * price
                        trades.append({
                            'date': date,
                            'action': 'sell',
                            'price': price,
                            'shares': position['shares'],
                            'reason': 'stop_loss'
                        })
                        position = None

                    # Check take profit
                    elif price >= position['entry_price'] * (1 + TAKE_PROFIT_PERCENTAGE):
                        portfolio_value += position['shares'] * price
                        trades.append({
                            'date': date,
                            'action': 'sell',
                            'price': price,
                            'shares': position['shares'],
                            'reason': 'take_profit'
                        })
                        position = None

            return {
                'final_value': portfolio_value,
                'return': (portfolio_value - TRADING_CAPITAL) / TRADING_CAPITAL,
                'trades': trades
            }

        except Exception as e:
            logger.error(f"Error in backtest: {str(e)}")
            return None
