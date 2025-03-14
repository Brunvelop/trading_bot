import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import pandera as pa
from tqdm import tqdm
from typing import List
from pathlib import Path

from data_manager import DataManager
from strategies import Strategy
from definitions import Memory, MarketData, PlotMode, Order
from drawer import BacktestDrawer, IndicatorPlotManager
from strategies.strategy import Action, ActionType

class Backtest(pa.DataFrameModel):
    date: pa.typing.Series[pd.Timestamp] = pa.Field()
    open: pa.typing.Series[np.float64] = pa.Field(gt=0)
    high: pa.typing.Series[np.float64] = pa.Field(gt=0)
    low: pa.typing.Series[np.float64] = pa.Field(gt=0)
    close: pa.typing.Series[np.float64] = pa.Field(gt=0)
    volume: pa.typing.Series[np.float64] = pa.Field(ge=0)
    timestamp: pa.typing.Series[pd.Timestamp] = pa.Field()
    pair: pa.typing.Series[str] = pa.Field()
    type: pa.typing.Series[str] = pa.Field()
    price: pa.typing.Series[np.float64] = pa.Field(ge=0)
    amount: pa.typing.Series[np.float64] = pa.Field(ge=0)
    fee: pa.typing.Series[np.float64] = pa.Field(ge=0)
    total_value: pa.typing.Series[np.float64] = pa.Field(ge=0)
    balance_a: pa.typing.Series[np.float64] = pa.Field(ge=0)
    balance_b: pa.typing.Series[np.float64] = pa.Field(ge=0)
    hold_value: pa.typing.Series[np.float64] = pa.Field(ge=0)
    total_value_a: pa.typing.Series[np.float64] = pa.Field(ge=0)
    total_value_b: pa.typing.Series[np.float64] = pa.Field(ge=0)
    adjusted_a_balance: pa.typing.Series[np.float64] = pa.Field()
    adjusted_b_balance: pa.typing.Series[np.float64] = pa.Field()

class BacktestProcessor:
    @staticmethod
    def calculate_metrics(
            marketdata: MarketData, 
            memory: Memory, 
            initial_balance_a: float, 
            initial_balance_b: float
        ) -> Backtest:
        memory_df = pd.DataFrame.from_records([vars(order) for order in memory.orders])
        df = pd.merge(marketdata, memory_df, left_on='date', right_on='timestamp', how='left')
        
        df.loc[0, 'balance_a'] = initial_balance_a
        df.loc[0, 'balance_b'] = initial_balance_b
        
        df = BacktestProcessor._fill_nan_with_bfill_ffill(df, ['balance_a', 'balance_b', 'total_value'])
        
        df['hold_value'] = df['balance_a'] * df['close']
        df['total_value_a'] = df['balance_a'] + df['balance_b'] / df['close']
        df['total_value_b'] = df['balance_b'] + df['hold_value']
        df['adjusted_a_balance'] = df['balance_a'] - (df['balance_b'].iloc[0] - df['balance_b']) / df['close']
        df['adjusted_b_balance'] = df['balance_b'] - (df['balance_a'].iloc[0] - df['balance_a']) * df['close']
        
        df = BacktestProcessor._fill_nan_values(df)

        return Backtest(df)
    
    @staticmethod
    def _fill_nan_values(df: pd.DataFrame) -> pd.DataFrame:
        df['timestamp'] = df['timestamp'].fillna(df['date'])
        df['pair'] = df['pair'].fillna('A/B')
        df['type'] = df['type'].fillna('wait')
        df['price'] = df['price'].fillna(df['close'])
        df['amount'] = df['amount'].fillna(0)
        df['fee'] = df['fee'].fillna(0)
        return df

    @staticmethod
    def _fill_nan_with_bfill_ffill(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        for column in columns:
            df[column] = df[column].ffill()
            first_valid_index = df[column].first_valid_index()
            if first_valid_index is not None:
                df[column] = df[column].fillna(df[column].iloc[first_valid_index])
        return df

class Backtester:
    def __init__(
        self,
        strategy: Strategy,
        initial_balance_a: float,
        initial_balance_b: float,
        fee: float = 0.001,
        verbose: bool = False,
    ):
        self.strategy = strategy
        self.fee = np.float64(fee)
        self.initial_balance_a = initial_balance_a
        self.initial_balance_b = initial_balance_b
        self.memory = Memory(
            orders=[],
            balance_a=np.float64(initial_balance_a),
            balance_b=np.float64(initial_balance_b)
        )
        self.marketdata: MarketData = None
        self.marketdata_metadata = None
        self.result: pd.DataFrame = None
        self.verbose = verbose
        self.indicator_plot_manager = IndicatorPlotManager()

    def run_backtest(
            self,
            data_config: dict = {
                'data_path': Path('data/coinex_prices_raw'),
                'duration': 43200,
                'variation': 0,
                'tolerance': 0.01,
                'normalize': True
            },
    ) -> Backtest:
        self.marketdata, self.marketdata_metadata = DataManager.get_marketdata_sample(**data_config)
        self._simulate_real_time_execution()
        self.result = BacktestProcessor.calculate_metrics(
            marketdata=self.marketdata,
            memory=self.memory,
            initial_balance_a=self.initial_balance_a,
            initial_balance_b=self.initial_balance_b
        )
        return self.result
    
    def plot_results(
            self,
            plot_config: dict = {
                'plot_modes': list(PlotMode),
                'save_path': None,
                'show': False
            }
        ):
        indicators = self.strategy.calculate_indicators(self.marketdata)
        extra_plots_price = self.indicator_plot_manager.create_price_plots(self.marketdata, indicators)
        extra_plot = self.indicator_plot_manager.create_technical_plots(self.marketdata, indicators)
        
        BacktestDrawer.draw(
            df=self.result,
            extra_plots_price=extra_plots_price,
            extra_plot=extra_plot,
            **plot_config
        )

    def _execute_strategy(self, data: MarketData):
        actions = self.strategy.run(data, self.memory)
        
        for action in actions:
            if action.action_type is not None and action.price is not None:
                total_value = action.price * action.amount
                fee = action.amount * self.fee if action.action_type == ActionType.BUY_MARKET else total_value * self.fee if action.action_type == ActionType.SELL_MARKET else np.float64(0)
                timestamp = data['date'].iloc[-1]
                pair = 'A/B'

                if action.action_type == ActionType.BUY_MARKET:
                    self.memory.balance_a += action.amount * (1-self.fee)
                    self.memory.balance_b = np.float64(0) if abs(self.memory.balance_b - total_value) < 1e-8 else self.memory.balance_b - total_value
                elif action.action_type == ActionType.SELL_MARKET:
                    self.memory.balance_a = np.float64(0) if abs(self.memory.balance_a - action.amount) < 1e-8 else self.memory.balance_a - action.amount
                    self.memory.balance_b += total_value * (1-self.fee)

                self.memory.orders.append(
                    Order(
                        timestamp=timestamp,
                        pair=pair,
                        type=action.action_type.value,
                        price=action.price,
                        amount=action.amount,
                        fee=fee,
                        total_value=total_value,
                        balance_a=self.memory.balance_a,
                        balance_b=self.memory.balance_b
                    )
                )
    
    def _simulate_real_time_execution(self, window_size: int = 200) -> List[Action]:
        iterator = tqdm(range(window_size, len(self.marketdata))) if self.verbose else range(window_size, len(self.marketdata))
        for i in iterator:
            window_data = self.marketdata.iloc[i-window_size:i]
            self._execute_strategy(window_data)
        return self.memory
