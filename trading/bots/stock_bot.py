"""
Stock trading bot implementation.
"""

import logging
import time
from typing import Dict, List, Optional, Any
import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta
from ..core.base_bot import BaseBot
from ..core.data_engine import DataEngine
from ..core.signal_engine import SignalEngine
from ..core.trade_engine import TradeEngine

class StockDataEngine(DataEngine):
    """Stock market data implementation using Alpaca API."""

    def __init__(self, api: tradeapi.REST):
        super().__init__()
        self.api = api
        self._request_count = 0
        self._last_request_time = datetime.now()
        self._rate_limit = 200  # requests per minute

    def _rate_limit_wait(self):
        """Handle rate limiting."""
        self._request_count += 1
        now = datetime.now()

        # Reset counter if a minute has passed
        if (now - self._last_request_time).seconds >= 60:
            self._request_count = 1
            self._last_request_time = now
            return

        # Wait if we're approaching the limit
        if self._request_count >= self._rate_limit:
            sleep_time = 60 - (now - self._last_request_time).seconds
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, waiting {sleep_time} seconds...")
                time.sleep(sleep_time)
            self._request_count = 1
            self._last_request_time = datetime.now()

    def get_price_data(
        self,
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Get historical price data from Alpaca."""
        cache_key = self._build_cache_key(symbol, timeframe=timeframe, limit=limit)
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached

        try:
            self._rate_limit_wait()
            bars = self.api.get_bars(
                symbol,
                timeframe,
                limit=limit
            ).df

            if not bars.empty:
                self._cache_data(cache_key, bars)
                return bars

        except Exception as e:
            self.logger.error(f"Error fetching price data for {symbol}: {str(e)}")

        return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Alpaca."""
        try:
            trade = self.api.get_latest_trade(symbol)
            return float(trade.price)
        except Exception as e:
            self.logger.error(f"Error fetching current price: {str(e)}")
            return None

    def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[Dict]:
        """Get current orderbook from Alpaca."""
        try:
            quotes = self.api.get_latest_quotes(symbol)
            return {
                "bids": [{"price": quotes.bidprice, "size": quotes.bidsize}],
                "asks": [{"price": quotes.askprice, "size": quotes.asksize}]
            }
        except Exception as e:
            self.logger.error(f"Error fetching orderbook: {str(e)}")
            return None

    def validate_symbol(self, symbol: str) -> bool:
        """Validate symbol exists on Alpaca."""
        try:
            self.api.get_asset(symbol)
            return True
        except Exception:
            return False

class StockSignalEngine(SignalEngine):
    """Stock market signal generation implementation."""

    def __init__(self, data_engine: StockDataEngine):
        super().__init__()
        self.data_engine = data_engine

    def generate_signal(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Generate trading signal for stocks."""
        try:
            # Calculate technical indicators
            indicators = self.calculate_technical_indicators(price_data)

            # Calculate signal strength
            strength = self.calculate_signal_strength(indicators)

            # Generate signal if strength is significant
            if abs(strength) >= 0.5:  # Minimum strength threshold
                return {
                    "symbol": symbol,
                    "action": "buy" if strength > 0 else "sell",
                    "strength": strength,
                    "price": price_data["close"].iloc[-1],
                    "timestamp": datetime.utcnow().isoformat(),
                    "indicators": indicators
                }

        except Exception as e:
            self.logger.error(f"Error generating signal: {str(e)}")

        return None

    def calculate_signal_strength(
        self,
        indicators: Dict[str, Any],
        **kwargs
    ) -> float:
        """Calculate signal strength for stocks."""
        try:
            # Get latest indicator values
            rsi = indicators["rsi"].iloc[-1]
            macd = indicators["macd"].iloc[-1]
            macd_signal = indicators["macd_signal"].iloc[-1]
            volume_ratio = indicators["volume_ratio"].iloc[-1]

            # Calculate individual signals
            rsi_signal = (rsi - 50) / 50  # -1 to 1
            macd_signal = 1 if macd > macd_signal else -1
            volume_signal = min(1, volume_ratio - 1)

            # Combine signals with weights
            strength = (
                rsi_signal * 0.4 +
                macd_signal * 0.4 +
                volume_signal * 0.2
            )

            return max(min(strength, 1), -1)  # Clamp between -1 and 1

        except Exception as e:
            self.logger.error(f"Error calculating signal strength: {str(e)}")
            return 0

class StockTradeEngine(TradeEngine):
    """Stock market trade execution implementation using Alpaca."""

    def __init__(self, api: tradeapi.REST, test_mode: bool = True):
        super().__init__(test_mode)
        self.api = api

    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute trade on Alpaca."""
        try:
            # Validate order
            is_valid, errors = self.validate_order(symbol, side, quantity, price)
            if not is_valid:
                self.logger.error(f"Invalid order: {', '.join(errors)}")
                return None

            if self.test_mode:
                self.logger.info(
                    f"TEST MODE: Would execute {side} {quantity} {symbol} "
                    f"at {price if price else 'market'}"
                )
                return {
                    "id": "test",
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "type": order_type,
                    "status": "filled"
                }

            # Execute real trade
            order = self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type=order_type,
                time_in_force="gtc",
                limit_price=price if order_type == "limit" else None
            )

            return {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.qty),
                "price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "type": order.type,
                "status": order.status
            }

        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return None

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position from Alpaca."""
        try:
            position = self.api.get_position(symbol)
            return {
                "symbol": position.symbol,
                "quantity": float(position.qty),
                "entry_price": float(position.avg_entry_price),
                "current_price": float(position.current_price),
                "profit_loss": float(position.unrealized_pl),
                "profit_loss_percent": float(position.unrealized_plpc)
            }
        except Exception as e:
            if "404" not in str(e):  # Ignore 404 (no position)
                self.logger.error(f"Error getting position: {str(e)}")
            return None

    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """Get account balance from Alpaca."""
        try:
            account = self.api.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "day_trades": int(account.daytrade_count)
            }
        except Exception as e:
            self.logger.error(f"Error getting account balance: {str(e)}")
            return None

    def get_market_price(self, symbol: str) -> Optional[float]:
        """Get current market price from Alpaca."""
        try:
            trade = self.api.get_latest_trade(symbol)
            return float(trade.price)
        except Exception as e:
            self.logger.error(f"Error getting market price: {str(e)}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order on Alpaca."""
        try:
            self.api.cancel_order(order_id)
            return True
        except Exception as e:
            self.logger.error(f"Error canceling order: {str(e)}")
            return False

