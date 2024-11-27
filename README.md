# Trading Bot Documentation

## Overview
This trading bot monitors StockTwits for trending stocks and analyzes them for potential trading opportunities based on price movements, social sentiment, and technical indicators. It uses the Alpaca API for market data and trade execution.

## Architecture

### Core Components

#### 1. Trading Bot (`trading/bot.py`)
The main bot class that orchestrates all trading activities:
```python
# Example initialization
from trading.bot import TradingBot

# Initialize in test mode
bot = TradingBot(test_mode=True)

# Start the bot
bot.start()
```

#### 2. Sentiment Analyzer (`sentiment_analyzer.py`)
Handles all social media sentiment analysis:
```python
# Example sentiment analysis
from sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()

# Get trending stocks
trending = analyzer.get_trending_stocks()
print(f"Found trending stocks: {trending}")

# Analyze sentiment for a symbol
metrics = analyzer.get_symbol_sentiment_metrics("AAPL")
print(f"Sentiment score: {metrics['sentiment']:.2f}")
```

#### 3. Sanity Checker (`trading/sanity_checks.py`)
Implements safety checks before trading:
```python
# Example safety checks
from trading.sanity_checks import SanityChecker

checker = SanityChecker(trading_api)

# Run all checks for a symbol
passed, results = checker.run_all_checks("AAPL", price_data)
print(f"Checks passed: {passed}")
print(f"Individual results: {results}")
```

## Configuration (`config.py`)

### Example Configuration
```python
# Trading Parameters
TRADING_CAPITAL = 10000              # $10,000 initial capital
MAX_POSITION_SIZE = 0.1              # Max $1,000 per position
MAX_PORTFOLIO_EXPOSURE = 0.3         # Max $3,000 total exposure

# Example: Position Sizing
position_size = TRADING_CAPITAL * MAX_POSITION_SIZE  # $1,000 max position
```

### Movement Analysis
```python
# Example price movement calculation
price_change = (current_price - previous_price) / previous_price
is_significant = abs(price_change) >= MIN_PRICE_MOVEMENT  # 3% threshold
```

### Sentiment Analysis
```python
# Example sentiment correlation
correlation = calculate_sentiment_correlation(sentiment_data, price_data)
is_valid = correlation >= SENTIMENT_CORRELATION_THRESHOLD  # 0.7 threshold
```

## Trading Strategy

### Example Trade Analysis
```python
# 1. Price Movement Check
if price_change >= 0.03:  # 3% move
    print("Significant price movement detected")

# 2. Sentiment Analysis
if sentiment_score >= 0.7:  # Strong positive sentiment
    print("High sentiment detected")

# 3. Safety Checks
if market_cap >= 1_000_000_000:  # $1B minimum
    print("Market cap check passed")
```

### Example Trade Execution
```python
# Calculate position size
price = 100.00
shares = min(
    MAX_POSITION_SIZE * TRADING_CAPITAL / price,
    MAX_PORTFOLIO_EXPOSURE * TRADING_CAPITAL / price
)

# Place order
order = {
    'symbol': 'AAPL',
    'qty': shares,
    'side': 'buy',
    'type': 'market',
    'time_in_force': 'day'
}
```

## Setup Instructions

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
venv\\Scripts\\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. API Configuration
```env
# .env file example
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# For crypto trading
ALPACA_CRYPTO_URL=https://paper-api.alpaca.markets
```

### 3. Running the Bot
```bash
# Test mode (recommended for starting)
python run_bot.py --test

# Live mode (real trading)
python run_bot.py

# Crypto mode (coming soon)
python run_crypto_bot.py
```

## Example Use Cases

### 1. Momentum Trading
The bot can identify and trade momentum moves:
```python
# Example momentum scenario
price_data = {
    't-3': 100.00,
    't-2': 103.00,  # +3%
    't-1': 106.09,  # +3%
    't-0': 109.27   # +3%
}
sentiment_data = {
    'bullish_count': 75,
    'bearish_count': 25,
    'sentiment_score': 0.75  # Strong positive
}
```

