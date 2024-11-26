import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from crypto_config import (
    ALPACA_CONFIG, TRADING_PAIRS,
    TIMEFRAMES, DEFAULT_TIMEFRAME
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoDataEngine:
    def __init__(self):
        self.api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )
        self._validate_trading_pairs()

    def _validate_trading_pairs(self):
        """Validate that all configured trading pairs are available."""
        try:
            assets = self.api.list_assets()
            available_pairs = {asset.symbol for asset in assets if asset.status == 'active' and asset.tradable}

            for pair in TRADING_PAIRS:
                symbol = pair.replace('/', '')  # Convert BTC/USD to BTCUSD
                if symbol not in available_pairs:
                    logger.warning(f"Trading pair {pair} not available on Alpaca")

        except Exception as e:
            logger.error(f"Error validating trading pairs: {str(e)}")

    def get_ticker(self, symbol):
        """Get current ticker data for a symbol."""
        try:
            symbol = symbol.replace('/', '')  # Convert BTC/USD to BTCUSD
            quote = self.api.get_latest_crypto_quote(symbol, 'CBSE')

            return {
                'bid': float(quote.bp),
                'ask': float(quote.ap),
                'last': float(quote.ap),  # Using ask price as last price
                'volume': float(quote.bv),  # Using bid volume
                'timestamp': quote.t
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            return None

    def get_ohlcv(self, symbol, timeframe=DEFAULT_TIMEFRAME, limit=100):
        """Get OHLCV data for a symbol."""
        try:
            symbol = symbol.replace('/', '')  # Convert BTC/USD to BTCUSD
            end = datetime.now()
            start = end - timedelta(days=limit if timeframe == '1D' else 10)

            bars = self.api.get_crypto_bars(
                symbol,
                timeframe,
                start=start.isoformat(),
                end=end.isoformat(),
                exchange='CBSE'
            ).df

            if bars.empty:
                return None

            # Convert to standard format
            df = pd.DataFrame({
                'timestamp': bars.index,
                'open': bars['open'],
                'high': bars['high'],
                'low': bars['low'],
                'close': bars['close'],
                'volume': bars['volume']
            })
            df.set_index('timestamp', inplace=True)

            return df.tail(limit)

        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {symbol}: {str(e)}")
            return None

    def get_order_book(self, symbol, limit=20):
        """Get order book data for a symbol."""
        try:
            symbol = symbol.replace('/', '')  # Convert BTC/USD to BTCUSD
            quotes = self.api.get_crypto_quotes(
                symbol,
                'CBSE',
                limit=limit
            ).df

            if quotes.empty:
                return None

            return {
                'bids': [[float(quotes.iloc[-1].bp), float(quotes.iloc[-1].bs)]],
                'asks': [[float(quotes.iloc[-1].ap), float(quotes.iloc[-1].as_)]],
                'timestamp': quotes.index[-1]
            }

        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {str(e)}")
            return None

    def get_recent_trades(self, symbol, limit=50):
        """Get recent trades for a symbol."""
        try:
            symbol = symbol.replace('/', '')  # Convert BTC/USD to BTCUSD
            trades = self.api.get_crypto_trades(
                symbol,
                'CBSE',
                limit=limit
            ).df

            if trades.empty:
                return None

            return pd.DataFrame({
                'timestamp': trades.index,
                'price': trades['p'],
                'size': trades['s'],
                'side': trades['tks']
            })

        except Exception as e:
            logger.error(f"Error fetching recent trades for {symbol}: {str(e)}")
            return None

    def calculate_volatility(self, symbol, window=24):
        """Calculate volatility for a symbol over a given window (in hours)."""
        try:
            df = self.get_ohlcv(symbol, timeframe='1H', limit=window)
            if df is None:
                return None

            returns = np.log(df['close'] / df['close'].shift(1))
            volatility = returns.std() * np.sqrt(24)  # Annualized volatility
            return volatility

        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {str(e)}")
            return None

    def get_market_depth(self, symbol, limit=100):
        """Calculate market depth from order book."""
        try:
            order_book = self.get_order_book(symbol, limit)
            if order_book is None:
                return None

            bids_depth = sum(bid[1] for bid in order_book['bids'])
            asks_depth = sum(ask[1] for ask in order_book['asks'])

            return {
                'bids_depth': bids_depth,
                'asks_depth': asks_depth,
                'ratio': bids_depth / asks_depth if asks_depth > 0 else None
            }

        except Exception as e:
            logger.error(f"Error calculating market depth for {symbol}: {str(e)}")
            return None

    def get_price_change(self, symbol, timeframe=DEFAULT_TIMEFRAME):
        """Calculate price change percentage over the specified timeframe."""
        try:
            df = self.get_ohlcv(symbol, timeframe, limit=2)
            if df is None or len(df) < 2:
                return None

            price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
            return price_change

        except Exception as e:
            logger.error(f"Error calculating price change for {symbol}: {str(e)}")
            return None

    def check_market_hours(self):
        """Check if the crypto market is open (always true for crypto)."""
        return True  # Crypto markets are always open

    def get_account(self):
        """Get account information."""
        try:
            return self.api.get_account()
        except Exception as e:
            logger.error(f"Error fetching account information: {str(e)}")
            return None
