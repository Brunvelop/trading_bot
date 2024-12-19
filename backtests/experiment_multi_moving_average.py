import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tqdm import tqdm
from pathlib import Path

from definitions import PlotMode
from backtesting import ExperimentManager
from strategies.multi_moving_average_strategy import MultiMovingAverageStrategy

if __name__ == "__main__":
    backtester_static_config = {
        'initial_balance_a': 0.0,
        'initial_balance_b': 100000.0,
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
    VARIATIONS = [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
    strategy_config={
            'max_duration': 341,
            'min_purchase': 5.1,
            'safety_margin': 1,
            'trading_phase': MultiMovingAverageStrategy.TradingPhase.ACCUMULATION,
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
    
    # Save experiment results
    experiment_dir = experiment_manager.save_experiment_results(
        strategy_class=MultiMovingAverageStrategy,
        data_config=data_config,
        variations=VARIATIONS,
        num_tests_per_strategy=num_tests_per_strategy
    )

    # # Save summary with only total value b
    # summary = experiment_manager.get_experiment_summary()
    # summary_filename = f"{MultiMovingAverageStrategy.__name__}_summary.csv"
    # summary.to_csv(summaries_dir / summary_filename)

    print(experiment_manager.get_experiment_summary())
    experiment_manager.plot_experiment_comparison(
        metrics_to_plot=[PlotMode.TOTAL_VALUE_B],
        save_path=None,
        show=True
    )
