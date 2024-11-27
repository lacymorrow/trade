# Crypto Trading Bot

A sophisticated cryptocurrency trading bot that uses technical analysis and market indicators to make automated trading decisions. The bot operates 24/7 on the Alpaca trading platform, analyzing multiple crypto pairs and executing trades based on configurable strategies.

## Features

- **24/7 Market Monitoring**: Continuously analyzes cryptocurrency markets
- **Multi-Currency Support**: Trades multiple crypto pairs (BTC, ETH, SOL, AVAX, MATIC)
- **Technical Analysis**: Uses multiple indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Moving Averages (Short and Long term)
  - Volume Analysis
  - Price Volatility

- **Risk Management**:
  - Position size limits
  - Portfolio exposure controls
  - Sanity checks on prices and volumes

- **Flexible Operation Modes**:
  - Test Mode (paper trading)
  - Live Trading Mode
  - Force Trade Mode (for immediate trade decisions)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd trade
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your Alpaca API credentials in `config.py`:
```python
ALPACA_CONFIG = {
    'API_KEY': 'your-api-key',
    'SECRET_KEY': 'your-secret-key',
    'BASE_URL': 'https://api.alpaca.markets'
}
```

## Usage

### Basic Run
```bash
python3 run_crypto_bot.py
```

### Test Mode (No Real Trades)
```bash
python3 run_crypto_bot.py --test
```

### Force Trade Mode
```bash
python3 run_crypto_bot.py --force-trade
```

### Specific Symbols
```bash
python3 run_crypto_bot.py --symbols BTC ETH SOL
```

## Configuration

Key parameters can be configured in `config.py`:

- `TRADING_CAPITAL`: Maximum capital to deploy
- `MAX_POSITION_SIZE`: Maximum size for any single position
- `MAX_PORTFOLIO_EXPOSURE`: Maximum total portfolio exposure
- `VOLUME_MULTIPLIER_THRESHOLD`: Volume surge detection threshold
- `PRICE_WINDOW`: Time window for price analysis
- `SENTIMENT_CORRELATION_THRESHOLD`: Threshold for sentiment correlation

## Trading Strategy

The bot uses a multi-factor analysis approach:

1. **Technical Analysis**:
   - RSI for overbought/oversold conditions
   - MACD for trend direction and momentum
   - Moving averages for trend confirmation
   - Volume analysis for trade conviction

2. **Decision Making**:
   - Calculates a weighted score based on multiple indicators
   - Buy signals when score > 0.2 (configurable)
   - Sell signals when score < -0.2 (configurable)

3. **Position Sizing**:
   - Based on available buying power
   - Respects maximum position and portfolio limits
   - Adjusts for crypto volatility

## Logging

The bot maintains detailed logs in `crypto_bot.log`, including:
- Trade decisions and executions
- Technical analysis results
- Error messages and warnings
- Market data summaries

## Safety Features

1. **Test Mode**: Run without real trades
2. **Sanity Checks**: Validates prices and volumes
3. **Position Limits**: Prevents oversized positions
4. **Error Handling**: Graceful handling of API issues

## Dependencies

- `alpaca-trade-api`: Alpaca Markets API client
- `pandas`: Data analysis and manipulation
- `numpy`: Numerical computations
- `requests`: HTTP requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here]

## Disclaimer

This bot is for educational purposes only. Cryptocurrency trading carries significant risks. Always test thoroughly in paper trading mode first.
