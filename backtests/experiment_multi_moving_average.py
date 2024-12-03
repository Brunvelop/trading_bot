import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tqdm import tqdm
from pathlib import Path

from definitions import PlotMode
from backtesting.backtester import Backtester
from backtesting.experiments_manager import ExperimentManager
from strategies.multi_moving_average_strategy import MultiMovingAverageStrategy, TradingPhase

if __name__ == "__main__":
    backtester_static_config = {
        'initial_balance_a': 0000.0,
        'initial_balance_b': 5000.0,
        'fee': 0.001,
        'verbose': False
    }
    data_config={
        'data_path': Path('E:/binance_prices_processed'),
        'duration': 4320,
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
    num_tests_per_strategy = 10
    VARIATIONS = [-0.25, 0, 0.25]
    strategy_config={
            'max_duration': 400,
            'min_purchase': 5.1,
            'safety_margin': 1,
            'trading_phase': TradingPhase.ACCUMULATION,
            'debug': False
        }

    experiment_manager = ExperimentManager()
    for variation in tqdm(VARIATIONS,desc='Testing variations', leave=False):
        experiment_manager.run_experiment(
            strategy=MultiMovingAverageStrategy,
            strategy_config=strategy_config,
            backtester_config=backtester_static_config,
            data_config={**data_config, 'variation': variation},
            num_tests_per_strategy=num_tests_per_strategy,
            metrics=metrics
        )
    
    experiment_manager.save_experiments('experiment_results.json')