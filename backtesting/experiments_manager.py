import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from pathlib import Path
import matplotlib.pyplot as plt

from backtesting.backtest_analyzer import BacktestAnalyzer
from backtester import Backtester

@dataclass
class ExperimentResult:
    strategy_name: str
    strategy_config: Dict[str, Any]
    backtester_config: Dict[str, Any]
    data_config: Dict[str, Any]
    num_tests_per_strategy: int
    confidence_intervals: Dict[str, tuple]
    prediction_intervals: Dict[str, tuple]

class ExperimentManager:
    def __init__(self):
        self.experiments: List[ExperimentResult] = []

    def run_experiment(self, strategy, strategy_config, backtester_config, data_config, num_tests_per_strategy, metrics):
        backtester = Backtester(strategy=strategy(**strategy_config), **backtester_config)
        
        result_df = BacktestAnalyzer.run_multiple_backtests(
            backtester=backtester,
            num_tests_per_strategy=num_tests_per_strategy,
            data_config=data_config,
            metrics=metrics,
        )

        confidence_intervals = BacktestAnalyzer.calculate_confidence_interval(result_df)
        prediction_intervals = BacktestAnalyzer.calculate_prediction_interval(result_df)

        strategy_config['trading_phase'] = str(strategy_config['trading_phase'])
        data_config = str(data_config['data_path'])
        experiment_result = ExperimentResult(
            strategy_name=strategy.__name__,
            strategy_config=strategy_config,
            backtester_config=backtester_config,
            data_config=data_config,
            num_tests_per_strategy=num_tests_per_strategy,
            confidence_intervals=confidence_intervals,
            prediction_intervals=prediction_intervals
        )

        self.experiments.append(experiment_result)
        return experiment_result

    def save_experiments(self, file_path: str):
        with open(file_path, 'w') as f:
            json.dump([asdict(exp) for exp in self.experiments], f, indent=2)

    def load_experiments(self, file_path: str):
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.experiments = [ExperimentResult(**exp) for exp in data]

    def plot_experiment_comparison():
        pass

if __name__ == '__main__':
    import strategies
    from definitions import TradingPhase, PlotMode

    strategy_static_config = {
        'min_purchase' : 5.1,
        'safety_margin' : 1,
        'trading_phase' : TradingPhase.ACCUMULATION,
        'debug' : False
    }
    backtester_static_config = {
        'initial_balance_a': 0000.0,
        'initial_balance_b': 5000.0,
        'fee': 0.001,
        'verbose': False
    }
    data_config={
        'data_path': Path('E:/binance_prices_processed'),
        'duration': 43200,
        'variation': 0.1,
        'tolerance': 0.01,
        'normalize': True
    }
    metrics= [
        PlotMode.BALANCE_A,
        PlotMode.BALANCE_B,
        PlotMode.TOTAL_VALUE_A,
        PlotMode.TOTAL_VALUE_B,
        PlotMode.ADJUSTED_A_BALANCE,
        PlotMode.ADJUSTED_B_BALANCE,
    ]

    experiment_manager = ExperimentManager()

    for strategy in [strategies.MultiMovingAverageStrategy]:
        for trading_phase in [TradingPhase.ACCUMULATION]:
            for variation in [0.1, 0.2]:
                strategy_config = {
                    'min_purchase': 5.1,
                    'safety_margin': 1,
                    'trading_phase': trading_phase,
                    'debug': False
                }
                data_config = {
                    'data_path': Path('E:/binance_prices_processed'),
                    'duration': 43200,
                    'variation': variation,
                    'tolerance': 0.01,
                    'normalize': True
                }
                experiment_manager.run_experiment(
                    strategy=strategy,
                    strategy_config=strategy_config,
                    backtester_config=backtester_static_config,
                    data_config=data_config,
                    num_tests_per_strategy=10,
                    metrics=metrics
                )

    # Save experiments
    experiment_manager.save_experiments('experiment_results.json')

    # Load experiments
    # experiment_manager.load_experiments('experiment_results.json')
