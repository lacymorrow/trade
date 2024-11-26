import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
import alpaca_trade_api as tradeapi
import yfinance as yf
import requests
from config import ALPACA_CONFIG, ALPHA_VANTAGE_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataEngine:
    def __init__(self):
        self.alpaca = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )
        self.alpha_vantage = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

    def get_market_hours(self):
        """Check if market is open and get next open/close times."""
        clock = self.alpaca.get_clock()
        return {
            'is_open': clock.is_open,
            'next_open': clock.next_open,
            'next_close': clock.next_close
        }

    def get_tradable_assets(self, min_price=5, max_price=100, min_volume=1000000):
        """Get list of tradable assets meeting our criteria."""
        assets = []
        try:
            for asset in self.alpaca.list_assets(status='active'):
                if asset.tradable and asset.shortable:
                    # Get current data from yfinance for more detailed filtering
                    ticker = yf.Ticker(asset.symbol)
                    info = ticker.info

                    if not info.get('regularMarketPrice'):
                        continue

                    price = info['regularMarketPrice']
                    volume = info.get('averageVolume', 0)

                    if min_price <= price <= max_price and volume >= min_volume:
                        assets.append({
                            'symbol': asset.symbol,
                            'name': info.get('shortName', ''),
                            'price': price,
                            'volume': volume,
                            'beta': info.get('beta', 0),
                            'sector': info.get('sector', '')
                        })

            return sorted(assets, key=lambda x: x['volume'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting tradable assets: {str(e)}")
            return []

    def get_market_data(self, symbol, timeframe='15Min', limit=100):
        """Get market data for a symbol."""
        try:
            bars = self.alpaca.get_bars(
                symbol,
                timeframe,
                limit=limit,
                adjustment='raw'
            ).df

            return bars
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return None

    def get_news_sentiment(self, symbols):
        """Get news and sentiment for given symbols."""
        try:
            news_data = []
            for symbol in symbols:
                url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
                response = requests.get(url)
                data = response.json()

                if 'feed' in data:
                    for article in data['feed']:
                        if 'ticker_sentiment' in article:
                            for ticker_sent in article['ticker_sentiment']:
                                if ticker_sent['ticker'] == symbol:
                                    news_data.append({
                                        'title': article['title'],
                                        'summary': article.get('summary', ''),
                                        'source': article.get('source', ''),
                                        'url': article.get('url', ''),
                                        'time_published': article.get('time_published', ''),
                                        'overall_sentiment_score': ticker_sent.get('relevance_score', 0) *
                                            float(ticker_sent.get('ticker_sentiment_score', 0))
                                    })
            return news_data
        except Exception as e:
            logger.error(f"Error getting news data: {str(e)}")
            return []

    def get_market_movers(self):
        """Get top market movers (gainers and losers)."""
        try:
            gainers = []
            losers = []

            assets = self.get_tradable_assets()
            for asset in assets:
                symbol = asset['symbol']
                data = self.get_market_data(symbol, timeframe='1D', limit=2)

                if data is None or len(data) < 2:
                    continue

                daily_return = (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0]

                if daily_return >= 0.05:  # 5% or more gain
                    gainers.append({
                        'symbol': symbol,
                        'return': daily_return,
                        'volume': data['volume'].iloc[-1]
                    })
                elif daily_return <= -0.05:  # 5% or more loss
                    losers.append({
                        'symbol': symbol,
                        'return': daily_return,
                        'volume': data['volume'].iloc[-1]
                    })

            return {
                'gainers': sorted(gainers, key=lambda x: x['return'], reverse=True)[:10],
                'losers': sorted(losers, key=lambda x: x['return'])[:10]
            }
        except Exception as e:
            logger.error(f"Error getting market movers: {str(e)}")
            return {'gainers': [], 'losers': []}

    def get_price_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None, interval: str = '15m') -> pd.DataFrame:
        """Get historical price data for a symbol."""
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()

            # Download data
            df = yf.download(symbol, start=start_date, end=end_date, interval=interval)

            if df.empty:
                logger.error(f"No data found for {symbol}")
                return None

            # Ensure all required columns exist
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Missing required columns for {symbol}")
                return None

            return df

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {str(e)}")
            return None