### 2. Overreaction Trading
The bot can identify market overreactions:
```python
# Example overreaction scenario
news_event = "Minor product delay"
price_change = -15.00  # -15% move
sentiment_score = -0.30  # Mild negative
correlation = 0.85  # High correlation

# Bot identifies overreaction due to:
# 1. Large price move vs mild sentiment
# 2. High sentiment-price correlation
# 3. Non-material news event
```

### 3. Volume Spike Trading
The bot monitors for unusual volume:
```python
# Example volume analysis
avg_volume = 1_000_000
current_volume = 2_500_000
volume_multiplier = current_volume / avg_volume  # 2.5x

if volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD:
    print("Volume spike detected")
```

## Safety Features

### Example Risk Management
```python
# Position sizing example
def calculate_position_size(price, volatility):
    base_size = TRADING_CAPITAL * MAX_POSITION_SIZE
    # Reduce size for volatile stocks
    adjusted_size = base_size * (1 - volatility)
    return min(adjusted_size, MAX_PORTFOLIO_EXPOSURE * TRADING_CAPITAL)
```

### Example Market Conditions Check
```python
def check_market_conditions():
    # Check market hours
    if not market.is_open:
        return False
        
    # Check volatility
    if vix > 30:
        return False
        
    # Check liquidity
    if spread > MAX_SPREAD_PCT:
        return False
        
    return True
```

## Logging and Monitoring

### Example Log Output
```
2024-03-14 09:30:01 INFO: Bot started in test mode
2024-03-14 09:30:02 INFO: Found 15 trending stocks
2024-03-14 09:30:03 INFO: Analyzing AAPL
2024-03-14 09:30:03 INFO: Price: $175.50 (+3.5%)
2024-03-14 09:30:03 INFO: Sentiment score: 0.85
2024-03-14 09:30:03 INFO: Volume multiplier: 2.3x
2024-03-14 09:30:04 INFO: Trade signal generated: BUY
```

### Example Monitoring Metrics
```python
# Performance metrics
metrics = {
    'win_rate': wins / total_trades,
    'avg_return': total_return / total_trades,
    'max_drawdown': max_drawdown,
    'sharpe_ratio': returns_mean / returns_std,
    'sentiment_accuracy': correct_signals / total_signals
}
```

## Testing

### Example Test Cases
```python
def test_price_movement():
    price_data = pd.DataFrame({
        'close': [100, 103, 106, 109]
    })
    movement = calculate_price_movement(price_data)
    assert movement == 0.09  # 9% move

def test_sentiment_analysis():
    posts = [
        {'text': 'Great stock!', 'sentiment': 1},
        {'text': 'Selling everything', 'sentiment': -1},
        {'text': 'Holding long term', 'sentiment': 0.5}
    ]
    score = calculate_sentiment_score(posts)
    assert score == 0.167  # Slightly positive
```

## Troubleshooting

### Common Issues and Solutions

1. API Connection Errors
```python
# Check API connection
try:
    account = trading_api.get_account()
    print(f"Connected successfully: {account.status}")
except Exception as e:
    print(f"Connection failed: {e}")
    # Check credentials in .env
    # Verify internet connection
    # Confirm API service status
```

2. Data Issues
```python
# Verify price data
def validate_price_data(data):
    if data is None or len(data) == 0:
        raise ValueError("No price data available")
    if data['close'].isnull().any():
        raise ValueError("Missing price values")
    return True
```

3. Trading Issues
```python
# Pre-trade checks
def validate_trade(symbol, side, quantity):
    # Check buying power
    if side == 'buy':
        if quantity * price > buying_power:
            return False
            
    # Check position limits
    current_exposure = calculate_exposure()
    if current_exposure + (quantity * price) > MAX_PORTFOLIO_EXPOSURE:
        return False
        
    return True
```

## Disclaimer
This trading bot is for educational and research purposes. Always:
- Test thoroughly before live trading
- Start with small positions
- Monitor bot behavior
- Understand the risks
- Use proper risk management

## Coming Soon: Crypto Trading
The bot will soon support cryptocurrency trading with:
- 24/7 market monitoring
- Crypto-specific indicators
- Exchange-specific features
- Additional safety checks
- Volatility adjustments
