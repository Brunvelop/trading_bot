import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path
import matplotlib.pyplot as plt

from backtesting.multi_backtest import MultiBacktest
from backtesting.backtester import Backtester

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
        
        result_df = MultiBacktest.run_multiple_backtests(
            backtester=backtester,
            num_tests_per_strategy=num_tests_per_strategy,
            data_config=data_config,
            metrics=metrics,
        )

        confidence_intervals = MultiBacktest.calculate_confidence_interval(result_df)
        prediction_intervals = MultiBacktest.calculate_prediction_interval(result_df)

        data_config_copy = data_config.copy()
        data_config_copy['data_path'] = str(data_config['data_path'])
        strategy_config_copy = strategy_config.copy()
        if strategy_config.get('trading_phase'):
            strategy_config_copy['trading_phase'] = str(strategy_config_copy['trading_phase'])
        experiment_result = ExperimentResult(
            strategy_name=strategy.__name__,
            strategy_config=strategy_config_copy,
            backtester_config=backtester_config,
            data_config=data_config_copy,
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

    def plot_experiment_comparison(self, metrics_to_plot, save_path: Optional[Path] = None, show: bool = True):
        strategies = list(set(exp.strategy_name for exp in self.experiments))
        fig, axes = plt.subplots(len(metrics_to_plot), len(strategies), 
                                figsize=(6*len(strategies), 5*len(metrics_to_plot)), 
                                squeeze=False)
        
        for col, strategy in enumerate(strategies):
            strategy_experiments = [exp for exp in self.experiments if exp.strategy_name == strategy]
            strategy_config = strategy_experiments[0].strategy_config  # Assuming all experiments for a strategy have the same config
            config_str = ', '.join(f'{k}={v}' for k, v in strategy_config.items())
            
            for row, metric in enumerate(metrics_to_plot):
                ax = axes[row, col]
                
                variations = [exp.data_config['variation'] for exp in strategy_experiments]
                ci_lower = [exp.confidence_intervals[metric][0] for exp in strategy_experiments]
                ci_upper = [exp.confidence_intervals[metric][1] for exp in strategy_experiments]
                pi_lower = [exp.prediction_intervals[metric][0] for exp in strategy_experiments]
                pi_upper = [exp.prediction_intervals[metric][1] for exp in strategy_experiments]
                
                ax.plot(variations, ci_lower, 'b-', label='Confidence Interval')
                ax.plot(variations, ci_upper, 'b-')
                ax.fill_between(variations, ci_lower, ci_upper, alpha=0.2, color='b')
                
                ax.plot(variations, pi_lower, 'r--', label='Prediction Interval')
                ax.plot(variations, pi_upper, 'r--')
                ax.fill_between(variations, pi_lower, pi_upper, alpha=0.1, color='r')
                
                # Highlight the zero level with a dotted line
                ax.axhline(y=0, color='yellow', linestyle=':', linewidth=1)
                
                ax.set_xlabel('Data Variation')
                ax.set_ylabel(metric, fontsize=5)
                ax.legend()
                
                # Customize the plot
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                
                # Only show x-label for the bottom plots
                if row != len(metrics_to_plot) - 1:
                    ax.set_xlabel('')

        # Add strategy names, configs, and metric names as overall row labels
        for row, metric in enumerate(metrics_to_plot):
            for col, strategy in enumerate(strategies):
                strategy_config = self.experiments[col].strategy_config
                config_str = '\n'.join(f'{k}={v}' for k, v in strategy_config.items())
                strategy_name = strategy.replace(' ', '\n')
                label = f"{strategy_name}\n\n{config_str}"
                fig.text(0.01 + col/len(strategies), 1 - (row + 0.5) / len(metrics_to_plot), label,
                         va='center', ha='left', fontsize=5, rotation='vertical')

        plt.tight_layout()
        fig.subplots_adjust(left=0.1, right=1, top=0.95, bottom=0.05)  # Adjusted margins
        
        if save_path:
            fig.savefig(save_path, bbox_inches='tight', dpi=300)
        if show:
            plt.show()
        else:
            plt.close(fig)


if __name__ == '__main__':
    import time
    from tqdm import tqdm

    from strategies.multi_moving_average_strategy_trend import MultiMovingAverageStrategyTrend
    from definitions import TradingPhase, PlotMode

    
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

    num_tests_per_strategy = 10
    STRATEGIES = [
        (MultiMovingAverageStrategyTrend, {
            'mode':MultiMovingAverageStrategyTrend.Mode.LONG,
            'debug':False
        }),
        # (strategies.MultiMovingAverageStrategy, {
        #     'max_duration': 400,
        #     'min_purchase': 5.1,
        #     'safety_margin': 1,
        #     'trading_phase': TradingPhase.ACCUMULATION,
        #     'debug': False
        # }),
    ]
    VARIATIONS = [-0.25, 0, 0.25]
    experiment_manager = ExperimentManager()
    start_time = time.time()
    for strategy, strategy_config in tqdm(STRATEGIES, desc=f'Testing strategies'):
        for variation in tqdm(VARIATIONS,desc='Testing variations', leave=False):
            experiment_manager.run_experiment(
                strategy=strategy,
                strategy_config=strategy_config,
                backtester_config=backtester_static_config,
                data_config={**data_config, 'variation': variation},
                num_tests_per_strategy=num_tests_per_strategy,
                metrics=metrics
            )
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time:.2f} seconds")
    print(f"Number of strategies: {len(STRATEGIES)}")
    print(f"Number of variations: {len(VARIATIONS)}")
    print(f"Tests per strategy: {num_tests_per_strategy}")
    print(f"Total number of experiments: {len(STRATEGIES)*len(VARIATIONS)*num_tests_per_strategy}")
    print("-----------------------------")

    # Save experiments
    # experiment_manager.save_experiments('experiment_results.json')

    # Load experiments
    # experiment_manager.load_experiments('experiment_results.json')

    metrics_to_plot = [
        # 'total_value_b (Absolute Change)',
        'total_value_b (Percentage Change)',
        # 'adjusted_b_balance (Percentage Change)',
        # 'adjusted_b_balance (Absolute Change)',
    ]
    
    experiment_manager.plot_experiment_comparison(metrics_to_plot)
