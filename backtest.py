import logging
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from trading.data_engine import DataEngine
from trading.signal_engine import SignalEngine
from trading.trade_engine import TradeEngine
from trading.backtest_engine import BacktestEngine
from config import TRADING_CAPITAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_performance_plot(results, symbol):
    """Create performance visualization."""
    fig = make_subplots(rows=3, cols=1,
                       subplot_titles=('Portfolio Value', 'Social Sentiment', 'Trading Signals'),
                       vertical_spacing=0.1,
                       row_heights=[0.5, 0.25, 0.25])

    # Portfolio value
    fig.add_trace(
        go.Scatter(x=results['portfolio_history'].index,
                  y=results['portfolio_history']['portfolio_value'],
                  name='Portfolio Value'),
        row=1, col=1
    )

    # Social sentiment
    if 'social_analysis' in results and not results['social_data'].empty:
        fig.add_trace(
            go.Scatter(x=results['social_data'].index,
                      y=results['social_data']['weighted_sentiment'],
                      name='Social Sentiment'),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=results['social_data'].index,
                      y=results['social_data']['engagement'],
                      name='Social Engagement',
                      yaxis='y3'),
            row=2, col=1
        )

    # Trading signals
    fig.add_trace(
        go.Scatter(x=results['signals'].index,
                  y=results['signals']['signal_strength'],
                  name='Signal Strength'),
        row=3, col=1
    )

    # Add trade markers
    buys = results['trades'][results['trades']['side'] == 'buy']
    sells = results['trades'][results['trades']['side'] == 'sell']

    fig.add_trace(
        go.Scatter(x=buys.index, y=buys['price'],
                  mode='markers', name='Buy',
                  marker=dict(symbol='triangle-up', size=10, color='green')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=sells.index, y=sells['price'],
                  mode='markers', name='Sell',
                  marker=dict(symbol='triangle-down', size=10, color='red')),
        row=1, col=1
    )

    fig.update_layout(
        title=f'Backtest Results for {symbol}',
        height=1000,
        showlegend=True
    )

    return fig

def run_backtest(symbols, start_date=None, end_date=None):
    """Run backtest for multiple symbols."""
    if start_date is None:
        start_date = datetime.now() - timedelta(days=30)
    if end_date is None:
        end_date = datetime.now()

    # Initialize engines
    data_engine = DataEngine()
    signal_engine = SignalEngine(data_engine)
    trade_engine = TradeEngine()
    backtest_engine = BacktestEngine(
        config={'initial_capital': TRADING_CAPITAL},
        data_engine=data_engine,
        signal_engine=signal_engine,
        trade_engine=trade_engine
    )

    all_results = {}
    for symbol in symbols:
        logger.info(f"\nRunning backtest for {symbol}...")

        try:
            # Run backtest
            results = backtest_engine.run_backtest(symbol, start_date, end_date)
            analysis = backtest_engine.analyze_results(results)

            # Store results
            all_results[symbol] = {
                'results': results,
                'analysis': analysis
            }

            # Print analysis
            print(f"\n=== {symbol} Backtest Results ===")
            print(f"Total Return: {analysis['total_return']:.2%}")
            print(f"Sharpe Ratio: {analysis['sharpe_ratio']:.2f}")
            print(f"Max Drawdown: {analysis['max_drawdown']:.2%}")
            print(f"Win Rate: {analysis['win_rate']:.2%}")
            print(f"Total Trades: {analysis['total_trades']}")

            # Print social metrics
            if 'social_metrics' in analysis:
                print("\nSocial Analysis:")
                print(f"Sentiment Correlation: {analysis['social_metrics']['sentiment_correlation']:.2f}")
                print(f"Engagement Correlation: {analysis['social_metrics']['engagement_correlation']:.2f}")
                print(f"Optimal Sentiment Lag: {analysis['social_metrics']['optimal_sentiment_lag']} periods")

                if 'social_events' in analysis:
                    events = analysis['social_events']
                    print(f"\nSignificant Social Events: {events['total_significant_events']}")
                    print(f"Positive Events: {events['positive_events']}")
                    print(f"Negative Events: {events['negative_events']}")
                    print(f"Avg Positive Move: {events['avg_positive_move']:.2%}")
                    print(f"Avg Negative Move: {events['avg_negative_move']:.2%}")

                    print("\nTop Social Impact Events:")
                    for i, event in enumerate(events['top_events'][:3], 1):
                        print(f"\nEvent {i}:")
                        print(f"Date: {event['timestamp']}")
                        print(f"Price Move: {event['price_move']:.2%}")
                        print(f"Pre-move Sentiment: {event['pre_move_sentiment']:.2f}")
                        print(f"Tweet Count: {event['tweet_count']}")

            # Create and save visualization
            fig = create_performance_plot(results, symbol)
            fig.write_html(f"backtest_{symbol}.html")

        except Exception as e:
            logger.error(f"Error in backtest for {symbol}: {str(e)}")
            continue

    return all_results

if __name__ == "__main__":
    symbols = ['GME', 'TSLA', 'NVDA', 'NFLX']
    start_date = datetime.now() - timedelta(days=30)
    results = run_backtest(symbols, start_date=start_date)
