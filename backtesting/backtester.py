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
from definitions import Memory, MarketData, Action, StrategyExecResult, PlotMode, StrategyExecResultFunctions
from plots_utils import StrategyExecResultDrawer

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
        self.marketdata: MarketData = None
        self.marketdata_metadata = None
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
        self.marketdata, self.marketdata_metadata = DataManager.get_marketdata_sample(**data_config)
        self._simulate_real_time_execution()
        self.result = StrategyExecResultFunctions.calculate_metrics(
            marketdata=self.marketdata,
            memory=self.memory
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
        extra_plots_price = None
        if isinstance(self.strategy, MultiMovingAverageStrategy):
            extra_plots_price = StrategyExecResultDrawer.calculate_moving_averages_extra_plot(self.marketdata)
        StrategyExecResultDrawer.draw_result(
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
        iterator = tqdm(range(window_size, len(self.marketdata))) if self.verbose else range(window_size, len(self.marketdata))
        for i in iterator:
            window_data = self.marketdata.iloc[i-window_size+1:i+1]
            self._execute_strategy(window_data)
        return self.memory
    
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