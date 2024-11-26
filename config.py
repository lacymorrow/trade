import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Trading parameters
TRADING_CAPITAL = 10000  # Initial capital for backtesting
MAX_POSITION_SIZE = 0.1  # Maximum position size as a fraction of portfolio
STOP_LOSS_PERCENTAGE = 0.05  # 5% stop loss
TAKE_PROFIT_PERCENTAGE = 0.1  # 10% take profit

# Sentiment Analysis parameters
SENTIMENT_THRESHOLD = 0.2  # Minimum sentiment score to trigger a trade
MIN_TWEETS = 10  # Minimum number of tweets needed for valid sentiment
PRICE_DROP_THRESHOLD = -0.05  # -5% price drop threshold

# API Credentials
ALPACA_CONFIG = {
    'API_KEY': os.getenv('ALPACA_API_KEY'),
    'SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
    'BASE_URL': os.getenv('ALPACA_BASE_URL')
}

TWITTER_CONFIG = {
    'API_KEY': os.getenv('TWITTER_API_KEY'),
    'API_SECRET': os.getenv('TWITTER_API_SECRET'),
    'ACCESS_TOKEN': os.getenv('TWITTER_ACCESS_TOKEN'),
    'ACCESS_TOKEN_SECRET': os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
}

STOCKTWITS_CONFIG = {
    'ACCESS_TOKEN': os.getenv('STOCKTWITS_ACCESS_TOKEN')
}

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
