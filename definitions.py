from enum import Enum, auto
from datetime import datetime
from typing import List, Literal

import numpy as np
import pandas as pd
import pandera as pa
from pydantic import BaseModel, Field, field_validator

class Order(BaseModel):
    timestamp: datetime = Field(description="Timestamp as datetime object")
    pair: str
    type: Literal['buy_market', 'sell_market', 'wait']
    price: np.float64 = Field(ge=0)
    amount: np.float64 = Field(ge=0)
    fee: np.float64 = Field(ge=0)
    total_value: np.float64 = Field(ge=0)
    balance_a: np.float64 = Field(ge=0)
    balance_b: np.float64 = Field(ge=0)

    class Config:
        arbitrary_types_allowed = True

class Memory(BaseModel):
    orders: List[Order]
    balance_a: np.float64 = Field(ge=0, description="Balance first coin in pair (btc if btc/usdt)")
    balance_b: np.float64 = Field(ge=0, description="Balance second coin in pair (usdt if btc/usdt)")
    
    @field_validator('balance_a', 'balance_b')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v
    
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
   
class MarketData(pa.DataFrameModel):
    date: pa.typing.Series[pd.Timestamp] = pa.Field() #datetime64[ns]
    open: pa.typing.Series[np.float64] = pa.Field(gt=0)
    high: pa.typing.Series[np.float64] = pa.Field(gt=0)
    low: pa.typing.Series[np.float64] = pa.Field(gt=0)
    close: pa.typing.Series[np.float64] = pa.Field(gt=0)
    volume: pa.typing.Series[np.float64] = pa.Field(ge=0)

class PlotMode(Enum):
    # Lowercase names match Backtest column names
    PRICE = 'price'
    BALANCE_A = 'balance_a'
    BALANCE_B = 'balance_b'
    HOLD_VALUE = 'hold_value'
    TOTAL_VALUE_A = 'total_value_a'
    TOTAL_VALUE_B = 'total_value_b'
    ADJUSTED_A_BALANCE = 'adjusted_a_balance'
    ADJUSTED_B_BALANCE = 'adjusted_b_balance'

class TradingPhase(Enum):
    ACCUMULATION = auto()
    DISTRIBUTION = auto()
    NEUTRAL = auto()
