# API Documentation

## Trading Bot API

### Bot Control Endpoints

#### Start Bot
```http
POST /api/bot/control/start
```

**Description**: Start the trading bot with specified configuration.

**Request Body**:
```json
{
  "mode": "live|test",
  "assets": ["BTC", "ETH", "SOL"],
  "force_trade": false
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Bot started successfully",
  "bot_id": "123"
}
```

#### Stop Bot
```http
POST /api/bot/control/stop
```

**Description**: Stop the currently running bot.

**Response**:
```json
{
  "status": "success",
  "message": "Bot stopped successfully"
}
```

#### Bot Status
```http
GET /api/bot/status
```

**Description**: Get current bot status and statistics.

**Response**:
```json
{
  "status": "running|stopped|error",
  "uptime": "2h 15m",
  "trades": 5,
  "profit_loss": "+2.5%"
}
```

### Trading Endpoints

#### Execute Trade
```http
POST /api/bot/trade
```

**Description**: Execute a single trade analysis and potential trade.

**Request Body**:
```json
{
  "symbol": "BTC",
  "force_trade": true
}
```

**Response**:
```json
{
  "status": "success",
  "trade": {
    "symbol": "BTC",
    "action": "buy|sell",
    "quantity": 0.1,
    "price": 35000
  }
}
```

#### Recent Trades
```http
GET /api/bot/trades
```

**Description**: Get list of recent trades.

**Query Parameters**:
- `limit` (optional): Number of trades to return (default: 10)
- `offset` (optional): Offset for pagination (default: 0)

**Response**:
```json
{
  "trades": [
    {
      "id": "123",
      "symbol": "BTC",
      "side": "buy",
      "quantity": 0.1,
      "price": 35000,
      "timestamp": "2024-11-29T22:18:58.535Z",
      "profit_loss": "+2.5%"
    }
  ],
  "total": 50
}
```

### Analysis Endpoints

#### Market Analysis
```http
GET /api/analysis/market
```

**Description**: Get current market analysis.

**Query Parameters**:
- `symbol` (required): Asset symbol to analyze
- `timeframe` (optional): Analysis timeframe (default: "1h")

**Response**:
```json
{
  "symbol": "BTC",
  "price": 35000,
  "indicators": {
    "rsi": 65,
    "macd": {
      "value": 100,
      "signal": 50
    },
    "volume": 1000000
  },
  "sentiment": {
    "score": 0.8,
    "activity": "high"
  }
}
```

#### Portfolio Analysis
```http
GET /api/analysis/portfolio
```

**Description**: Get current portfolio analysis.

**Response**:
```json
{
  "total_value": 100000,
  "cash": 50000,
  "positions": [
    {
      "symbol": "BTC",
      "quantity": 0.1,
      "value": 35000,
      "profit_loss": "+2.5%"
    }
  ],
  "exposure": "50%"
}
```

### Configuration Endpoints

#### Get Configuration
```http
GET /api/config
```

**Description**: Get current bot configuration.

**Response**:
```json
{
  "mode": "live",
  "assets": ["BTC", "ETH", "SOL"],
  "parameters": {
    "max_position_size": 0.1,
    "stop_loss": 0.02,
    "take_profit": 0.05
  }
}
```

#### Update Configuration
```http
PUT /api/config
```

**Description**: Update bot configuration.

**Request Body**:
```json
{
  "mode": "test",
  "assets": ["BTC", "ETH"],
  "parameters": {
    "max_position_size": 0.05
  }
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Configuration updated"
}
```

## Error Handling

All endpoints return standard error responses:

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Error description"
}
```

Common error codes:
- `UNAUTHORIZED`: Authentication required
- `INVALID_REQUEST`: Invalid request parameters
- `BOT_ERROR`: Trading bot error
- `MARKET_ERROR`: Market-related error
- `CONFIG_ERROR`: Configuration error

## Rate Limiting

- API requests are limited to 100 requests per minute per IP
- Trading endpoints are limited to 10 requests per minute per IP
- Status endpoints are limited to 60 requests per minute per IP

## Authentication

All endpoints require authentication using an API key:

```http
Authorization: Bearer YOUR_API_KEY
```

## WebSocket API

### Real-time Updates
```websocket
ws://api/websocket
```

**Subscribe to Updates**:
```json
{
  "action": "subscribe",
  "channels": ["trades", "portfolio", "status"]
}
```

**Message Format**:
```json
{
  "type": "trade|portfolio|status",
  "data": {
    // Channel-specific data
  },
  "timestamp": "2024-11-29T22:18:58.535Z"
}
``` 
