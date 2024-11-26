import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Trading parameters
TRADING_CAPITAL = 1000  # Initial capital in USD
MAX_POSITION_SIZE = 0.1  # Maximum position size as a fraction of portfolio
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 0.04  # 4% take profit

# Technical Analysis Parameters
FAST_EMA = 12
SLOW_EMA = 26
SIGNAL_EMA = 9
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Trading Pairs Configuration
TRADING_PAIRS = [
    'BTC/USD',
    'ETH/USD',
    'SOL/USD',
    'AVAX/USD',
    'LINK/USD',
    'DOT/USD',
    'UNI/USD',
    'AAVE/USD'
]

# Timeframes
TIMEFRAMES = {
    '1Min': '1m',
    '5Min': '5m',
    '15Min': '15m',
    '1H': '1h',
    '4H': '4h',
    '1D': '1d'
}

DEFAULT_TIMEFRAME = '15Min'

# Alpaca Configuration
ALPACA_CONFIG = {
    'API_KEY': os.getenv('ALPACA_API_KEY'),
    'SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
    'BASE_URL': os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
    'CRYPTO_URL': 'https://data.alpaca.markets/v1beta2/crypto'
}

# Risk Management
MIN_ORDER_SIZE = {
    'BTC/USD': 0.0001,
    'ETH/USD': 0.001,
    'SOL/USD': 0.1,
    'AVAX/USD': 0.1,
    'LINK/USD': 1.0,
    'DOT/USD': 1.0,
    'UNI/USD': 1.0,
    'AAVE/USD': 0.01
}

# Strategy Parameters
STRATEGY_PARAMS = {
    'volume_threshold': 1.5,  # Minimum volume increase factor
    'price_change_threshold': 0.02,  # 2% price change threshold
    'trend_ema_period': 200,  # Long-term trend EMA
    'volatility_window': 24,  # Hours for volatility calculation
    'min_volatility': 0.01,  # Minimum volatility threshold
    'max_volatility': 0.1    # Maximum volatility threshold
}

# Sentiment Analysis
SENTIMENT_PARAMS = {
    'min_posts': 20,  # Minimum number of social media posts
    'sentiment_threshold': 0.2,  # Minimum sentiment score
    'time_window': 24  # Hours to look back for sentiment
}

# Websocket Configuration
WEBSOCKET_TIMEOUT = 60  # seconds
RECONNECT_DELAY = 5  # seconds between reconnection attempts
MAX_RECONNECTS = 5  # maximum number of reconnection attempts