class StockBot(BaseBot):
    """Stock trading bot implementation."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        test_mode: bool = True
    ):
        """Initialize stock trading bot."""
        super().__init__(test_mode)

        # Initialize Alpaca API
        self.api = tradeapi.REST(
            api_key,
            api_secret,
            base_url,
            api_version="v2"
        )

        # Initialize components
        self.data_engine = StockDataEngine(self.api)
        self.signal_engine = StockSignalEngine(self.data_engine)
        self.trade_engine = StockTradeEngine(self.api, test_mode)

    def _initialize(self) -> bool:
        """Initialize bot components."""
        try:
            # Check API connection
            self.api.get_account()

            # Update trading symbols
            self.update_symbols()

            return True

        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    def _can_trade(self) -> bool:
        """Check if trading is currently possible."""
        try:
            # Check market hours
            clock = self.api.get_clock()
            if not clock.is_open and not self.test_mode:
                self.logger.info("Market is closed")
                return False

            # Check account status
            account = self.api.get_account()
            if account.trading_blocked:
                self.logger.error("Account is blocked from trading")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking trade status: {str(e)}")
            return False

    def update_symbols(self) -> None:
        """Update list of tradeable symbols."""
        try:
            assets = self.api.list_assets(status="active")
            self.symbols = [
                asset.symbol for asset in assets
                if asset.tradable and asset.marginable
            ]
            self.logger.info(f"Updated symbols: {len(self.symbols)} available")

        except Exception as e:
            self.logger.error(f"Error updating symbols: {str(e)}")

    def analyze_symbols(self) -> None:
        """Analyze symbols for trading opportunities."""
        for symbol in self.symbols:
            try:
                # Get price data
                price_data = self.data_engine.get_price_data(symbol)
                if price_data is None:
                    continue

                # Generate trading signal
                signal = self.signal_engine.generate_signal(symbol, price_data)
                if signal is None:
                    continue

                # Execute trade if signal is strong enough
                if abs(signal["strength"]) >= 0.8:  # High conviction threshold
                    price = signal["price"]
                    quantity = self.trade_engine.calculate_position_size(
                        symbol,
                        price,
                        risk_percent=0.02
                    )

                    if quantity > 0:
                        self.trade_engine.execute_trade(
                            symbol=symbol,
                            side=signal["action"],
                            quantity=quantity,
                            price=price
                        )

            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {str(e)}")
                continue

    def _cleanup(self) -> None:
        """Cleanup resources."""
        # Cancel all open orders
        try:
            if not self.test_mode:
                self.api.cancel_all_orders()
        except Exception as e:
            self.logger.error(f"Error cleaning up: {str(e)}")
