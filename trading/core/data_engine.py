"""
Base data engine implementation for market data handling.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

class DataEngine(ABC):
    """
    Abstract base class for market data handling.

    Provides interface and common functionality for fetching and
    processing market data from various sources.
    """

    def __init__(self):
        """Initialize data engine."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=1)

    @abstractmethod
    def get_price_data(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price data for a symbol.

        Args:
            symbol: The trading symbol
            timeframe: Data timeframe (e.g., "1m", "5m", "1h")
            limit: Number of data points to fetch

        Returns:
            DataFrame with OHLCV data or None if error
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol.

        Args:
            symbol: The trading symbol

        Returns:
            Current price or None if error
        """
        pass

    @abstractmethod
    def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[Dict]:
        """
        Get current orderbook for a symbol.

        Args:
            symbol: The trading symbol
            limit: Number of levels to fetch

        Returns:
            Dict containing bids and asks or None if error
        """
        pass

    def _get_cached_data(self, key: str) -> Optional[Any]:
        """
        Get data from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/missing
        """
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]
        if datetime.utcnow() - cache_entry["timestamp"] > self._cache_ttl:
            del self._cache[key]
            return None

        return cache_entry["data"]

    def _cache_data(self, key: str, data: Any) -> None:
        """
        Cache data with timestamp.

        Args:
            key: Cache key
            data: Data to cache
        """
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.utcnow()
        }

    def _build_cache_key(self, symbol: str, **kwargs) -> str:
        """
        Build cache key from parameters.

        Args:
            symbol: The trading symbol
            **kwargs: Additional parameters

        Returns:
            Cache key string
        """
        key_parts = [symbol]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return ":".join(key_parts)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def set_cache_ttl(self, ttl: timedelta) -> None:
        """
        Set cache TTL.

        Args:
            ttl: New cache TTL
        """
        self._cache_ttl = ttl

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is valid.

        Args:
            symbol: The trading symbol

        Returns:
            True if valid, False otherwise
        """
        pass
