"""
Technical indicators module for trading strategies.

This module provides a collection of technical indicators commonly used in trading strategies.
Each indicator is implemented as a static method in the Indicators class, returning standardized
Indicator objects that can be used by strategies to make trading decisions.

The module supports two main categories of indicators:
1. Price indicators: Based on price data (e.g., moving averages, Bollinger Bands)
2. Extra indicators: Additional metrics (e.g., RSI, volume, momentum)
"""

from typing import Type, Union, List, Optional
from enum import Enum, auto

import pandas as pd
import numpy as np
from pydantic import BaseModel

from definitions import MarketData


class IndicatorTypes:
    """
    Container class for indicator type enumerations.
    
    This class organizes indicators into logical categories to facilitate
    their use in visualization and strategy implementation.
    """
    
    class Price(Enum):
        """Price-based indicator types."""
        SIMPLE_MOVING_AVERAGE = auto()
        BOLLINGER_BANDS = auto()
        MACD = auto()
    
    class Extra(Enum):
        """Additional indicator types not directly based on price."""
        VELOCITY = auto()
        ACCELERATION = auto()
        RELATIVE_STRENGTH_INDEX = auto()
        VOLUME_SMA = auto()


class Indicator(BaseModel):
    """
    Standard container for indicator data.
    
    This class provides a consistent interface for all indicators,
    making them easier to use in strategies and visualization.
    
    Attributes:
        name: Unique identifier for the indicator
        type: Category and type of the indicator
        result: Series containing the calculated indicator values
    """
    name: str
    type: Union[IndicatorTypes.Price, IndicatorTypes.Extra]
    result: pd.Series

    class Config:
        arbitrary_types_allowed = True


