import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Trading parameters
TRADING_CAPITAL = 10000              # Initial capital
MAX_POSITION_SIZE = 0.25             # Max 25% per position (increased from 20%)
MAX_PORTFOLIO_EXPOSURE = 0.6         # Max 60% total exposure (increased from 50%)

# Sentiment Analysis Parameters
SENTIMENT_CORRELATION_THRESHOLD = 0.3 # Min correlation coefficient (reduced from 0.5)
MIN_SOCIAL_POSTS = 5                 # Minimum posts for valid sentiment (reduced from 10)
SENTIMENT_WINDOW = "30m"             # Sentiment analysis timeframe (reduced from 1h)
SENTIMENT_LOOKBACK_PERIODS = 4       # Number of periods to calculate correlation (reduced from 6)

# Movement Analysis
MIN_PRICE_MOVEMENT = 0.015           # 1.5% minimum price movement (reduced from 2%)
MAX_PRICE_MOVEMENT = 3.00            # 300% maximum price movement
VOLUME_MULTIPLIER_THRESHOLD = 1.1    # Minimum volume increase (reduced from 1.2)
PRICE_WINDOW = "30m"                 # Price analysis timeframe (reduced from 1h)

# Sanity Checks
MAX_VOLATILITY = 0.8                 # Maximum allowed volatility (increased from 0.6)
MIN_MARKET_CAP = 250000000          # $250M minimum market cap (reduced from 500M)
MIN_AVG_VOLUME = 100000             # Minimum average daily volume (reduced from 250000)
EARNINGS_BUFFER_DAYS = 3            # Days to avoid trading before earnings
MAX_SPREAD_PCT = 0.03               # Maximum bid-ask spread as percentage
MIN_SHARES_AVAILABLE = 50000        # Minimum shares available to short

# Technical Indicators
RSI_PERIOD = 14
RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 65
VWAP_WINDOW = "1d"
BB_PERIOD = 20
BB_STD = 2

# API Credentials
ALPACA_CONFIG = {
    'API_KEY': os.getenv('ALPACA_API_KEY'),
    'SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
    'BASE_URL': os.getenv('ALPACA_BASE_URL'),
    'DATA_URL': 'https://data.sandbox.alpaca.markets',
    'CRYPTO_URL': 'https://data.sandbox.alpaca.markets/v2/crypto',
    'DATA_FEED': 'iex'  # Use IEX for free data
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

# Crypto-specific parameters
CRYPTO_CONFIG = {
    'DEFAULT_PAIRS': ['BTCUSD', 'ETHUSD', 'SOLUSD', 'AVAXUSD', 'MATICUSD'],
    'MIN_PRICE_MOVEMENT': 0.05,  # 5% for crypto (more volatile)
    'VOLUME_MULTIPLIER': 3.0,    # Higher volume threshold for crypto
    'MAX_SPREAD_PCT': 0.03,      # Allow higher spreads for crypto
    'MIN_TRADE_SIZE': 10.0,      # Minimum trade size in USD
    'MAX_POSITION_SIZE': 0.2,    # Maximum 20% of buying power per position
    'MAX_TRADE_VALUE': 10000.0,  # Maximum $10,000 per trade

    # Technical Analysis Parameters for Forced Trades
    'RSI_PERIOD': 14,
    'RSI_OVERSOLD': 30,
    'RSI_OVERBOUGHT': 70,
    'SMA_SHORT_PERIOD': 5,
    'SMA_LONG_PERIOD': 20,
    'MACD_FAST': 12,
    'MACD_SLOW': 26,
    'MACD_SIGNAL': 9,

    # Scoring Weights for Forced Trades
    'WEIGHT_TREND': 0.3,      # Weight for trend following signals
    'WEIGHT_MOMENTUM': 0.3,   # Weight for momentum indicators
    'WEIGHT_VOLUME': 0.2,     # Weight for volume analysis
    'WEIGHT_VOLATILITY': 0.2  # Weight for volatility measures
}
