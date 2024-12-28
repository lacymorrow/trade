"""
Cryptocurrency trading bot implementation.
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
import requests
import json

class CryptoDataEngine(DataEngine):
    """Crypto market data implementation using Alpaca Crypto API."""

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
        """Get historical crypto price data."""
        cache_key = self._build_cache_key(symbol, timeframe=timeframe, limit=limit)
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached

        try:
            # Ensure symbol has /USD suffix
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"

            self._rate_limit_wait()

            # Get current time
            end = datetime.now()
            start = end - timedelta(minutes=limit)

            # Get bars with proper time range
            bars = self.api.get_crypto_bars(
                symbol,
                timeframe,
                start=start.isoformat(),
                end=end.isoformat()
            ).df

            if not bars.empty:
                # Ensure we have the right columns
                required_columns = ['open', 'high', 'low', 'close', 'volume']
                if all(col in bars.columns for col in required_columns):
                    self._cache_data(cache_key, bars)
                    return bars
                else:
                    self.logger.error(f"Missing required columns in data for {symbol}")

        except Exception as e:
            self.logger.error(f"Error fetching crypto price data for {symbol}: {str(e)}")

        return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current crypto price."""
        try:
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"

            trade = self.api.get_latest_crypto_trade(symbol)
            return float(trade.price)
        except Exception as e:
            self.logger.error(f"Error fetching current crypto price: {str(e)}")
            return None

    def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[Dict]:
        """Get current crypto orderbook."""
        try:
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"

            quotes = self.api.get_latest_crypto_quotes(symbol)
            return {
                "bids": [{"price": quotes.bidprice, "size": quotes.bidsize}],
                "asks": [{"price": quotes.askprice, "size": quotes.asksize}]
            }
        except Exception as e:
            self.logger.error(f"Error fetching crypto orderbook: {str(e)}")
            return None

    def validate_symbol(self, symbol: str) -> bool:
        """Validate crypto symbol exists."""
        try:
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"
            self.api.get_latest_crypto_trade(symbol)
            return True
        except Exception:
            return False

    def get_recent_trades(self, symbol: str, limit: int = 50) -> Optional[pd.DataFrame]:
        """Get recent trades for a symbol."""
        try:
            # Input validation
            if not isinstance(symbol, str):
                self.logger.error(f"Invalid symbol type: {type(symbol)}")
                return None

            if not isinstance(limit, int) or limit <= 0:
                self.logger.error(f"Invalid limit: {limit}")
                return None

            # Ensure symbol format is correct
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"

            self._rate_limit_wait()

            # Get current time and use a longer window (1 hour)
            end = datetime.now()
            start = end - timedelta(hours=1)

            # Format timestamps in RFC3339 format
            try:
                start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
                end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                self.logger.error(f"Error formatting timestamps: {str(e)}")
                return None

            self.logger.info(f"Fetching trades for {symbol} from {start_str} to {end_str}")
            self.logger.info(f"API Key ID: {self.api._key_id[:8]}...")  # Log first 8 chars of key

            # Get trades using the Alpaca API
            try:
                self.logger.info("Making API call to get_trades...")

                # Build URL for crypto trades (v1beta3 endpoint)
                base_url = "https://data.alpaca.markets/v1beta3"
                trades_url = f"{base_url}/crypto/us/trades"

                # Add API key to headers
                headers = {
                    'APCA-API-KEY-ID': self.api._key_id,
                    'APCA-API-SECRET-KEY': self.api._secret_key
                }

                # Get trades
                params = {
                    'symbols': [symbol],  # Keep the symbol format as "BTC/USD"
                    'start': start_str,
                    'end': end_str,
                    'limit': limit
                }

                self.logger.info(f"Request URL: {trades_url}")
                self.logger.info(f"Request params: {params}")

                # Make API request with timeout
                try:
                    response = self.api._session.get(trades_url, headers=headers, params=params, timeout=10)
                    response.raise_for_status()
                except requests.exceptions.Timeout:
                    self.logger.error("API request timed out")
                    return None
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"API request failed: {str(e)}")
                    return None

                # Parse JSON response
                try:
                    trades_data = response.json()
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response: {str(e)}")
                    return None

                self.logger.info(f"API Response type: {type(trades_data)}")
                self.logger.info(f"API Response keys: {trades_data.keys() if isinstance(trades_data, dict) else 'N/A'}")

                # Validate response structure
                if not isinstance(trades_data, dict):
                    self.logger.error(f"Invalid response type: {type(trades_data)}")
                    return None

                if 'trades' not in trades_data:
                    self.logger.warning(f"No trades data in response for {symbol}")
                    return None

                if symbol not in trades_data['trades']:
                    self.logger.warning(f"No trades found for {symbol}")
                    return None

                # Convert trades to DataFrame
                trades_list = []
                for trade in trades_data['trades'][symbol]:
                    if not isinstance(trade, dict):
                        self.logger.warning(f"Invalid trade data type: {type(trade)}")
                        continue

                    try:
                        trades_list.append({
                            'timestamp': pd.Timestamp(trade['t']),
                            'price': float(trade['p']),
                            'size': float(trade['s']),
                            'side': 'buy' if trade['tks'].lower() == 'b' else 'sell'
                        })
                    except (KeyError, ValueError, TypeError) as e:
                        self.logger.warning(f"Error processing trade: {str(e)}")
                        continue

                if not trades_list:
                    self.logger.warning(f"No valid trades found for {symbol}")
                    return None

                # Create DataFrame
                try:
                    trades_df = pd.DataFrame(trades_list)
                    trades_df.set_index('timestamp', inplace=True)
                    trades_df.sort_index(ascending=False, inplace=True)
                except Exception as e:
                    self.logger.error(f"Error creating DataFrame: {str(e)}")
                    return None

                self.logger.info(f"Created DataFrame with shape: {trades_df.shape}")
                self.logger.info(f"First few rows:\n{trades_df.head()}")

                return trades_df

            except Exception as e:
                self.logger.error(f"API call failed: {str(e)}")
                self.logger.error(f"Error type: {type(e)}")
                self.logger.error(f"Error args: {e.args}")
                if isinstance(e, requests.exceptions.HTTPError):
                    response = e.response
                    self.logger.error(f"Response status code: {response.status_code}")
                    self.logger.error(f"Response headers: {response.headers}")
                    self.logger.error(f"Response text: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching recent trades for {symbol}: {str(e)}")
            self.logger.error(f"Error type: {type(e)}")
            self.logger.error(f"Error args: {e.args}")
            if hasattr(e, '__dict__'):
                self.logger.error(f"Error details: {e.__dict__}")
            return None

