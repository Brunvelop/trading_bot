import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import List
from pathlib import Path

from data_manager import DataManager
from strategies.strategy import Strategy
from definitions import (
    Memory,
    MarketData,
    Action,
    StrategyExecResult,
    PlotMode,
    StrategyExecResultFunctions,
    IndicatorTypes,
    Order
)
from drawer import BacktestDrawer

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

    def run_backtest(
            self,
            data_config: dict = {
                'data_path': Path('data/coinex_prices_raw'),
                'duration': 43200,
                'variation': 0,
                'tolerance': 0.01,
                'normalize': True
            },
    ) -> StrategyExecResult:
        self.marketdata, self.marketdata_metadata = DataManager.get_marketdata_sample(**data_config)
        self._simulate_real_time_execution()
        self.result = StrategyExecResultFunctions.calculate_metrics(
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
        BacktestDrawer.draw(
            df=self.result,
            extra_plots_price=self._calculate_extra_plot_price(self.strategy, self.marketdata),
            extra_plot=self._calculate_extra_plot(self.strategy, self.marketdata),
            **plot_config
        )

    def _execute_strategy(self, data: MarketData):
        actions = self.strategy.run(data, self.memory)
        
        for action_type, price, amount in actions:
            if action_type is not None and price is not None:
                total_value = price * amount
                fee = amount * self.fee if action_type == Action.BUY_MARKET else total_value * self.fee if action_type == Action.SELL_MARKET else 0
                timestamp = data['date'].iloc[-1]
                pair = 'A/B'

                if action_type == Action.BUY_MARKET:
                    self.memory.balance_a += amount * (1-self.fee)
                    self.memory.balance_b = np.float64(0) if abs(self.memory.balance_b - total_value) < 1e-8 else self.memory.balance_b - total_value
                elif action_type == Action.SELL_MARKET:
                    self.memory.balance_a = np.float64(0) if abs(self.memory.balance_a - amount) < 1e-8 else self.memory.balance_a - amount
                    self.memory.balance_b += total_value * (1-self.fee)

                self.memory.orders.append(
                    Order(
                        timestamp=timestamp,
                        pair=pair,
                        type=action_type.value,
                        price=price,
                        amount=amount,
                        fee=fee,
                        total_value=total_value,
                        balance_a=self.memory.balance_a,
                        balance_b=self.memory.balance_b
                    )
                )
    
    def _simulate_real_time_execution(self, window_size: int = 200) -> List[Action]:
        iterator = tqdm(range(window_size, len(self.marketdata))) if self.verbose else range(window_size, len(self.marketdata))
        for i in iterator:
            window_data = self.marketdata.iloc[i-window_size:i+1]
            self._execute_strategy(window_data)
        return self.memory
    
    def _calculate_extra_plot_price(self, strategy: Strategy, data: MarketData) -> list:
        indicators = strategy.calculate_indicators(data)
        extra_plots_price = []
        
        colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray']
        
        for i, indicator in enumerate(indicators):
            if indicator['type'] == IndicatorTypes.SIMPLE_MOVING_AVERAGE:
                color = colors[i % len(colors)]
                extra_plots_price.append(
                    ((data['date'], indicator['result']),
                    {'color': color, 'linewidth': 2, 'alpha': 0.5, 'label': indicator['name'], 'type': 'plot'})
                )
        
        return extra_plots_price if extra_plots_price else None
        
    def _calculate_extra_plot(self, strategy: Strategy, data: MarketData) -> list:
        indicators = strategy.calculate_indicators(data)
        extra_plots = []
        
        colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray']
        
        for i, indicator in enumerate(indicators):
            if indicator['type'] in [IndicatorTypes.RELATIVE_STRENGTH_INDEX, IndicatorTypes.VELOCITY, IndicatorTypes.ACCELERATION]:
                color = colors[i % len(colors)]
                extra_plots.append(
                    ((data['date'], indicator['result']),
                    {'color': color, 'linewidth': 2, 'alpha': 0.5, 'label': indicator['name'], 'type': 'plot'})
                )
        
        return extra_plots if extra_plots else None