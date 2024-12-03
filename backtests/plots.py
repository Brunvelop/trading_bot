import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.experiments_manager import ExperimentManager

if __name__ == "__main__":

    experiment_manager = ExperimentManager()
    experiment_manager.load_experiments('backtests/results/experiment_results.json')

    metrics_to_plot = [
        # 'total_value_b (Absolute Change)',
        'total_value_b (Percentage Change)',
        # 'adjusted_b_balance (Percentage Change)',
        # 'adjusted_b_balance (Absolute Change)',
    ]
    
    experiment_manager.plot_experiment_comparison(metrics_to_plot)