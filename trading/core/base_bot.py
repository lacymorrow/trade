"""
Base trading bot implementation that defines common functionality.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

class BaseBot(ABC):
    """
    Abstract base class for trading bots.

    Implements common functionality and defines interface that must be
    implemented by specific bot types (stock, crypto, etc).
    """

    def __init__(self, test_mode: bool = True):
        """
        Initialize base bot functionality.

        Args:
            test_mode (bool): Whether to run in test mode (no real trades)
        """
        self.test_mode = test_mode
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False
        self.symbols: List[str] = []

    def start(self) -> None:
        """Start the trading bot."""
        self.logger.info("Starting trading bot...")
        self.running = True

        try:
            # Initialize components
            if not self._initialize():
                self.logger.error("Failed to initialize bot")
                return

            # Main trading loop
            while self.running:
                try:
                    # Update symbols if needed
                    self.update_symbols()

                    # Check if we can trade
                    if not self._can_trade():
                        self.logger.info("Cannot trade right now, waiting...")
                        continue

                    # Analyze symbols
                    self.analyze_symbols()

                    # Wait before next iteration
                    self._wait_for_next_cycle()

                except KeyboardInterrupt:
                    self.logger.info("Received stop signal")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {str(e)}")
                    self._handle_error(e)

        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the trading bot."""
        self.logger.info("Stopping trading bot...")
        self.running = False
        self._cleanup()

    @abstractmethod
    def _initialize(self) -> bool:
        """
        Initialize bot components.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def _can_trade(self) -> bool:
        """
        Check if trading is currently possible.

        Returns:
            bool: True if trading is possible, False otherwise
        """
        pass

    @abstractmethod
    def update_symbols(self) -> None:
        """Update the list of symbols to trade."""
        pass

    @abstractmethod
    def analyze_symbols(self) -> None:
        """Analyze current symbols for trading opportunities."""
        pass

    @abstractmethod
    def _cleanup(self) -> None:
        """Cleanup resources before stopping."""
        pass

    def _wait_for_next_cycle(self) -> None:
        """Wait for next trading cycle."""
        import time
        time.sleep(60)  # Default 1 minute

    def _handle_error(self, error: Exception) -> None:
        """
        Handle errors in main loop.

        Args:
            error (Exception): The error that occurred
        """
        import time
        self.logger.exception("Error occurred:")
        time.sleep(60)  # Wait before retrying

    def get_status(self) -> Dict[str, Any]:
        """
        Get current bot status.

        Returns:
            Dict containing bot status information
        """
        return {
            "running": self.running,
            "test_mode": self.test_mode,
            "symbols": self.symbols,
            "timestamp": datetime.utcnow().isoformat()
        }

    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """
        Validate bot configuration.

        Returns:
            Tuple[bool, List[str]]: (is_valid, list of error messages)
        """
        errors = []

        # Basic validation
        if not self.symbols:
            errors.append("No symbols configured")

        return len(errors) == 0, errors
