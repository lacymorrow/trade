import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
import ta

logger = logging.getLogger(__name__)

class SignalEngine:
    def __init__(self, data_engine):
        self.data_engine = data_engine

    def generate_signals(self, price_data: pd.DataFrame, social_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Generate trading signals based on price and social data."""
        try:
            if price_data is None or price_data.empty:
                return pd.DataFrame()

            signals = pd.DataFrame(index=price_data.index)
            signals['signal_strength'] = 0.0

            # Technical Analysis Signals
            self._add_trend_signals(price_data, signals)
            self._add_momentum_signals(price_data, signals)
            self._add_volatility_signals(price_data, signals)
            self._add_volume_signals(price_data, signals)

            # Add social signals if available
            if social_data is not None and not social_data.empty:
                self._add_social_signals(social_data, signals)

            # Normalize signals
            signals = self.normalize_signals(signals)

            # Forward fill any NaN values
            signals = signals.fillna(method='ffill').fillna(0)

            return signals

        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return pd.DataFrame(index=price_data.index, columns=['signal_strength'], data=0)

    def _add_trend_signals(self, price_data: pd.DataFrame, signals: pd.DataFrame):
        """Add trend-based signals."""
        try:
            close_series = price_data['Close'].squeeze()

            # MACD
            macd = ta.trend.MACD(close_series)
            signals['macd'] = macd.macd_diff()

            # EMA Crossovers
            ema_short = ta.trend.EMAIndicator(close_series, window=20).ema_indicator()
            ema_long = ta.trend.EMAIndicator(close_series, window=50).ema_indicator()
            signals['ema_cross'] = np.where(ema_short > ema_long, 1, -1)

            # ADX for trend strength
            adx = ta.trend.ADXIndicator(
                price_data['High'].squeeze(),
                price_data['Low'].squeeze(),
                close_series
            )
            signals['adx'] = adx.adx()

            # Weight and combine trend signals
            signals['trend_signal'] = (
                0.4 * np.sign(signals['macd']) +
                0.4 * signals['ema_cross'] +
                0.2 * (signals['adx'] / 100.0)  # Normalize ADX
            )

            signals['signal_strength'] += signals['trend_signal']

        except Exception as e:
            logger.error(f"Error adding trend signals: {str(e)}")

    def _add_momentum_signals(self, price_data: pd.DataFrame, signals: pd.DataFrame):
        """Add momentum-based signals."""
        try:
            close_series = price_data['Close'].squeeze()

            # RSI
            rsi = ta.momentum.RSIIndicator(close_series).rsi()
            signals['rsi_signal'] = np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0))

            # Stochastic Oscillator
            stoch = ta.momentum.StochasticOscillator(
                price_data['High'].squeeze(),
                price_data['Low'].squeeze(),
                close_series
            )
            signals['stoch_signal'] = np.where(stoch.stoch() < 20, 1, np.where(stoch.stoch() > 80, -1, 0))

            # CCI (Commodity Channel Index)
            cci = ta.trend.CCIIndicator(
                price_data['High'].squeeze(),
                price_data['Low'].squeeze(),
                close_series
            ).cci()
            signals['cci_signal'] = np.where(cci < -100, 1, np.where(cci > 100, -1, 0))

            # Weight and combine momentum signals
            signals['momentum_signal'] = (
                0.4 * signals['rsi_signal'] +
                0.3 * signals['stoch_signal'] +
                0.3 * signals['cci_signal']
            )

            signals['signal_strength'] += signals['momentum_signal']

        except Exception as e:
            logger.error(f"Error adding momentum signals: {str(e)}")

    def _add_volatility_signals(self, price_data: pd.DataFrame, signals: pd.DataFrame):
        """Add volatility-based signals."""
        try:
            close_series = price_data['Close'].squeeze()

            # Bollinger Bands
            bb = ta.volatility.BollingerBands(close_series)
            signals['bb_signal'] = np.where(
                close_series < bb.bollinger_lband(),
                1,
                np.where(close_series > bb.bollinger_hband(), -1, 0)
            )

            # ATR for volatility scaling
            atr = ta.volatility.AverageTrueRange(
                price_data['High'].squeeze(),
                price_data['Low'].squeeze(),
                close_series
            ).average_true_range()
            signals['volatility_scale'] = 1.0 / (1.0 + atr/close_series)

            # Weight and combine volatility signals
            signals['volatility_signal'] = signals['bb_signal'] * signals['volatility_scale']

            signals['signal_strength'] += signals['volatility_signal']

        except Exception as e:
            logger.error(f"Error adding volatility signals: {str(e)}")

    def _add_volume_signals(self, price_data: pd.DataFrame, signals: pd.DataFrame):
        """Add volume-based signals."""
        try:
            close_series = price_data['Close'].squeeze()
            volume_series = price_data['Volume'].squeeze()

            # OBV (On-Balance Volume)
            obv = ta.volume.OnBalanceVolumeIndicator(close_series, volume_series)
            signals['obv'] = obv.on_balance_volume()

            # Volume Price Trend
            vpt = ta.volume.VolumePriceTrendIndicator(close_series, volume_series)
            signals['vpt'] = vpt.volume_price_trend()

            # Normalize and combine volume signals
            signals['volume_signal'] = (
                0.5 * np.sign(signals['obv'].diff()) +
                0.5 * np.sign(signals['vpt'].diff())
            )

            signals['signal_strength'] += 0.5 * signals['volume_signal']  # Lower weight for volume

        except Exception as e:
            logger.error(f"Error adding volume signals: {str(e)}")

    def _add_social_signals(self, social_data: pd.DataFrame, signals: pd.DataFrame):
        """Add social sentiment-based signals."""
        try:
            # Align social data with signals
            social_data = social_data.reindex(signals.index, method='ffill')

            if 'weighted_sentiment' in social_data.columns:
                # Normalize sentiment to [-1, 1]
                sentiment = social_data['weighted_sentiment'].squeeze()
                max_sentiment = sentiment.abs().max()
                if max_sentiment > 0:
                    sentiment = sentiment / max_sentiment

                # Add sentiment signal
                signals['sentiment_signal'] = sentiment

            if 'engagement' in social_data.columns:
                # Normalize engagement to [0, 1]
                engagement = social_data['engagement'].squeeze()
                max_engagement = engagement.max()
                if max_engagement > 0:
                    engagement = engagement / max_engagement

                # Use engagement as a signal multiplier
                signals['engagement_scale'] = 1.0 + engagement

                # Apply engagement scaling to sentiment
                if 'sentiment_signal' in signals.columns:
                    signals['sentiment_signal'] *= signals['engagement_scale']

            # Add social signals to overall signal strength
            if 'sentiment_signal' in signals.columns:
                signals['signal_strength'] += 0.3 * signals['sentiment_signal']  # 30% weight for social

        except Exception as e:
            logger.error(f"Error adding social signals: {str(e)}")

    def normalize_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Normalize signal strength to [-1, 1] range."""
        try:
            max_strength = signals['signal_strength'].abs().max()
            if max_strength > 0:
                signals['signal_strength'] = signals['signal_strength'] / max_strength
            return signals
        except Exception as e:
            logger.error(f"Error normalizing signals: {str(e)}")
            return signals
