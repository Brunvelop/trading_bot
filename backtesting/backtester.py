import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import pandas as pd
import numpy as np
from tqdm import tqdm
from typing import List
from pathlib import Path

from data_manager import DataManager
from strategies import Strategy, MultiMovingAverageStrategy
from definitions import Memory, MarketData, Action, StrategyExecResult, PlotMode
from plots_utils import draw_graphs, calculate_moving_averages_extra_plot

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
        self.fee = fee
        self.memory: Memory = {'orders': [], 'balance_a': initial_balance_a, 'balance_b': initial_balance_b}
        self.data = None
        self.data_metadata = None
        self.result: pd.DataFrame = None
        self.verbose = verbose

    def run_backtest(
            self,
            data_config: dict = {
                'data_path': Path('data/coinex_prices_raw'),
                'duration': 4320,
                'variation': 0,
                'tolerance': 0.01,
                'normalize': True
            },
    ) -> StrategyExecResult:
        self.data, self.data_metadata = DataManager.get_data_sample(**data_config)
        self._simulate_real_time_execution()
        self.result = self._calculate_metrics()
        return self.result
    
    def plot_results(
            self, 
            plot_config: dict = {
                'plot_modes': list(PlotMode),
                'save_path': None,
                'show': False
            }
        ):
        extra_plots_price = None
        if isinstance(self.strategy, MultiMovingAverageStrategy):
            extra_plots_price = calculate_moving_averages_extra_plot(self.data)
        draw_graphs(
            df=self.result,  
            extra_plots_price=extra_plots_price,
            **plot_config
        )

    def _execute_strategy(self, data: MarketData):
        actions = self.strategy.run(data, self.memory)
        
        for action_type, price, amount in actions:
            if action_type is not None and price is not None:
                total_value = price * amount
                fee = amount * self.fee if action_type == Action.BUY_MARKET else total_value * self.fee if action_type == Action.SELL_MARKET else 0
                timestamp = data['Date'].iloc[-1]
                pair = 'DOG/USDT'  

                if action_type == Action.BUY_MARKET:
                    self.memory['balance_a'] += amount * (1-self.fee)
                    self.memory['balance_b'] -= total_value
                elif action_type == Action.SELL_MARKET:
                    self.memory['balance_a'] -= amount
                    self.memory['balance_b'] += total_value * (1-self.fee)

                self.memory.get('orders').append({
                    'timestamp': timestamp,
                    'pair': pair,
                    'type': action_type.value,
                    'price': price,
                    'amount': amount,
                    'fee': fee,
                    'total_value': total_value,
                    'balance_a': self.memory['balance_a'],
                    'balance_b': self.memory['balance_b']
                })
    
    def _simulate_real_time_execution(self, window_size: int = 200) -> List[Action]:
        iterator = tqdm(range(window_size, len(self.data))) if self.verbose else range(window_size, len(self.data))
        for i in iterator:
            window_data = self.data.iloc[i-window_size+1:i+1]
            self._execute_strategy(window_data)
        return self.memory
    
    def _calculate_metrics(self) -> StrategyExecResult:
        memory_df = pd.DataFrame(self.memory.get('orders'))
        df = pd.merge(self.data, memory_df, left_on='Date', right_on='timestamp', how='left')

        df = self._fill_nan_with_bfill_ffill(df, 'balance_a')
        df = self._fill_nan_with_bfill_ffill(df, 'balance_b')
        df['hold_value'] = df['balance_a'] * df['Close']
        df['total_value_a'] = df['balance_a'] + df['balance_b'] / df['Close'] 
        df['total_value_b'] = df['balance_b'] + df['hold_value']
        df['adjusted_a_balance'] = df['balance_a'] - (df['balance_b'].iloc[0] - df['balance_b']) / df['Close']
        df['adjusted_b_balance'] = df['balance_b'] - (df['balance_a'].iloc[0] - df['balance_a']) * df['Close']

        return df
    
    def _fill_nan_with_bfill_ffill(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        # Fill NaN values forward
        df[column_name] = df[column_name].ffill()
        # Fill remaining NaN values (at the beginning) with the first non-NaN value
        first_valid_index = df[column_name].first_valid_index()
        if first_valid_index is not None:
            df[column_name] = df[column_name].fillna(df[column_name].iloc[first_valid_index])

        return df
    
if __name__ == "__main__":
    import strategies
    from definitions import TradingPhase

    backtester = Backtester(
        strategy=strategies.MultiMovingAverageStrategy(
            max_duration = 200,
            min_purchase = 5.1,
            safety_margin = 1,
            trading_phase = TradingPhase.DISTRIBUTION,
            debug = False
        ),
        initial_balance_a=5000.0,
        initial_balance_b=0000.0,
        fee=0.001,
        verbose=True
    )
    df: StrategyExecResult = backtester.run_backtest(
        data_config={
            'data_path': Path('data/coinex_prices_raw'),
            'duration': 4320,
            'variation': 0.05,
            'tolerance': 0.01,
            'normalize': True
        }
    )
    backtester.plot_results(
        plot_config={
            'plot_modes': list(PlotMode),
            'save_path': None,  # Path('data/prueba.png'),
            'show': True
        }
    )