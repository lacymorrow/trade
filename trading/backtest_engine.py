import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, config: Dict, data_engine, signal_engine, trade_engine):
        self.config = config
        self.data_engine = data_engine
        self.signal_engine = signal_engine
        self.trade_engine = trade_engine
        self.initial_capital = config.get('initial_capital', 100000)

    def run_backtest(self, symbol: str, start_date: datetime, end_date: datetime) -> Dict:
        """Run backtest simulation."""
        try:
            # Get historical data
            price_data = self.data_engine.get_price_data(symbol, start_date, end_date)
            if price_data is None or price_data.empty:
                logger.error(f"No price data available for {symbol}")
                return {}

            # Initialize portfolio and results tracking
            portfolio = {
                'cash': self.initial_capital,
                'position': 0,
                'portfolio_value': self.initial_capital
            }

            portfolio_history = pd.DataFrame(index=price_data.index)
            portfolio_history['portfolio_value'] = self.initial_capital
            trades = pd.DataFrame(columns=['timestamp', 'side', 'price', 'quantity', 'value'])

            # Get social data if available
            try:
                social_data = self.data_engine.get_social_data(symbol, start_date, end_date)
            except:
                social_data = pd.DataFrame()

            # Generate initial signals
            signals = self.signal_engine.generate_signals(price_data.copy(), social_data)
            if signals.empty:
                logger.error("No signals generated")
                return {}

            # Ensure signals have the same index as price_data
            signals = signals.reindex(price_data.index, method='ffill')

            # Simulate trading
            for i, timestamp in enumerate(price_data.index):
                try:
                    current_price = float(price_data.iloc[i]['Close'])
                    signal_strength = float(signals.iloc[i]['signal_strength'])

                    # Execute trades based on signals
                    if signal_strength > 0.5 and portfolio['position'] <= 0:
                        # Buy signal
                        quantity = int((portfolio['cash'] * 0.95) / current_price)  # Use 95% of cash
                        if quantity > 0:
                            cost = quantity * current_price
                            portfolio['cash'] -= cost
                            portfolio['position'] += quantity
                            trades = pd.concat([trades, pd.DataFrame({
                                'timestamp': [timestamp],
                                'side': ['buy'],
                                'price': [current_price],
                                'quantity': [quantity],
                                'value': [cost]
                            })], ignore_index=True)

                    elif signal_strength < -0.5 and portfolio['position'] > 0:
                        # Sell signal
                        quantity = portfolio['position']
                        value = quantity * current_price
                        portfolio['cash'] += value
                        portfolio['position'] = 0
                        trades = pd.concat([trades, pd.DataFrame({
                            'timestamp': [timestamp],
                            'side': ['sell'],
                            'price': [current_price],
                            'quantity': [quantity],
                            'value': [value]
                        })], ignore_index=True)

                    # Update portfolio value
                    portfolio['portfolio_value'] = portfolio['cash'] + (portfolio['position'] * current_price)
                    portfolio_history.loc[timestamp, 'portfolio_value'] = portfolio['portfolio_value']

                except Exception as e:
                    logger.error(f"Error processing bar at {timestamp}: {str(e)}")
                    continue

            # Set index for trades DataFrame
            if not trades.empty:
                trades.set_index('timestamp', inplace=True)

            return {
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': self.initial_capital,
                'final_portfolio_value': portfolio['portfolio_value'],
                'portfolio_history': portfolio_history,
                'trades': trades,
                'signals': signals,
                'price_data': price_data,
                'social_data': social_data
            }

        except Exception as e:
            logger.error(f"Error in backtest: {str(e)}")
            return {}

    def analyze_results(self, results: Dict) -> Dict:
        """Analyze backtest results."""
        try:
            if not results:
                return {}

            portfolio_history = results['portfolio_history']
            trades = results['trades']
            signals = results['signals']
            price_data = results['price_data']
            social_data = results.get('social_data', pd.DataFrame())

            # Calculate returns
            returns = portfolio_history['portfolio_value'].pct_change().dropna()

            # Calculate metrics
            total_return = (float(results['final_portfolio_value']) - float(results['initial_capital'])) / float(results['initial_capital'])
            sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0
            max_drawdown = (portfolio_history['portfolio_value'].cummax() - portfolio_history['portfolio_value']) / portfolio_history['portfolio_value'].cummax()
            max_drawdown = float(max_drawdown.max())

            # Calculate trade metrics
            if not trades.empty:
                winning_trades = trades[trades['value'] > trades['value'].shift(1)]
                total_trades = len(trades)
                win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            else:
                total_trades = 0
                win_rate = 0

            analysis = {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades,
                'win_rate': win_rate
            }

            # Add social metrics if available
            if not social_data.empty and 'weighted_sentiment' in social_data.columns:
                # Calculate correlations
                sentiment_corr = social_data['weighted_sentiment'].corr(returns)
                engagement_corr = social_data['engagement'].corr(returns) if 'engagement' in social_data.columns else 0

                # Find optimal sentiment lag
                max_lag = min(10, len(returns) // 2)
                lag_corrs = [social_data['weighted_sentiment'].shift(i).corr(returns) for i in range(max_lag)]
                optimal_lag = np.argmax(np.abs(lag_corrs))

                # Find significant social events
                sentiment_std = social_data['weighted_sentiment'].std()
                high_sentiment = social_data[np.abs(social_data['weighted_sentiment']) > 2 * sentiment_std]

                # Calculate price moves following high sentiment
                price_moves = []
                for idx in high_sentiment.index:
                    try:
                        start_price = float(price_data.loc[idx, 'Close'])
                        end_price = float(price_data.loc[idx:].iloc[5]['Close'])  # 5 periods forward
                        move = (end_price - start_price) / start_price
                        price_moves.append({
                            'timestamp': idx,
                            'sentiment': float(high_sentiment.loc[idx, 'weighted_sentiment']),
                            'price_move': float(move),
                            'tweet_count': int(high_sentiment.loc[idx, 'tweet_count']) if 'tweet_count' in high_sentiment.columns else 0,
                            'pre_move_sentiment': float(high_sentiment.loc[idx, 'weighted_sentiment'])
                        })
                    except:
                        continue

                # Sort events by absolute price move
                price_moves.sort(key=lambda x: abs(x['price_move']), reverse=True)

                analysis['social_metrics'] = {
                    'sentiment_correlation': float(sentiment_corr),
                    'engagement_correlation': float(engagement_corr),
                    'optimal_sentiment_lag': int(optimal_lag)
                }

                analysis['social_events'] = {
                    'total_significant_events': len(price_moves),
                    'positive_events': len([m for m in price_moves if m['price_move'] > 0]),
                    'negative_events': len([m for m in price_moves if m['price_move'] < 0]),
                    'avg_positive_move': float(np.mean([m['price_move'] for m in price_moves if m['price_move'] > 0])) if price_moves else 0,
                    'avg_negative_move': float(np.mean([m['price_move'] for m in price_moves if m['price_move'] < 0])) if price_moves else 0,
                    'top_events': price_moves[:5]  # Top 5 events by price move magnitude
                }

            return analysis

        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            return {}