class CryptoSignalEngine(SignalEngine):
    """Crypto market signal generation implementation."""

    def __init__(self, data_engine: CryptoDataEngine):
        super().__init__()
        self.data_engine = data_engine

    def generate_signal(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Generate trading signal for crypto."""
        try:
            # Calculate technical indicators
            indicators = self.calculate_technical_indicators(price_data)

            # Calculate signal strength
            strength = self.calculate_signal_strength(indicators)

            # Generate signal if strength is significant
            if abs(strength) >= 0.6:  # Higher threshold for crypto
                return {
                    "symbol": symbol,
                    "action": "buy" if strength > 0 else "sell",
                    "strength": strength,
                    "price": price_data["close"].iloc[-1],
                    "timestamp": datetime.utcnow().isoformat(),
                    "indicators": indicators
                }

        except Exception as e:
            self.logger.error(f"Error generating crypto signal: {str(e)}")

        return None

    def calculate_signal_strength(
        self,
        indicators: Dict[str, Any],
        **kwargs
    ) -> float:
        """Calculate signal strength for crypto."""
        try:
            # Get latest indicator values
            rsi = indicators["rsi"].iloc[-1]
            macd = indicators["macd"].iloc[-1]
            macd_signal = indicators["macd_signal"].iloc[-1]
            volume_ratio = indicators["volume_ratio"].iloc[-1]
            volatility = indicators["volatility"].iloc[-1]

            # Calculate individual signals
            rsi_signal = (rsi - 50) / 50  # -1 to 1
            macd_signal = 1 if macd > macd_signal else -1
            volume_signal = min(1, volume_ratio - 1)

            # Adjust for volatility
            volatility_factor = 1 - min(volatility * 2, 0.5)  # Reduce signal in high volatility

            # Combine signals with weights
            strength = (
                rsi_signal * 0.3 +
                macd_signal * 0.3 +
                volume_signal * 0.4  # Higher weight on volume for crypto
            ) * volatility_factor

            return max(min(strength, 1), -1)  # Clamp between -1 and 1

        except Exception as e:
            self.logger.error(f"Error calculating crypto signal strength: {str(e)}")
            return 0

class CryptoTradeEngine(TradeEngine):
    """Crypto market trade execution implementation."""

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
        """Execute crypto trade."""
        try:
            # Ensure symbol format
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"

            # Validate order
            is_valid, errors = self.validate_order(symbol, side, quantity, price)
            if not is_valid:
                self.logger.error(f"Invalid crypto order: {', '.join(errors)}")
                return None

            if self.test_mode:
                self.logger.info(
                    f"TEST MODE: Would execute crypto {side} {quantity} {symbol} "
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
            self.logger.error(f"Error executing crypto trade: {str(e)}")
            return None

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get crypto position."""
        try:
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"

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
                self.logger.error(f"Error getting crypto position: {str(e)}")
            return None

    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """Get crypto account balance."""
        try:
            account = self.api.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "crypto_status": account.crypto_status
            }
        except Exception as e:
            self.logger.error(f"Error getting crypto account balance: {str(e)}")
            return None

    def get_market_price(self, symbol: str) -> Optional[float]:
        """Get current crypto market price."""
        try:
            if not symbol.endswith("/USD"):
                symbol = f"{symbol}/USD"
            trade = self.api.get_latest_crypto_trade(symbol)
            return float(trade.price)
        except Exception as e:
            self.logger.error(f"Error getting crypto market price: {str(e)}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel crypto order."""
        try:
            self.api.cancel_order(order_id)
            return True
        except Exception as e:
            self.logger.error(f"Error canceling crypto order: {str(e)}")
            return False

class CryptoBot(BaseBot):
    """Cryptocurrency trading bot implementation."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        test_mode: bool = True
    ):
        """Initialize crypto trading bot."""
        super().__init__(test_mode)

        # Initialize Alpaca API
        self.api = tradeapi.REST(
            api_key,
            api_secret,
            base_url,
            api_version="v2"
        )

        # Initialize components
        self.data_engine = CryptoDataEngine(self.api)
        self.signal_engine = CryptoSignalEngine(self.data_engine)
        self.trade_engine = CryptoTradeEngine(self.api, test_mode)

        # Default crypto pairs
        self.default_symbols = ["BTC", "ETH", "SOL"]

    def _initialize(self) -> bool:
        """Initialize bot components."""
        try:
            # Check API connection
            self.api.get_account()

            # Update trading symbols
            self.update_symbols()

            return True

        except Exception as e:
            self.logger.error(f"Crypto bot initialization failed: {str(e)}")
            return False

    def _can_trade(self) -> bool:
        """Check if crypto trading is possible."""
        try:
            # Check account status
            account = self.api.get_account()
            if account.trading_blocked:
                self.logger.error("Account is blocked from trading")
                return False

            if account.crypto_status != "ACTIVE":
                self.logger.error("Crypto trading not active")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking crypto trade status: {str(e)}")
            return False

    def update_symbols(self) -> None:
        """Update list of tradeable crypto symbols."""
        try:
            # Get available crypto pairs
            assets = self.api.list_assets(asset_class="crypto")
            self.symbols = [
                asset.symbol.replace("/USD", "") for asset in assets
                if asset.tradable
            ]

            if not self.symbols:
                self.logger.warning("No crypto pairs found, using defaults")
                self.symbols = self.default_symbols

            self.logger.info(f"Updated crypto symbols: {len(self.symbols)} available")

        except Exception as e:
            self.logger.error(f"Error updating crypto symbols: {str(e)}")
            self.symbols = self.default_symbols

    def analyze_symbols(self) -> None:
        """Analyze crypto symbols for trading opportunities."""
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
                        risk_percent=0.01  # Lower risk for crypto
                    )

                    if quantity > 0:
                        self.trade_engine.execute_trade(
                            symbol=symbol,
                            side=signal["action"],
                            quantity=quantity,
                            price=price
                        )

            except Exception as e:
                self.logger.error(f"Error analyzing crypto {symbol}: {str(e)}")
                continue

    def _cleanup(self) -> None:
        """Cleanup resources."""
        # Cancel all open orders
        try:
            if not self.test_mode:
                self.api.cancel_all_orders()
        except Exception as e:
            self.logger.error(f"Error cleaning up crypto bot: {str(e)}")

    def get_trading_pairs(self):
        """Get list of trading pairs."""
        return ["BTC/USD", "ETH/USD", "SOL/USD"]  # Default trading pairs
