from typing import Type, Union
from enum import Enum, auto

import pandas as pd
from pydantic import BaseModel

from definitions import MarketData

class IndicatorTypes():
    class Price(Enum):
        SIMPLE_MOVING_AVERAGE = auto()
    
    class Extra(Enum):
        VELOCITY = auto()
        ACCELERATION = auto()
        RELATIVE_STRENGTH_INDEX = auto()

class Indicator(BaseModel):
    name: str
    type: Union[IndicatorTypes.Price, IndicatorTypes.Extra]
    result: pd.Series

    class Config:
        arbitrary_types_allowed = True

class Indicators:
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
            result=series.diff(periods=window)
        )

    @staticmethod
    def calculate_acceleration(velocity: pd.Series, window: int) -> Indicator:
        return Indicator(
            name=f'acceleration_{window}',
            type=IndicatorTypes.Extra.ACCELERATION,
            result=velocity.diff(periods=window)
        )
