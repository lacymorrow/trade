# Development Guide

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git
- Alpaca trading account (paper or live)

### Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd trade
   ```

2. **Set Up Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # Unix/macOS
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your credentials
   # Required variables:
   # - ALPACA_API_KEY
   # - ALPACA_SECRET_KEY
   # - ALPACA_BASE_URL
   ```

## Configuration

### Environment Variables

1. **Alpaca API Credentials**
   ```env
   # Paper Trading (recommended for development)
   ALPACA_API_KEY=your_paper_key
   ALPACA_SECRET_KEY=your_paper_secret
   ALPACA_BASE_URL=https://paper-api.alpaca.markets

   # Live Trading
   # ALPACA_API_KEY=your_live_key
   # ALPACA_SECRET_KEY=your_live_secret
   # ALPACA_BASE_URL=https://api.alpaca.markets
   ```

2. **Optional Settings**
   ```env
   # Alpha Vantage API (for additional data)
   ALPHA_VANTAGE_API_KEY=your_key

   # Logging
   LOG_LEVEL=INFO
   ```

### Trading Parameters

Modify these in the bot initialization:
```python
bot = CryptoBot(
    api_key=api_key,
    api_secret=api_secret,
    base_url=base_url,
    test_mode=True  # Set to False for live trading
)
```

## Running the Bot

### Test Mode

```bash
# Single analysis run
python run_bot.py --single-run

# Get recent trades
python run_bot.py --get-trades

# Continuous trading
python run_bot.py
```

### Production Mode

1. **Update Environment**
   - Switch to live API credentials
   - Set test_mode to False

2. **Run Bot**
   ```bash
   python run_bot.py
   ```

## Code Structure

### Core Components

```
trading/
├── core/               # Core abstractions
│   ├── base_bot.py    # Base trading bot
│   ├── data_engine.py # Data handling
│   ├── signal_engine.py # Signal generation
│   └── trade_engine.py # Trade execution
│
├── bots/              # Bot implementations
│   └── crypto_bot.py  # Crypto trading bot
```

### Entry Points

- `run_bot.py`: Main bot execution
- `test_bot.py`: Testing utilities

## Development Workflow

1. **Making Changes**
   - Create feature branch
   - Implement changes
   - Add tests
   - Update documentation

2. **Testing**
   ```bash
   # Run unit tests
   python -m pytest tests/

   # Test bot in paper trading mode
   python run_bot.py --single-run
   ```

3. **Code Style**
   - Follow PEP 8
   - Use type hints
   - Document functions and classes

## Adding Features

### New Trading Pairs

1. Update `CryptoBot.update_symbols()`:
   ```python
   def update_symbols(self) -> None:
       try:
           assets = self.api.list_assets(
               status='active',
               asset_class='crypto'
           )
           self.symbols = [
               asset.symbol
               for asset in assets
               if asset.tradable
           ]
       except Exception as e:
           self.logger.error(f"Error updating symbols: {str(e)}")
   ```

### New Indicators

1. Add to `SignalEngine.calculate_technical_indicators()`:
   ```python
   def calculate_technical_indicators(
       self,
       price_data: pd.DataFrame
   ) -> Dict[str, Any]:
       indicators = {}
       # Add new indicator
       indicators['new_indicator'] = calculate_new_indicator(price_data)
       return indicators
   ```

### Custom Strategies

1. Create new signal engine class:
   ```python
   class CustomSignalEngine(SignalEngine):
       def calculate_signal_strength(
           self,
           indicators: Dict[str, Any],
           **kwargs
       ) -> float:
           # Implement custom strategy
           return signal_strength
   ```

## Troubleshooting

### Common Issues

1. **API Connection**
   - Verify credentials
   - Check API endpoint
   - Confirm internet connection

2. **Data Issues**
   - Check symbol validity
   - Verify timeframe
   - Monitor rate limits

3. **Trading Issues**
   - Confirm buying power
   - Check position limits
   - Verify order parameters

### Debugging

1. **Enable Debug Logging**
   ```python
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Test Mode**
   - Use `--single-run` for isolated testing
   - Monitor log output
   - Check trade simulation results

## Best Practices

1. **Code Quality**
   - Write clear documentation
   - Add type hints
   - Include error handling
   - Write unit tests

2. **Trading Safety**
   - Always test in paper trading
   - Implement position limits
   - Add safety checks
   - Monitor performance

3. **Maintenance**
   - Regular dependency updates
   - Code reviews
   - Performance monitoring
   - Documentation updates 
