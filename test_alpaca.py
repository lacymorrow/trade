import logging
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
import pandas as pd
from config import ALPACA_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alpaca_connection():
    try:
        # Initialize Trading API
        trading_api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )

        # Initialize Data API
        data_api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['DATA_URL']
        )

        # Test account access
        account = trading_api.get_account()
        logger.info(f"Successfully connected to Alpaca Trading API")
        logger.info(f"Account Status: {account.status}")
        logger.info(f"Equity: ${account.equity}")
        logger.info(f"Cash: ${account.cash}")
        logger.info(f"Buying Power: ${account.buying_power}")

        # Test market data access
        logger.info("\nTesting market data access...")
        try:
            # Try getting latest trade
            aapl_trade = data_api.get_latest_trade("AAPL")
            logger.info(f"Latest AAPL trade price: ${aapl_trade.price}")

            # Try getting bars
            end = pd.Timestamp.now(tz='America/New_York')
            start = end - pd.Timedelta(days=1)

            bars = data_api.get_bars(
                "AAPL",
                TimeFrame.Hour,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                adjustment='raw',
                feed=ALPACA_CONFIG['DATA_FEED']
            )

            if bars is not None and hasattr(bars, 'df'):
                df = bars.df
                logger.info(f"Successfully got {len(df)} bars for AAPL")
                if len(df) > 0:
                    logger.info(f"First bar: {df.iloc[0]}")
                    logger.info(f"Last bar: {df.iloc[-1]}")
            else:
                logger.error("No bars data available")

            # Check market status
            clock = trading_api.get_clock()
            logger.info(f"\nMarket Status:")
            logger.info(f"Is Open: {clock.is_open}")
            logger.info(f"Next Open: {clock.next_open}")
            logger.info(f"Next Close: {clock.next_close}")

        except Exception as e:
            logger.error(f"Market data access failed: {e}")
            logger.info("Note: You may need a separate subscription for market data")

        return True

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_alpaca_connection()
