# API Documentation

## Command Line Interface

### Running the Bot

1. **Single Analysis Run**
   ```bash
   # Crypto bot
   python run_bot.py --bot-type crypto --single-run

   # Stock bot
   python run_bot.py --bot-type stock --single-run
   ```
   - Performs one analysis cycle
   - Generates signals
   - Simulates trades in test mode
   - Exits after completion

2. **Get Recent Trades**
   ```bash
   # Crypto bot
   python run_bot.py --bot-type crypto --get-trades

   # Stock bot
   python run_bot.py --bot-type stock --get-trades
   ```
   - Fetches recent trades for all symbols
   - Returns JSON-formatted trade data
   - Includes error handling and warnings

3. **Continuous Trading**
   ```bash
   # Crypto bot
   python run_bot.py --bot-type crypto

   # Stock bot
   python run_bot.py --bot-type stock
   ```
   - Runs continuous trading loop
   - Monitors market data
   - Executes trades based on signals

## Data Structures

### Trade Object
```json
{
    "id": "2024-01-01T00:00:00Z-BTC/USD",
    "timestamp": "2024-01-01T00:00:00Z",
    "symbol": "BTC/USD",
    "side": "buy",
    "price": 42000.00,
    "quantity": 0.1
}
```

### Signal Object
```json
{
    "symbol": "BTC/USD",
    "action": "buy",
    "strength": 0.75,
    "price": 42000.00,
    "timestamp": "2024-01-01T00:00:00Z",
    "indicators": {
        "rsi": 65.5,
        "macd": 100.5,
        "macd_signal": 90.2,
        "volume_ratio": 1.5,
        "volatility": 0.02
    }
}
```

### Position Object
```json
{
    "symbol": "BTC/USD",
    "quantity": 0.1,
    "entry_price": 42000.00,
    "current_price": 42500.00,
    "profit_loss": 50.00,
    "profit_loss_percent": 1.19
}
```

## Core Classes

### Base Classes

1. **BaseBot**
   - Abstract base class for all bots
   - Manages bot lifecycle
   - Implements trading loop
   - Handles error recovery

2. **DataEngine**
   - Abstract base class for market data
   - Defines data retrieval interface
   - Implements caching
   - Rate limit handling

3. **SignalEngine**
   - Abstract base class for signals
   - Technical analysis framework
   - Signal generation interface
   - Indicator calculations

4. **TradeEngine**
   - Abstract base class for trading
   - Order execution interface
   - Position management
   - Risk controls

### Crypto Implementation

#### CryptoBot

1. **start()**
   - Starts the trading bot
   - Initializes components
   - Begins trading loop

2. **stop()**
   - Stops the trading bot
   - Cleans up resources
   - Cancels open orders

3. **get_trading_pairs()**
   - Returns list of crypto pairs
   - Filters for active pairs
   - Returns: `List[str]`

#### CryptoDataEngine

1. **get_price_data()**
   ```python
   def get_price_data(
       self,
       symbol: str,
       timeframe: str = "1Min",
       limit: int = 100
   ) -> Optional[pd.DataFrame]
   ```
   - Fetches crypto price data
   - Returns OHLCV DataFrame
   - Implements caching

2. **get_recent_trades()**
   ```python
   def get_recent_trades(
       self,
       symbol: str,
       limit: int = 50
   ) -> Optional[pd.DataFrame]
   ```
   - Fetches recent crypto trades
   - Returns trade DataFrame
   - Handles rate limiting

### Stock Implementation

#### StockBot

1. **start()**
   - Starts the trading bot
   - Checks market hours
   - Begins trading loop

2. **stop()**
   - Stops the trading bot
   - Closes positions
   - Cancels open orders

3. **get_trading_pairs()**
   - Returns list of stock symbols
   - Filters for active, tradeable stocks
   - Returns: `List[str]`

#### StockDataEngine

1. **get_price_data()**
   ```python
   def get_price_data(
       self,
       symbol: str,
       timeframe: str = "1Min",
       limit: int = 100
   ) -> Optional[pd.DataFrame]
   ```
   - Fetches stock price data
   - Returns OHLCV DataFrame
   - Implements caching

2. **get_recent_trades()**
   ```python
   def get_recent_trades(
       self,
       symbol: str,
       limit: int = 50
   ) -> Optional[pd.DataFrame]
   ```
   - Fetches recent stock trades
   - Returns trade DataFrame
   - Handles rate limiting

## Error Handling

### Error Response Format
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Error description",
        "details": "Additional error details"
    }
}
```

### Common Error Codes

1. **MISSING_CREDENTIALS**
   - Missing API credentials
   - Check environment variables

2. **FETCH_ERROR**
   - Error fetching data
   - Check API connection

3. **SERIALIZATION_ERROR**
   - Error processing data
   - Check data format

4. **MARKET_CLOSED**
   - Stock market is closed
   - Only for stock trading

## Rate Limiting

### Alpaca API Limits

1. **Crypto API**
   - 200 requests per minute
   - Higher data frequency
   - 24/7 trading

2. **Stock API**
   - 200 requests per minute
   - Market hours only
   - Trading halts respected

### Rate Limit Handling

```python
def _rate_limit_wait(self):
    """Handle rate limiting."""
    self._request_count += 1
    now = datetime.now()

    if (now - self._last_request_time).seconds >= 60:
        self._request_count = 1
        self._last_request_time = now
        return

    if self._request_count >= self._rate_limit:
        sleep_time = 60 - (now - self._last_request_time).seconds
        if sleep_time > 0:
            time.sleep(sleep_time)
        self._request_count = 1
        self._last_request_time = datetime.now()
```

## Data Caching

### Cache Implementation

1. **Cache Keys**
   ```python
   cache_key = self._build_cache_key(
       symbol,
       timeframe=timeframe,
       limit=limit
   )
   ```

2. **Cache TTL**
   - Crypto: 10 seconds
   - Stocks: 1 minute
   - Configurable per instance

3. **Cache Methods**
   ```python
   def _cache_data(self, key: str, data: Any) -> None
   def _get_cached_data(self, key: str) -> Optional[Any]
   def clear_cache(self) -> None
   ``` 
