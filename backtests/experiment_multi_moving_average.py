import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tqdm import tqdm
from pathlib import Path
from datetime import datetime

from definitions import PlotMode
from backtesting import ExperimentManager
from strategies.multi_moving_average_strategy import MultiMovingAverageStrategy, TradingPhase

if __name__ == "__main__":
    backtester_static_config = {
        'initial_balance_a': 0000.0,
        'initial_balance_b': 100000.0,
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
    num_tests_per_strategy = 100
    VARIATIONS = [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
    strategy_config={
            'max_duration': 341,
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
    
    # Create descriptive filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    strategy_name = MultiMovingAverageStrategy.__name__
    trading_phase = strategy_config['trading_phase'].name.lower()
    duration = data_config['duration']
    variations = f"var_{min(VARIATIONS)}_{max(VARIATIONS)}"
    tests_per_strategy = f"tests_{num_tests_per_strategy}"
    
    filename = f"{timestamp}_{strategy_name}_{trading_phase}_dur{duration}_{variations}_{tests_per_strategy}.json"
    
    # Ensure results directory exists
    results_dir = Path('backtests/results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save experiments with descriptive filename
    experiment_manager.save_experiments(results_dir / filename)
