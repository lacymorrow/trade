"""
Base trade engine implementation for order execution.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal

class TradeEngine(ABC):
    """
    Abstract base class for trade execution.

    Provides interface and common functionality for executing trades
    and managing positions.
    """

    def __init__(self, test_mode: bool = True):
        """
        Initialize trade engine.

        Args:
            test_mode: Whether to run in test mode (no real trades)
        """
        self.test_mode = test_mode
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a trade.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Trade quantity
            price: Limit price (optional)
            order_type: Order type (market, limit, etc)
            **kwargs: Additional parameters

        Returns:
            Order details or None if failed
        """
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position details or None if no position
        """
        pass

    @abstractmethod
    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """
        Get current account balance.

        Returns:
            Account balance details or None if error
        """
        pass

    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        risk_percent: float = 0.02
    ) -> float:
        """
        Calculate position size based on risk.

        Args:
            symbol: Trading symbol
            price: Current price
            risk_percent: Percentage of account to risk

        Returns:
            Position size
        """
        try:
            # Get account balance
            balance = self.get_account_balance()
            if not balance:
                return 0

            # Calculate position size
            account_value = float(balance.get('equity', 0))
            risk_amount = account_value * risk_percent

            # Calculate quantity
            quantity = risk_amount / price

            # Round to appropriate decimals
            if price >= 100:
                quantity = round(quantity, 2)
            elif price >= 10:
                quantity = round(quantity, 3)
            else:
                quantity = round(quantity, 4)

            return quantity

        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 0

    def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate order parameters.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Trade quantity
            price: Limit price (optional)

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Basic validation
        if side not in ['buy', 'sell']:
            errors.append("Invalid side (must be 'buy' or 'sell')")

        if quantity <= 0:
            errors.append("Quantity must be positive")

        if price is not None and price <= 0:
            errors.append("Price must be positive")

        # Check account balance for buys
        if side == 'buy':
            balance = self.get_account_balance()
            if balance:
                buying_power = float(balance.get('buying_power', 0))
                if price:
                    cost = price * quantity
                else:
                    # Use current market price
                    current_price = self.get_market_price(symbol)
                    cost = current_price * quantity if current_price else 0

                if cost > buying_power:
                    errors.append("Insufficient buying power")

        # Check position size for sells
        if side == 'sell':
            position = self.get_position(symbol)
            if position:
                current_quantity = float(position.get('quantity', 0))
                if quantity > current_quantity:
                    errors.append("Insufficient position size")

        return len(errors) == 0, errors

    @abstractmethod
    def get_market_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Current price or None if error
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        pass

    def log_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_type: str,
        order_id: str
    ) -> None:
        """
        Log trade details.

        Args:
            symbol: Trading symbol
            side: Trade side
            quantity: Trade quantity
            price: Trade price
            order_type: Order type
            order_id: Order ID
        """
        self.logger.info(
            f"Trade executed - Symbol: {symbol}, Side: {side}, "
            f"Quantity: {quantity}, Price: {price}, Type: {order_type}, "
            f"Order ID: {order_id}"
        )
