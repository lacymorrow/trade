# Sentiment-Based Trading Bot

This trading bot uses sentiment analysis from Twitter and StockTwits combined with technical analysis to identify potential trading opportunities. It specifically looks for stocks that have experienced significant price drops (5-10%) and analyzes social media sentiment to determine if the drop presents a buying opportunity.

## Features

- Sentiment analysis using Twitter and StockTwits APIs
- Real-time market data monitoring using Alpaca API
- Automated trading with stop-loss and take-profit orders
- Backtesting capabilities
- Configurable trading parameters
- 15-minute trading intervals during market hours

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example` and fill in your API credentials:
   - Alpaca API credentials (get from https://alpaca.markets/)
   - Twitter API credentials (get from https://developer.twitter.com/)
   - StockTwits API token (get from https://api.stocktwits.com/developers)

4. Configure trading parameters in `config.py`:
   - Initial capital
   - Position size limits
   - Stop loss and take profit percentages
   - Sentiment thresholds

## Usage

1. Run backtesting:
   ```bash
   python main.py
   ```
   This will first run a backtest on AAPL for the last 6 months, then start the live trading bot.

2. The bot will automatically:
   - Monitor market movements every 15 minutes
   - Analyze sentiment for stocks that have dropped significantly
   - Place trades when opportunities are identified
   - Manage positions with stop-loss and take-profit orders

## Trading Strategy

The bot implements the following strategy:
1. Identifies stocks that have dropped 5-10% in price
2. Analyzes sentiment from Twitter and StockTwits
3. If sentiment is positive despite the price drop, considers it a potential overreaction
4. Places a buy order with:
   - Stop loss at 5% below entry
   - Take profit at 10% above entry
   - Position size limited to 10% of portfolio

## Disclaimer

This is a experimental trading bot. Use at your own risk. Always monitor your trades and never trade with money you cannot afford to lose. 
