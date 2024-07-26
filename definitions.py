from enum import Enum, auto
from typing import TypedDict, List, Any

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Series

class Action(Enum):
    BUY_MARKET = "buy_market"
    SELL_MARKET = "sell_market"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    WAIT = "wait"

class Memory(TypedDict):
    orders: List[Any]
    balance_a: float #balance firs coin in pair (btc if btc/usdt)
    balance_b: float #balance second coint in pair (usdt if btc/usdt)

class MarketData(pa.DataFrameModel): #ordenado de temporalmente (ultimo el mas actual)
    Date: Series[pd.Int64Dtype]
    Open: Series[float]
    High: Series[float]
    Low: Series[float]
    Close: Series[float]
    Volume: Series[float]

class VisualizationDataframe(pa.DataFrameModel):
    Date: Series[pd.Timestamp]
    Open: Series[float]
    High: Series[float]
    Low: Series[float]
    Close: Series[float]
    Volume: Series[float]
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
    adjusted_b_balance: Series[float]

class OscilationAnalysis(TypedDict):
    average_buy_duration: int
    longest_buy_duration: int
    total_buy_periods: int
    average_sell_duration: int
    longest_sell_duration: int
    total_sell_periods: int
    current_state: str


class PlotMode(Enum):
    # Lowercase names match VisualizationDataframe column names
    PRICE = 'price'
    BALANCE_A = 'balance_a'
    BALANCE_B = 'balance_b'
    HOLD_VALUE = 'hold_value'
    TOTAL_VALUE_A = 'total_value_a'
    TOTAL_VALUE_B = 'total_value_b'
    ADJUSTED_B_BALANCE = 'adjusted_b_balance'

class TradingPhase(Enum):
    ACCUMULATION = auto()
    DISTRIBUTION = auto()
    NEUTRAL = auto()


