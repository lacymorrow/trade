# API Documentation

## Command Line Interface

### Running the Bot

1. **Single Analysis Run**
   ```bash
   python run_bot.py --single-run
   ```
   - Performs one analysis cycle
   - Generates signals
   - Simulates trades in test mode
   - Exits after completion

2. **Get Recent Trades**
   ```bash
   python run_bot.py --get-trades
   ```
   - Fetches recent trades for all symbols
   - Returns JSON-formatted trade data
   - Includes error handling and warnings

3. **Continuous Trading**
   ```bash
   python run_bot.py
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

### CryptoBot

#### Methods

1. **start()**
   - Starts the trading bot
   - Initializes components
   - Begins trading loop

2. **stop()**
   - Stops the trading bot
   - Cleans up resources
   - Cancels open orders

3. **get_trading_pairs()**
   - Returns list of tradeable symbols
   - Filters for active pairs
   - Returns: `List[str]`

### CryptoDataEngine

#### Methods

1. **get_price_data()**
   ```python
   def get_price_data(
       self,
       symbol: str,
       timeframe: str = "1Min",
       limit: int = 100
   ) -> Optional[pd.DataFrame]
   ```
   - Fetches historical price data
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
   - Fetches recent trades
   - Returns trade DataFrame
   - Handles rate limiting

### CryptoSignalEngine

#### Methods

1. **generate_signal()**
   ```python
   def generate_signal(
       self,
       symbol: str,
       price_data: pd.DataFrame,
       **kwargs
   ) -> Optional[Dict[str, Any]]
   ```
   - Analyzes price data
   - Generates trading signals
   - Returns signal dictionary

2. **calculate_signal_strength()**
   ```python
   def calculate_signal_strength(
       self,
       indicators: Dict[str, Any],
       **kwargs
   ) -> float
   ```
   - Calculates signal strength
   - Range: -1.0 to +1.0
   - Returns strength value

### CryptoTradeEngine

#### Methods

1. **execute_trade()**
   ```python
   def execute_trade(
       self,
       symbol: str,
       side: str,
       quantity: float,
       price: Optional[float] = None,
       order_type: str = "market",
       **kwargs
   ) -> Optional[Dict[str, Any]]
   ```
   - Executes trading order
   - Handles validation
   - Returns order details

2. **get_position()**
   ```python
   def get_position(
       self,
       symbol: str
   ) -> Optional[Dict[str, Any]]
   ```
   - Gets current position
   - Returns position details
   - Handles missing positions

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

## Rate Limiting

### Alpaca API Limits

1. **REST API**
   - 200 requests per minute
   - Implemented in CryptoDataEngine
   - Automatic rate limiting

2. **Data API**
   - Higher limits for market data
   - Cached responses
   - Batch requests when possible

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
   - Default: 1 minute
   - Configurable per instance
   - Automatic expiration

3. **Cache Methods**
   ```python
   def _cache_data(self, key: str, data: Any) -> None
   def _get_cached_data(self, key: str) -> Optional[Any]
   def clear_cache(self) -> None
   ``` 
