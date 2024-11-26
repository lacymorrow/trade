import alpaca_trade_api as tradeapi
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from config import ALPACA_CONFIG, PRICE_DROP_THRESHOLD
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketData:
    def __init__(self):
        self.api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )

    def get_price_data(self, symbol, days=5):
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            df = yf.download(symbol, start=start, end=end, interval='15m')
            return df
        except Exception as e:
            logger.error(f"Error fetching price data: {str(e)}")
            return None

    def get_daily_movers(self, min_price=5, max_price=100):
        try:
            assets = self.api.list_assets(status='active')
            movers = []

            for asset in assets:
                if asset.tradable and asset.shortable:
                    symbol = asset.symbol
                    try:
                        data = self.get_price_data(symbol, days=2)
                        if data is None or data.empty:
                            continue

                        current_price = data['Close'][-1]
                        if min_price <= current_price <= max_price:
                            daily_return = (data['Close'][-1] - data['Close'][0]) / data['Close'][0]
                            if daily_return <= PRICE_DROP_THRESHOLD:
                                movers.append({
                                    'symbol': symbol,
                                    'price': current_price,
                                    'return': daily_return
                                })
                    except Exception as e:
                        continue

            return sorted(movers, key=lambda x: x['return'])
        except Exception as e:
            logger.error(f"Error fetching market movers: {str(e)}")
            return []

    def check_market_hours(self):
        clock = self.api.get_clock()
        return clock.is_open

    def get_account(self):
        return self.api.get_account()

    def get_position(self, symbol):
        try:
            return self.api.get_position(symbol)
        except:
            return None
