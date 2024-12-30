# Trading Strategy

## Overview

The trading bot implements a technical analysis-based strategy for cryptocurrency trading, focusing on momentum and volume indicators with risk-adjusted position sizing.

## Signal Generation

### Technical Indicators

1. **RSI (Relative Strength Index)**
   - Calculation: 14-period RSI
   - Signal range: 0-100
   - Interpretation:
     - RSI > 70: Overbought
     - RSI < 30: Oversold
   - Weight in final signal: 30%

2. **MACD (Moving Average Convergence Divergence)**
   - Calculation:
     - Fast EMA: 12 periods
     - Slow EMA: 26 periods
     - Signal Line: 9-period EMA of MACD
   - Signal generation:
     - Buy: MACD crosses above signal line
     - Sell: MACD crosses below signal line
   - Weight in final signal: 30%

3. **Volume Analysis**
   - Volume ratio: Current volume / 20-period average
   - Interpretation:
     - High volume confirms trend
     - Low volume suggests weak moves
   - Weight in final signal: 40%

### Signal Strength Calculation

```python
strength = (
    rsi_signal * 0.3 +      # RSI component
    macd_signal * 0.3 +     # MACD component
    volume_signal * 0.4     # Volume component
) * volatility_factor       # Risk adjustment
```

- Signal range: -1.0 to +1.0
- Minimum threshold: ±0.6 for trade execution
- Volatility adjustment reduces signal in high volatility

## Risk Management

### Position Sizing

1. **Account Risk**
   - Maximum risk per trade: 1% of account equity
   - Position size calculation:
     ```python
     risk_amount = account_value * 0.01  # 1% risk
     quantity = risk_amount / price
     ```

2. **Order Validation**
   - Minimum order size checks
   - Available buying power verification
   - Maximum position size limits

### Volatility Adjustment

1. **Volatility Factor**
   ```python
   volatility_factor = 1 - min(volatility * 2, 0.5)
   ```
   - Reduces position size in volatile markets
   - Maximum 50% reduction based on volatility

2. **Market Conditions**
   - Higher thresholds in volatile markets
   - Reduced position sizes in uncertain conditions
   - Automatic trading pause in extreme conditions

## Trade Execution

### Entry Rules

1. **Long (Buy) Signals**
   - Signal strength > 0.6
   - Sufficient buying power
   - Below maximum position size

2. **Short (Sell) Signals**
   - Signal strength < -0.6
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

## Strategy Parameters

### Default Settings

```python
{
    "timeframe": "1Min",        # Trading interval
    "window": 20,              # Analysis window
    "risk_percent": 0.01,      # Risk per trade
    "signal_threshold": 0.6,   # Min signal strength
    "rsi_period": 14,         # RSI calculation period
    "volume_window": 20,      # Volume average window
    "test_mode": True         # Paper trading enabled
}
```

### Customization

The strategy can be customized by adjusting:
- Indicator parameters
- Signal thresholds
- Risk percentages
- Timeframes
- Trading pairs 
