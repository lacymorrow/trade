import pandas as pd
import numpy as np
import ta
import logging
from crypto_config import (
    FAST_EMA, SLOW_EMA, SIGNAL_EMA,
    RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD,
    STRATEGY_PARAMS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoSignalEngine:
    def __init__(self, data_engine):
        self.data_engine = data_engine

    def calculate_indicators(self, df):
        """Calculate technical indicators for the given DataFrame."""
        try:
            # MACD
            df['macd'] = ta.trend.macd_diff(df['close'],
                                          window_slow=SLOW_EMA,
                                          window_fast=FAST_EMA,
                                          window_sign=SIGNAL_EMA)

            # RSI
            df['rsi'] = ta.momentum.rsi(df['close'], window=RSI_PERIOD)

            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['close'], window=20)
            df['bb_upper'] = bollinger.bollinger_hband()
            df['bb_lower'] = bollinger.bollinger_lband()
            df['bb_middle'] = bollinger.bollinger_mavg()

            # Volume indicators
            df['volume_ema'] = ta.trend.ema_indicator(df['volume'], window=20)
            df['volume_sma'] = df['volume'].rolling(window=20).mean()

            # Additional indicators
            df['ema_200'] = ta.trend.ema_indicator(df['close'], window=200)
            df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return None

    def generate_signal(self, symbol, timeframe='15m'):
        """Generate trading signal for a symbol."""
        try:
            # Get market data
            df = self.data_engine.get_ohlcv(symbol, timeframe=timeframe, limit=300)
            if df is None:
                return None

            # Calculate indicators
            df = self.calculate_indicators(df)
            if df is None:
                return None

            # Get additional market data
            volatility = self.data_engine.calculate_volatility(symbol)
            market_depth = self.data_engine.get_market_depth(symbol)
            price_change = self.data_engine.get_price_change(symbol)

            # Initialize signal components
            signal = {
                'symbol': symbol,
                'timestamp': df.index[-1],
                'price': df['close'].iloc[-1],
                'action': 'HOLD',
                'strength': 0,
                'indicators': {}
            }

            # Store indicator values
            signal['indicators'] = {
                'macd': df['macd'].iloc[-1],
                'rsi': df['rsi'].iloc[-1],
                'bb_upper': df['bb_upper'].iloc[-1],
                'bb_lower': df['bb_lower'].iloc[-1],
                'volume_ratio': df['volume'].iloc[-1] / df['volume_sma'].iloc[-1],
                'trend': 'UP' if df['close'].iloc[-1] > df['ema_200'].iloc[-1] else 'DOWN',
                'volatility': volatility,
                'market_depth_ratio': market_depth['ratio'] if market_depth else None,
                'price_change': price_change
            }

            # Generate trading signal
            signal_strength = 0
            reasons = []

            # 1. Trend Analysis
            if df['close'].iloc[-1] > df['ema_200'].iloc[-1]:
                signal_strength += 1
                reasons.append("Price above EMA200")

            # 2. MACD Analysis
            if df['macd'].iloc[-1] > 0 and df['macd'].iloc[-2] <= 0:
                signal_strength += 2
                reasons.append("MACD bullish crossover")
            elif df['macd'].iloc[-1] < 0 and df['macd'].iloc[-2] >= 0:
                signal_strength -= 2
                reasons.append("MACD bearish crossover")

            # 3. RSI Analysis
            if df['rsi'].iloc[-1] < RSI_OVERSOLD:
                signal_strength += 1
                reasons.append("RSI oversold")
            elif df['rsi'].iloc[-1] > RSI_OVERBOUGHT:
                signal_strength -= 1
                reasons.append("RSI overbought")

            # 4. Volume Analysis
            if signal['indicators']['volume_ratio'] > STRATEGY_PARAMS['volume_threshold']:
                signal_strength = signal_strength * 1.5
                reasons.append("High volume")

            # 5. Volatility Check
            if volatility:
                if STRATEGY_PARAMS['min_volatility'] <= volatility <= STRATEGY_PARAMS['max_volatility']:
                    signal_strength = signal_strength * 1.2
                    reasons.append("Optimal volatility")
                elif volatility > STRATEGY_PARAMS['max_volatility']:
                    signal_strength = signal_strength * 0.5
                    reasons.append("High volatility - reduced signal")

            # 6. Market Depth Analysis
            if market_depth and market_depth['ratio']:
                if market_depth['ratio'] > 1.2:
                    signal_strength += 1
                    reasons.append("Strong buy pressure")
                elif market_depth['ratio'] < 0.8:
                    signal_strength -= 1
                    reasons.append("Strong sell pressure")

            # Determine final signal
            if signal_strength >= 3:
                signal['action'] = 'BUY'
            elif signal_strength <= -3:
                signal['action'] = 'SELL'

            signal['strength'] = signal_strength
            signal['reasons'] = reasons

            return signal

        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {str(e)}")
            return None

    def get_signals_all_pairs(self, timeframe='15m'):
        """Generate signals for all configured trading pairs."""
        signals = {}
        for pair in self.data_engine.exchange.markets:
            if pair in self.data_engine.exchange.markets and '/USDT' in pair:
                signal = self.generate_signal(pair, timeframe)
                if signal:
                    signals[pair] = signal
        return signals
