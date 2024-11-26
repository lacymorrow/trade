import logging
from datetime import datetime, timedelta
from crypto.backtest_engine import BacktestEngine
from crypto_config import TRADING_PAIRS, DEFAULT_TIMEFRAME

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_metrics(metrics):
    """Format metrics for display."""
    return f"""
    Performance Metrics:
    -------------------
    Total Trades: {metrics['total_trades']}
    Winning Trades: {metrics['winning_trades']}
    Losing Trades: {metrics['losing_trades']}
    Win Rate: {metrics['win_rate']:.2f}%

    Total PnL: ${metrics['total_pnl']:.2f}
    Total Return: {metrics['total_pnl_percentage']:.2f}%
    Average Trade PnL: ${metrics['average_trade_pnl']:.2f}

    Max Drawdown: {metrics['max_drawdown']:.2f}%
    Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
    Average Trade Duration: {metrics['average_trade_duration']}
    """

def main():
    """Run backtests for configured trading pairs."""
    try:
        # Initialize backtest engine
        engine = BacktestEngine()

        # Set backtest period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        # Run backtests for each trading pair
        for symbol in TRADING_PAIRS:
            logger.info(f"\nRunning backtest for {symbol}")
            logger.info("=" * 50)

            results = engine.run_backtest(
                symbol=symbol,
                timeframe=DEFAULT_TIMEFRAME,
                start_date=start_date,
                end_date=end_date
            )

            if results:
                logger.info(format_metrics(results['metrics']))

                # Save results to CSV
                results['results'].to_csv(f'backtest_results_{symbol.replace("/", "_")}.csv')
                results['trades'].to_csv(f'backtest_trades_{symbol.replace("/", "_")}.csv')

            else:
                logger.error(f"Backtest failed for {symbol}")

    except KeyboardInterrupt:
        logger.info("Backtest interrupted by user")
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")

if __name__ == "__main__":
    main()
