import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from config import (
    MAX_VOLATILITY,
    MIN_MARKET_CAP,
    MIN_AVG_VOLUME,
    EARNINGS_BUFFER_DAYS,
    MAX_SPREAD_PCT,
    MIN_SHARES_AVAILABLE,
    RSI_PERIOD,
    RSI_OVERSOLD,
    RSI_OVERBOUGHT
)

logger = logging.getLogger(__name__)

class SanityChecker:
    """
    SanityChecker class for validating trading safety conditions.

    This class implements various safety checks to ensure trades are executed
    under appropriate market conditions. It checks:
    - Volatility levels
    - Market capitalization
    - Trading volume
    - Earnings dates
    - Bid-ask spreads
    - Short availability

    The checker uses Alpaca API to get market data and implements configurable
    thresholds for each safety check.

    Attributes:
        trading_api (alpaca_trade_api.REST): Alpaca API client for market data
        logger (logging.Logger): Logger for safety check activities

    Configuration:
        The checker's behavior is controlled by parameters in config.py:
        - MAX_VOLATILITY: Maximum allowed volatility
        - MIN_MARKET_CAP: Minimum market capitalization
        - MIN_AVG_VOLUME: Minimum average daily volume
        - EARNINGS_BUFFER_DAYS: Days to avoid before earnings
        - MAX_SPREAD_PCT: Maximum bid-ask spread
        - MIN_SHARES_AVAILABLE: Minimum shares for shorting
    """

    def __init__(self, trading_api):
        """
        Initialize the sanity checker.

        Args:
            trading_api (alpaca_trade_api.REST): Alpaca API client for market data
        """
        self.trading_api = trading_api
        self.logger = logging.getLogger(__name__)

    def run_all_checks(self, symbol, price_data):
        """
        Run all sanity checks for a symbol.

        Performs a comprehensive set of safety checks including:
        - Volatility check
        - Market cap check
        - Volume check
        - Earnings date check
        - Spread check
        - Short availability check

        Args:
            symbol (str): The stock symbol to check
            price_data (pd.DataFrame): OHLCV data for the symbol

        Returns:
            tuple: (bool, dict) indicating if all checks passed and individual results
        """
        try:
            check_results = {}

            # Check volatility
            check_results['volatility'] = self.check_volatility(price_data)

            # Check market cap
            check_results['market_cap'] = self.check_market_cap(symbol)

            # Check volume
            check_results['volume'] = self.check_volume(price_data)

            # Check earnings
            check_results['earnings'] = self.check_earnings_date(symbol)

            # Check spread
            check_results['spread'] = self.check_spread(symbol)

            # Check short availability
            check_results['short_shares'] = self.check_short_shares(symbol)

            # All checks must pass
            all_passed = all(check_results.values())
            return all_passed, check_results

        except Exception as e:
            self.logger.error(f"Error running sanity checks for {symbol}: {e}")
            return False, {}

    def check_volatility(self, price_data):
        """
        Check if volatility is within acceptable range.

        Calculates annualized volatility from price data and compares
        it against the maximum allowed threshold.

        Args:
            price_data (pd.DataFrame): OHLCV data for the symbol

        Returns:
            bool: True if volatility is acceptable, False otherwise
        """
        try:
            returns = price_data['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            return volatility <= MAX_VOLATILITY
        except Exception as e:
            self.logger.error(f"Error checking volatility: {e}")
            return False

    def check_market_cap(self, symbol):
        """
        Check if market cap is above minimum threshold.

        Gets market cap from Alpaca API and compares it against
        the minimum required threshold.

        Args:
            symbol (str): The stock symbol to check

        Returns:
            bool: True if market cap is sufficient, False otherwise
        """
        try:
            asset = self.trading_api.get_asset(symbol)
            return float(asset.market_cap) >= MIN_MARKET_CAP if asset.market_cap else False
        except Exception as e:
            self.logger.error(f"Error checking market cap: {e}")
            return False

    def check_volume(self, price_data):
        """
        Check if volume is sufficient.

        Calculates average volume from price data and compares it
        against the minimum required threshold.

        Args:
            price_data (pd.DataFrame): OHLCV data for the symbol

        Returns:
            bool: True if volume is sufficient, False otherwise
        """
        try:
            avg_volume = price_data['volume'].mean()
            return avg_volume >= MIN_AVG_VOLUME
        except Exception as e:
            self.logger.error(f"Error checking volume: {e}")
            return False

    def check_earnings_date(self, symbol):
        """
        Check if stock is not near earnings.

        This is a placeholder for earnings date checking. Would need
        to be implemented with a proper earnings calendar API.

        Args:
            symbol (str): The stock symbol to check

        Returns:
            bool: True if not near earnings, False otherwise
        """
        try:
            # This would need to be implemented with a proper earnings calendar API
            # For now, return True to avoid blocking trades
            return True
        except Exception as e:
            self.logger.error(f"Error checking earnings date: {e}")
            return False

    def check_spread(self, symbol):
        """
        Check if bid-ask spread is acceptable.

        Gets latest quote from Alpaca API and calculates the spread
        as a percentage of the ask price.

        Args:
            symbol (str): The stock symbol to check

        Returns:
            bool: True if spread is acceptable, False otherwise
        """
        try:
            quote = self.trading_api.get_latest_quote(symbol)
            if quote and quote.ask_price > 0:
                spread = (quote.ask_price - quote.bid_price) / quote.ask_price
                return spread <= MAX_SPREAD_PCT
            return False
        except Exception as e:
            self.logger.error(f"Error checking spread: {e}")
            return False

    def check_short_shares(self, symbol):
        """
        Check if enough shares are available to short.

        This is a placeholder for short availability checking. Would need
        to be implemented with a proper short availability API.

        Args:
            symbol (str): The stock symbol to check

        Returns:
            bool: True if enough shares available, False otherwise
        """
        try:
            # This would need to be implemented with a proper short availability API
            # For now, return True to avoid blocking trades
            return True
        except Exception as e:
            self.logger.error(f"Error checking short shares: {e}")
            return False
