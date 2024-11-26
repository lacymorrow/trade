import logging
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from crypto_config import ALPACA_CONFIG, TRADING_PAIRS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_alpaca_connection():
    """Test connection to Alpaca API and verify crypto trading capabilities."""
    try:
        # Initialize API connection
        api = tradeapi.REST(
            ALPACA_CONFIG['API_KEY'],
            ALPACA_CONFIG['SECRET_KEY'],
            ALPACA_CONFIG['BASE_URL']
        )

        # Test account connection
        account = api.get_account()
        logger.info(f"Connected to Alpaca account: {account.id}")
        logger.info(f"Account status: {account.status}")
        logger.info(f"Cash balance: ${float(account.cash):.2f}")
        logger.info(f"Portfolio value: ${float(account.portfolio_value):.2f}")

        # Test crypto data access
        end = datetime.now()
        start = end - timedelta(minutes=5)

        for pair in TRADING_PAIRS:
            symbol = pair.replace('/', '')  # Convert BTC/USD to BTCUSD
            try:
                # Get latest bar data
                bars = api.get_crypto_bars(
                    symbol,
                    start=start.isoformat(),
                    end=end.isoformat(),
                    timeframe='1Min',
                    exchanges=['CBSE']  # Coinbase Exchange
                ).df

                if not bars.empty:
                    last_bar = bars.iloc[-1]
                    logger.info(f"{symbol} - Last price: ${float(last_bar.close):.2f}, "
                              f"Volume: {float(last_bar.volume):.4f}")
                else:
                    logger.warning(f"No recent data available for {symbol}")

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")

        # Test crypto trading permissions
        try:
            # Check if we can trade crypto
            assets = api.list_assets()
            crypto_assets = [a for a in assets if a.exchange == 'CRYPTO' and a.tradable]
            logger.info(f"Available crypto assets: {[a.symbol for a in crypto_assets]}")

            # Get account configurations
            trading_config = api.get_account_configurations()
            logger.info("Account configuration retrieved successfully")
            logger.info(f"Crypto trading enabled: {len(crypto_assets) > 0}")

            # Get current positions
            positions = api.list_positions()
            if positions:
                logger.info("Current positions:")
                for pos in positions:
                    logger.info(f"{pos.symbol}: {pos.qty} @ ${float(pos.avg_entry_price):.2f}")
            else:
                logger.info("No open positions")

            return True

        except Exception as e:
            logger.error(f"Error checking trading permissions: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Error connecting to Alpaca: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing Alpaca API connection...")
    if test_alpaca_connection():
        logger.info("All tests passed successfully!")
    else:
        logger.error("Some tests failed. Please check your API credentials and permissions.")
