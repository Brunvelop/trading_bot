import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from backtesting import ExperimentManager
from backtesting.multi_backtest import MultiBacktest
from definitions import PlotMode

if __name__ == "__main__":
    # Initialize experiment manager
    experiment_manager = ExperimentManager()
    
    # Load experiments from file
    # results_file = Path('backtests/results/20241212_100217_MultiMovingAverageStrategy_distribution_dur43200_var_-0.5_0.5_tests_100.json')
    results_file = Path('backtests/results/20241218_190635_MomentumRsiStrategy_distribution_dur4320_var_-0.5_0.5_tests_10.json')

    experiment_manager.load_experiments(results_file)

    # Define metrics to plot using PlotMode
    metrics = [
        # PlotMode.BALANCE_A,
        # PlotMode.BALANCE_B,
        # PlotMode.TOTAL_VALUE_A,
        PlotMode.TOTAL_VALUE_B,
        # PlotMode.ADJUSTED_A_BALANCE,
        # PlotMode.ADJUSTED_B_BALANCE,
    ]

    print(experiment_manager.get_experiment_summary())
    # Plot experiment comparison (variation vs intervals)
    experiment_manager.plot_experiment_comparison(
        metrics_to_plot=metrics,
        save_path=None,
        show=True
    )

    # For each experiment, show detailed plots using MultiBacktest functions
    # for i, experiment in enumerate(experiment_manager.experiments):
    #     print(f"\nPlots for experiment {i+1} - Strategy: {experiment.strategy_name}")
    #     print(f"Data variation: {experiment.data_config['variation']}")
        
    #     # Plot boxplots
    #     MultiBacktest.plot_results(experiment.results_df)
        
    #     # Plot confidence intervals
    #     MultiBacktest.plot_intervals(experiment.results_df, "Confidence", show=True)
        
    #     # Plot prediction intervals
    #     MultiBacktest.plot_intervals(experiment.results_df, "Prediction", show=True)
