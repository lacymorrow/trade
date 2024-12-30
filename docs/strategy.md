# Trading Strategies

## Overview

The trading system implements technical analysis-based strategies for both cryptocurrency and stock trading, focusing on momentum and volume indicators with risk-adjusted position sizing.

## Common Components

### Technical Indicators

1. **RSI (Relative Strength Index)**
   - Calculation: 14-period RSI
   - Signal range: 0-100
   - Interpretation:
     - RSI > 70: Overbought
     - RSI < 30: Oversold
   - Weight in final signal: 30-40%

2. **MACD (Moving Average Convergence Divergence)**
   - Calculation:
     - Fast EMA: 12 periods
     - Slow EMA: 26 periods
     - Signal Line: 9-period EMA of MACD
   - Signal generation:
     - Buy: MACD crosses above signal line
     - Sell: MACD crosses below signal line
   - Weight in final signal: 30-40%

3. **Volume Analysis**
   - Volume ratio: Current volume / 20-period average
   - Interpretation:
     - High volume confirms trend
     - Low volume suggests weak moves
   - Weight in final signal: 20-40%

## Cryptocurrency Trading (CryptoBot)

### Signal Generation

```python
strength = (
    rsi_signal * 0.3 +      # RSI component
    macd_signal * 0.3 +     # MACD component
    volume_signal * 0.4     # Volume component
) * volatility_factor       # Risk adjustment
```

- Signal range: -1.0 to +1.0
- Minimum threshold: ±0.6 for trade execution
- Higher volatility adjustment for crypto markets

### Risk Management

1. **Position Sizing**
   - Maximum risk per trade: 1% of account equity
   - Position size calculation:
     ```python
     risk_amount = account_value * 0.01  # 1% risk
     quantity = risk_amount / price
     ```

2. **Volatility Adjustment**
   - Reduces position size in volatile markets
   - Maximum 50% reduction based on volatility
   - More aggressive adjustment for crypto

### Market Specific Features

1. **24/7 Trading**
   - Continuous market monitoring
   - No market hours restrictions
   - Real-time price updates

2. **Asset Selection**
   - Focuses on major cryptocurrencies
   - Requires sufficient liquidity
   - Must be supported by Alpaca

## Stock Trading (StockBot)

### Signal Generation

```python
strength = (
    rsi_signal * 0.4 +      # RSI component
    macd_signal * 0.4 +     # MACD component
    volume_signal * 0.2     # Volume component
)
```

- Signal range: -1.0 to +1.0
- Minimum threshold: ±0.5 for trade execution
- No volatility adjustment (more stable market)

### Risk Management

1. **Position Sizing**
   - Maximum risk per trade: 1% of account equity
   - Position size calculation:
     ```python
     risk_amount = account_value * 0.01  # 1% risk
     quantity = risk_amount / price
     ```

2. **Market Hours**
   - Only trades during market hours
   - Checks market status before trading
   - Respects trading halts

### Market Specific Features

1. **Asset Selection**
   ```python
   assets = api.list_assets(
       status='active',
       asset_class='us_equity'
   )
   symbols = [
       asset.symbol
       for asset in assets
       if asset.tradable and asset.fractionable
   ]
   ```
   - US equities only
   - Must be actively trading
   - Must support fractional shares

2. **Trading Restrictions**
   - Pattern day trading rules
   - Market hours only
   - Trading halts

## Trade Execution

### Entry Rules

1. **Long (Buy) Signals**
   - Signal strength above threshold
   - Sufficient buying power
   - Below maximum position size
   - Market conditions suitable

2. **Short (Sell) Signals**
   - Signal strength below threshold
   - Existing position to close
   - Market conditions suitable

### Order Types

1. **Market Orders**
   - Default order type
   - Used for immediate execution
   - Slippage consideration in sizing

2. **Test Mode**
   - Simulated trade execution
   - Full logging of would-be trades
   - Performance tracking

## Performance Monitoring

### Trade Logging

1. **Trade Details**
   - Entry/exit prices
   - Position sizes
   - Signal strengths
   - Execution timestamps

2. **Performance Metrics**
   - Win/loss ratio
   - Average profit/loss
   - Maximum drawdown
   - Sharpe ratio

### Risk Metrics

1. **Position Monitoring**
   - Current positions
   - Unrealized P&L
   - Position duration
   - Cost basis

2. **Account Metrics**
   - Equity curve
   - Available buying power
   - Open orders
   - Trading history

## Configuration

### Default Settings

```python
{
    "timeframe": "1Min",        # Trading interval
    "window": 20,              # Analysis window
    "risk_percent": 0.01,      # Risk per trade
    "signal_threshold": {
        "crypto": 0.6,         # Crypto threshold
        "stock": 0.5           # Stock threshold
    },
    "rsi_period": 14,         # RSI calculation period
    "volume_window": 20,      # Volume average window
    "test_mode": True         # Paper trading enabled
}
```

### Customization

The strategies can be customized by adjusting:
- Indicator parameters
- Signal thresholds
- Risk percentages
- Timeframes
- Trading pairs/symbols 