class Indicators:
    """
    Collection of technical indicators for trading strategies.
    
    This class provides static methods for calculating various technical indicators
    used in trading strategies. Each method returns one or more Indicator objects
    that can be used by strategies to make trading decisions.
    """
    
    @staticmethod
    def calculate_moving_average(
        data: Type[MarketData], 
        window: int
    ) -> Indicator:
        """
        Calculate Simple Moving Average (SMA) for the closing price.
        
        Args:
            data: Market data containing OHLCV information
            window: Number of periods to include in the moving average
            
        Returns:
            Indicator object containing the calculated SMA
            
        Example:
            >>> sma = Indicators.calculate_moving_average(market_data, 20)
            >>> print(f"Latest SMA value: {sma.result.iloc[-1]}")
        """
        return Indicator(
            name=f'ma_{window}',
            type=IndicatorTypes.Price.SIMPLE_MOVING_AVERAGE,
            result=data['close'].rolling(window=window).mean()
        )
    
    @staticmethod
    def calculate_bollinger_bands(
        data: Type[MarketData], 
        window: int = 20, 
        num_std: float = 2.0
    ) -> List[Indicator]:
        """
        Calculate Bollinger Bands for the closing price.
        
        Bollinger Bands consist of:
        - Middle band: SMA of the closing price
        - Upper band: Middle band + (standard deviation * num_std)
        - Lower band: Middle band - (standard deviation * num_std)
        
        Args:
            data: Market data containing OHLCV information
            window: Number of periods to include in the calculation
            num_std: Number of standard deviations for the upper and lower bands
            
        Returns:
            List of three Indicator objects containing the middle, upper, and lower bands
            
        Example:
            >>> bands = Indicators.calculate_bollinger_bands(market_data, 20, 2.0)
            >>> middle, upper, lower = bands
            >>> print(f"Latest values - Middle: {middle.result.iloc[-1]}, "
                      f"Upper: {upper.result.iloc[-1]}, Lower: {lower.result.iloc[-1]}")
        """
        sma = data['close'].rolling(window=window).mean()
        std = data['close'].rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return [
            Indicator(
                name=f'bb_middle_{window}',
                type=IndicatorTypes.Price.BOLLINGER_BANDS,
                result=sma
            ),
            Indicator(
                name=f'bb_upper_{window}',
                type=IndicatorTypes.Price.BOLLINGER_BANDS,
                result=upper_band
            ),
            Indicator(
                name=f'bb_lower_{window}',
                type=IndicatorTypes.Price.BOLLINGER_BANDS,
                result=lower_band
            )
        ]
    
    @staticmethod
    def calculate_macd(
        data: Type[MarketData], 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> List[Indicator]:
        """
        Calculate Moving Average Convergence Divergence (MACD).
        
        MACD consists of:
        - MACD line: Difference between fast and slow EMAs
        - Signal line: EMA of the MACD line
        - Histogram: Difference between MACD line and signal line
        
        Args:
            data: Market data containing OHLCV information
            fast_period: Number of periods for the fast EMA
            slow_period: Number of periods for the slow EMA
            signal_period: Number of periods for the signal line EMA
            
        Returns:
            List of three Indicator objects containing the MACD line, signal line, and histogram
            
        Example:
            >>> macd_indicators = Indicators.calculate_macd(market_data)
            >>> macd_line, signal_line, histogram = macd_indicators
            >>> # Check for MACD crossover (bullish signal)
            >>> if (macd_line.result.iloc[-2] < signal_line.result.iloc[-2] and
            ...     macd_line.result.iloc[-1] > signal_line.result.iloc[-1]):
            ...     print("Bullish MACD crossover detected")
        """
        exp1 = data['close'].ewm(span=fast_period, adjust=False).mean()
        exp2 = data['close'].ewm(span=slow_period, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        return [
            Indicator(
                name=f'macd_{fast_period}_{slow_period}',
                type=IndicatorTypes.Price.MACD,
                result=macd
            ),
            Indicator(
                name=f'macd_signal_{signal_period}',
                type=IndicatorTypes.Price.MACD,
                result=signal
            ),
            Indicator(
                name=f'macd_hist',
                type=IndicatorTypes.Price.MACD,
                result=histogram
            )
        ]
    
    @staticmethod
    def calculate_rsi(
        data: Type[MarketData], 
        window: int = 14
    ) -> Indicator:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI measures the magnitude of recent price changes to evaluate
        overbought or oversold conditions. It oscillates between 0 and 100.
        
        Args:
            data: Market data containing OHLCV information
            window: Number of periods to include in the calculation
            
        Returns:
            Indicator object containing the calculated RSI
            
        Example:
            >>> rsi = Indicators.calculate_rsi(market_data)
            >>> latest_rsi = rsi.result.iloc[-1]
            >>> if latest_rsi < 30:
            ...     print("Oversold condition detected")
            >>> elif latest_rsi > 70:
            ...     print("Overbought condition detected")
        """
        delta = data['close'].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        return Indicator(
            name=f'rsi_{window}',
            type=IndicatorTypes.Extra.RELATIVE_STRENGTH_INDEX,
            result=rsi
        )
    
    @staticmethod
    def calculate_volume_sma(
        data: Type[MarketData], 
        window: int = 20
    ) -> Indicator:
        """
        Calculate Simple Moving Average (SMA) for volume.
        
        This indicator can be used to identify volume trends and confirm price movements.
        
        Args:
            data: Market data containing OHLCV information
            window: Number of periods to include in the moving average
            
        Returns:
            Indicator object containing the calculated volume SMA
            
        Example:
            >>> vol_sma = Indicators.calculate_volume_sma(market_data)
            >>> # Check if current volume is above average (potentially significant move)
            >>> if data['volume'].iloc[-1] > vol_sma.result.iloc[-1] * 1.5:
            ...     print("Volume spike detected - 50% above average")
        """
        return Indicator(
            name=f'volume_sma_{window}',
            type=IndicatorTypes.Extra.VOLUME_SMA,
            result=data['volume'].rolling(window=window).mean()
        )

    @staticmethod
    def calculate_velocity(
        series: pd.Series, 
        window: int
    ) -> Indicator:
        """
        Calculate the velocity (rate of change) of a series.
        
        Velocity measures how quickly a value is changing over time.
        It can be applied to price or any other indicator.
        
        Args:
            series: Data series to calculate velocity for
            window: Number of periods to include in the moving average
            
        Returns:
            Indicator object containing the calculated velocity
            
        Example:
            >>> price_velocity = Indicators.calculate_velocity(market_data['close'], 5)
            >>> # Check if price velocity is increasing (momentum building)
            >>> if price_velocity.result.iloc[-1] > price_velocity.result.iloc[-2]:
            ...     print("Price momentum is increasing")
        """
        return Indicator(
            name=f'velocity_{window}',
            type=IndicatorTypes.Extra.VELOCITY,
            result=series.diff(periods=1).rolling(window=window).mean()
        )

    @staticmethod
    def calculate_acceleration(
        velocity: pd.Series, 
        window: int
    ) -> Indicator:
        """
        Calculate the acceleration (rate of change of velocity) of a series.
        
        Acceleration measures how quickly the velocity is changing over time.
        It can help identify when a trend is strengthening or weakening.
        
        Args:
            velocity: Velocity series to calculate acceleration for
            window: Number of periods to include in the moving average
            
        Returns:
            Indicator object containing the calculated acceleration
            
        Example:
            >>> price_velocity = Indicators.calculate_velocity(market_data['close'], 5)
            >>> price_accel = Indicators.calculate_acceleration(price_velocity.result, 5)
            >>> # Check if price acceleration is positive (trend strengthening)
            >>> if price_accel.result.iloc[-1] > 0:
            ...     print("Price trend is accelerating")
        """
        return Indicator(
            name=f'acceleration_{window}',
            type=IndicatorTypes.Extra.ACCELERATION,
            result=velocity.diff(periods=1).rolling(window=window).mean()
        )
    
    @staticmethod
    def calculate_exponential_moving_average(
        data: Type[MarketData], 
        window: int
    ) -> Indicator:
        """
        Calculate Exponential Moving Average (EMA) for the closing price.
        
        EMA gives more weight to recent prices, making it more responsive to new information
        than a simple moving average.
        
        Args:
            data: Market data containing OHLCV information
            window: Number of periods to include in the moving average
            
        Returns:
            Indicator object containing the calculated EMA
            
        Example:
            >>> ema = Indicators.calculate_exponential_moving_average(market_data, 20)
            >>> print(f"Latest EMA value: {ema.result.iloc[-1]}")
        """
        return Indicator(
            name=f'ema_{window}',
            type=IndicatorTypes.Price.SIMPLE_MOVING_AVERAGE,  # Using same type as SMA for simplicity
            result=data['close'].ewm(span=window, adjust=False).mean()
        )
    
    @staticmethod
    def calculate_atr(
        data: Type[MarketData], 
        window: int = 14
    ) -> Indicator:
        """
        Calculate Average True Range (ATR).
        
        ATR measures market volatility by decomposing the entire range of an asset price
        for that period.
        
        Args:
            data: Market data containing OHLCV information
            window: Number of periods to include in the calculation
            
        Returns:
            Indicator object containing the calculated ATR
            
        Example:
            >>> atr = Indicators.calculate_atr(market_data)
            >>> # Use ATR to set stop loss (e.g., 2 ATR below entry price)
            >>> entry_price = 100
            >>> stop_loss = entry_price - (2 * atr.result.iloc[-1])
            >>> print(f"Stop loss price: {stop_loss}")
        """
        high = data['high']
        low = data['low']
        close = data['close']
        
        # Calculate true range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        return Indicator(
            name=f'atr_{window}',
            type=IndicatorTypes.Extra.VOLUME_SMA,  # Reusing existing type
            result=atr
        )
