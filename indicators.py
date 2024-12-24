from typing import Type, Union, List
from enum import Enum, auto

import pandas as pd
from pydantic import BaseModel

from definitions import MarketData

class IndicatorTypes():
    class Price(Enum):
        SIMPLE_MOVING_AVERAGE = auto()
        BOLLINGER_BANDS = auto()
        MACD = auto()
    
    class Extra(Enum):
        VELOCITY = auto()
        ACCELERATION = auto()
        RELATIVE_STRENGTH_INDEX = auto()
        VOLUME_SMA = auto()

class Indicator(BaseModel):
    name: str
    type: Union[IndicatorTypes.Price, IndicatorTypes.Extra]
    result: pd.Series

    class Config:
        arbitrary_types_allowed = True

class Indicators:
    @staticmethod
    def calculate_bollinger_bands(data: Type[MarketData], window: int = 20, num_std: float = 2.0) -> List[Indicator]:
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
    def calculate_macd(data: Type[MarketData], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> List[Indicator]:
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
    def calculate_volume_sma(data: Type[MarketData], window: int = 20) -> Indicator:
        return Indicator(
            name=f'volume_sma_{window}',
            type=IndicatorTypes.Extra.VOLUME_SMA,
            result=data['volume'].rolling(window=window).mean()
        )

    @staticmethod
    def calculate_moving_average(data: Type[MarketData], window: int) -> Indicator:
        return Indicator(
            name=f'ma_{window}',
            type=IndicatorTypes.Price.SIMPLE_MOVING_AVERAGE,
            result=data['close'].rolling(window=window).mean()
        )
    
    @staticmethod
    def calculate_rsi(data: Type[MarketData], window: int = 14) -> Indicator:
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return Indicator(
            name=f'rsi_{window}',
            type=IndicatorTypes.Extra.RELATIVE_STRENGTH_INDEX,
            result=rsi
        )

    @staticmethod
    def calculate_velocity(series: pd.Series, window: int) -> Indicator:
        return Indicator(
            name=f'velocity_{window}',
            type=IndicatorTypes.Extra.VELOCITY,
            result=series.diff(periods=1).rolling(window=window).mean()
        )

    @staticmethod
    def calculate_acceleration(velocity: pd.Series, window: int) -> Indicator:
        return Indicator(
            name=f'acceleration_{window}',
            type=IndicatorTypes.Extra.ACCELERATION,
            result=velocity.diff(periods=1).rolling(window=window).mean()
        )
