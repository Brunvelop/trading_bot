from enum import Enum, auto
from typing import TypedDict, List, Literal

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

class Order(TypedDict):
    timestamp: str  # Consider using datetime if possible
    pair: str
    type: Literal['buy_market', 'sell_market']
    price: float
    amount: float
    fee: float
    total_value: float
    balance_a: float
    balance_b: float

class Memory(TypedDict):
    orders: List[Order]
    balance_a: float #balance firs coin in pair (btc if btc/usdt)
    balance_b: float #balance second coint in pair (usdt if btc/usdt)

class MarketData(pa.DataFrameModel): #ordenado de temporalmente (ultimo el mas actual)
    date: Series[pd.Int64Dtype]
    open: Series[float]
    high: Series[float]
    low: Series[float]
    close: Series[float]
    volume: Series[float]

class StrategyExecResult(pa.DataFrameModel):
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
    def calculate_metrics(marketdata: MarketData, memory: Memory) -> StrategyExecResult:
        memory_df = pd.DataFrame(memory.get('orders'))
        df = pd.merge(marketdata, memory_df, left_on='date', right_on='timestamp', how='left')

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
    # Lowercase names match StrategyExecResult column names
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


