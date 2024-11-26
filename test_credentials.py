import twitter
import requests
from config import TWITTER_CONFIG, STOCKTWITS_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_twitter():
    try:
        api = twitter.Api(
            consumer_key=TWITTER_CONFIG['API_KEY'],
            consumer_secret=TWITTER_CONFIG['API_SECRET'],
            access_token_key=TWITTER_CONFIG['ACCESS_TOKEN'],
            access_token_secret=TWITTER_CONFIG['ACCESS_TOKEN_SECRET']
        )

        # Test the connection by verifying credentials
        account = api.VerifyCredentials()
        if account:
            logger.info(f"Twitter connection successful! Connected as: {account.screen_name}")
            return True
        return False
    except Exception as e:
        logger.error(f"Twitter connection failed: {str(e)}")
        return False

def test_stocktwits():
    try:
        # Test StockTwits connection by getting AAPL stream without auth
        url = "https://api.stocktwits.com/api/2/streams/symbol/AAPL.json"
        response = requests.get(url)  # StockTwits basic API doesn't require auth
        if response.status_code == 200:
            logger.info("StockTwits connection successful!")
            return True
        else:
            logger.error(f"StockTwits connection failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"StockTwits connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing API connections...")
    twitter_ok = test_twitter()
    stocktwits_ok = test_stocktwits()

    if twitter_ok and stocktwits_ok:
        logger.info("All API connections successful!")
    else:
        logger.error("Some API connections failed. Please check the logs above.")
