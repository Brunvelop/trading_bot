from enum import Enum, auto
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


import numpy as np
import pandas as pd
import pandera as pa
from pandera.typing import Series

class Action(Enum):
    BUY_MARKET = "buy_market"
    SELL_MARKET = "sell_market"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    WAIT = "wait"

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

class Backtest(pa.DataFrameModel):
    date: Series[pd.Timestamp]
    open: Series[float]
    high: Series[float]
    low: Series[float]
    close: Series[float]
    volume: Series[float]
    timestamp: Series[pd.Timestamp]
    pair: Series[str]
    type: Series[str]
    price: Series[float]
    amount: Series[float]
    fee: Series[float]
    total_value: Series[float]
    balance_a: Series[float]
    balance_b: Series[float]
    hold_value: Series[float]
    total_value_a: Series[float]
    total_value_b: Series[float]
    adjusted_a_balance: Series[float]
    adjusted_b_balance: Series[float]

class StrategyExecResultFunctions:
    @staticmethod
    def calculate_metrics(marketdata: MarketData, memory: Memory, initial_balance_a: float, initial_balance_b: float) -> Backtest:
        memory_df = pd.DataFrame.from_records([vars(order) for order in memory.orders])
        df = pd.merge(marketdata, memory_df, left_on='date', right_on='timestamp', how='left')

        df.loc[0, 'balance_a'] = initial_balance_a
        df.loc[0, 'balance_b'] = initial_balance_b

        df = StrategyExecResultFunctions._fill_nan_with_bfill_ffill(df, 'balance_a')
        df = StrategyExecResultFunctions._fill_nan_with_bfill_ffill(df, 'balance_b')
        df['hold_value'] = df['balance_a'] * df['close']
        df['total_value_a'] = df['balance_a'] + df['balance_b'] / df['close']
        df['total_value_b'] = df['balance_b'] + df['hold_value']
        df['adjusted_a_balance'] = df['balance_a'] - (df['balance_b'].iloc[0] - df['balance_b']) / df['close']
        df['adjusted_b_balance'] = df['balance_b'] - (df['balance_a'].iloc[0] - df['balance_a']) * df['close']

        return df

    @staticmethod
    def _fill_nan_with_bfill_ffill(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        # Fill NaN values forward
        df[column_name] = df[column_name].ffill()
        # Fill remaining NaN values (at the beginning) with the first non-NaN value
        first_valid_index = df[column_name].first_valid_index()
        if first_valid_index is not None:
            df[column_name] = df[column_name].fillna(df[column_name].iloc[first_valid_index])

        return df

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
