import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from backtesting.multi_backtest import MultiBacktest
from backtesting.backtester import Backtester
from definitions import PlotMode

@dataclass
class ExperimentResult:
    strategy_name: str
    strategy_config: Dict[str, Any]
    backtester_config: Dict[str, Any]
    data_config: Dict[str, Any]
    num_tests_per_strategy: int
    results_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    failed_tests: int = 0

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        d = asdict(self)
        d['results_df'] = self.results_df.to_dict() if not self.results_df.empty else {}
        return d

    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary"""
        results_df = pd.DataFrame.from_dict(data.pop('results_df')) if data.get('results_df') else pd.DataFrame()
        return cls(**data, results_df=results_df)

class ExperimentManager:
    def __init__(self):
        self.experiments: List[ExperimentResult] = []

    def run_experiment(
        self,
        strategy,
        strategy_config: Dict[str, Any],
        backtester_config: Dict[str, Any],
        data_config: Dict[str, Any],
        num_tests_per_strategy: int,
        metrics: List[PlotMode],
        save_plots: bool = False,
        plots_dir: Optional[Path] = None
    ) -> ExperimentResult:
        """
        Run a single experiment with the given configuration
        """
        # Create backtester instance
        backtester = Backtester(strategy=strategy(**strategy_config), **backtester_config)
        
        # Run multiple backtests
        try:
            result_df = MultiBacktest.run_multiple_backtests(
                backtester=backtester,
                num_tests_per_strategy=num_tests_per_strategy,
                data_config=data_config,
                metrics=metrics,
            )

            # Calculate intervals
            result_df = MultiBacktest.calculate_confidence_interval(result_df)
            result_df = MultiBacktest.calculate_prediction_interval(result_df)

            # Save plots if requested
            if save_plots and plots_dir:
                plots_dir.mkdir(parents=True, exist_ok=True)
                experiment_name = f"{strategy.__name__}_{len(self.experiments)}"
                
                # Save boxplot
                boxplot_path = plots_dir / f"{experiment_name}_boxplot.png"
                MultiBacktest.plot_results(result_df, save_path=boxplot_path, show=False)
                
                # Save confidence intervals plot
                ci_path = plots_dir / f"{experiment_name}_confidence_intervals.png"
                MultiBacktest.plot_intervals(result_df, "Confidence", save_path=ci_path, show=False)
                
                # Save prediction intervals plot
                pi_path = plots_dir / f"{experiment_name}_prediction_intervals.png"
                MultiBacktest.plot_intervals(result_df, "Prediction", save_path=pi_path, show=False)

            # Create experiment result
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
                results_df=result_df,
                failed_tests=0  # We'll update this if we get it from MultiBacktest
            )

            self.experiments.append(experiment_result)
            return experiment_result

        except Exception as e:
            print(f"Error running experiment with strategy {strategy.__name__}: {str(e)}")
            raise

    def save_experiments(self, file_path: Union[str, Path]):
        """Save experiments to a JSON file"""
        file_path = Path(file_path)
        with open(file_path, 'w') as f:
            json.dump([exp.to_dict() for exp in self.experiments], f, indent=2)

    def save_experiment_results(
        self,
        strategy_class,
        data_config: Dict[str, Any],
        variations: List[float],
        num_tests_per_strategy: int,
        base_dir: str = 'backtests/results'
    ) -> Path:
        """
        Save experiment results and summaries in an organized directory structure.
        
        Args:
            strategy_class: The strategy class used in the experiments
            data_config: Configuration for the data used in experiments
            variations: List of variations tested
            num_tests_per_strategy: Number of tests per strategy
            base_dir: Base directory for results (default: 'backtests/results')
            
        Returns:
            Path: The experiment directory path where results were saved
        """
        # Create directory path components
        strategy_name = strategy_class.__name__
        duration = f"duration_{data_config['duration']}"
        variations_str = f"variations_{min(variations)}_{max(variations)}"
        tests = f"tests_{num_tests_per_strategy}"
        
        # Create directory structure
        results_base_dir = Path(base_dir)
        experiment_dir = results_base_dir / f"{duration}/{variations_str}/{tests}"
        summaries_dir = experiment_dir / "summaries"
        
        # Create directories
        experiment_dir.mkdir(parents=True, exist_ok=True)
        summaries_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main experiment results
        self.save_experiments(experiment_dir / f"{strategy_name}.json")
        
        # Save summary
        summary = self.get_experiment_summary()
        summary_filename = f"{strategy_name}_summary.csv"
        summary.to_csv(summaries_dir / summary_filename)
        
        return experiment_dir

    def load_experiments(self, file_path: Union[str, Path]):
        """Load experiments from a JSON file"""
        file_path = Path(file_path)
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.experiments = [ExperimentResult.from_dict(exp) for exp in data]

    def plot_experiment_comparison(
        self,
        metrics_to_plot: List[PlotMode],
        save_path: Optional[Path] = None,
        show: bool = True
    ):
        """
        Create a comprehensive comparison plot of all experiments
        """
        if not self.experiments:
            raise ValueError("No experiments to plot")

        strategies = list(set(exp.strategy_name for exp in self.experiments))
        fig, axes = plt.subplots(
            len(metrics_to_plot),
            len(strategies),
            figsize=(6*len(strategies), 5*len(metrics_to_plot)),
            squeeze=False
        )

        for col, strategy in enumerate(strategies):
            strategy_experiments = [exp for exp in self.experiments if exp.strategy_name == strategy]
            strategy_config = strategy_experiments[0].strategy_config
            
            for row, metric in enumerate(metrics_to_plot):
                ax = axes[row, col]
                
                variations = [exp.data_config['variation'] for exp in strategy_experiments]
                
                # Get confidence and prediction intervals from the new DataFrame structure
                ci_lower = []
                ci_upper = []
                pi_lower = []
                pi_upper = []
                
                for exp in strategy_experiments:
                    metric_data = exp.results_df[exp.results_df['Metric'] == metric.value]
                    if not metric_data.empty:
                        # Using Percentage Change intervals by default
                        ci_lower.append(metric_data['Percentage Lower Confidence'].iloc[0])
                        ci_upper.append(metric_data['Percentage Upper Confidence'].iloc[0])
                        pi_lower.append(metric_data['Percentage Lower Prediction'].iloc[0])
                        pi_upper.append(metric_data['Percentage Upper Prediction'].iloc[0])
                
                # Plot confidence intervals
                ax.plot(variations, ci_lower, 'b-', label='Confidence Interval')
                ax.plot(variations, ci_upper, 'b-')
                ax.fill_between(variations, ci_lower, ci_upper, alpha=0.2, color='b')
                
                # Plot prediction intervals
                ax.plot(variations, pi_lower, 'r--', label='Prediction Interval')
                ax.plot(variations, pi_upper, 'r--')
                ax.fill_between(variations, pi_lower, pi_upper, alpha=0.1, color='r')
                
                # Highlight the zero level
                ax.axhline(y=0, color='yellow', linestyle=':', linewidth=1)
                
                # Customize plot
                ax.set_xlabel('Data Variation')
                ax.set_ylabel(metric.value, fontsize=5)
                ax.legend()
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                
                # Only show x-label for the bottom plots
                if row != len(metrics_to_plot) - 1:
                    ax.set_xlabel('')

        # Add strategy names and configs as labels
        for row, metric in enumerate(metrics_to_plot):
            for col, strategy in enumerate(strategies):
                strategy_config = self.experiments[col].strategy_config
                config_str = '\n'.join(f'{k}={v}' for k, v in strategy_config.items())
                strategy_name = strategy.replace(' ', '\n')
                label = f"{strategy_name}\n\n{config_str}"
                fig.text(0.01 + col/len(strategies), 1 - (row + 0.5) / len(metrics_to_plot), label,
                        va='center', ha='left', fontsize=5, rotation='vertical')

        plt.tight_layout()
        fig.subplots_adjust(left=0.1, right=1, top=0.95, bottom=0.05)
        
        if save_path:
            fig.savefig(save_path, bbox_inches='tight', dpi=300)
        if show:
            plt.show()
        else:
            plt.close(fig)

    def get_experiment_summary(self) -> pd.DataFrame:
        """
        Generate a summary DataFrame of all experiments
        """
        summaries = []
        for exp in self.experiments:
            for metric in exp.results_df['Metric'].unique():
                metric_data = exp.results_df[exp.results_df['Metric'] == metric]
                
                summary = {
                    'Strategy': exp.strategy_name,
                    'Metric': metric,
                    'Mean Absolute Change': metric_data['Absolute Change'].mean(),
                    'Mean Percentage Change': metric_data['Percentage Change'].mean(),
                    'Failed Tests': exp.failed_tests,
                    'Total Tests': exp.num_tests_per_strategy,
                    'Success Rate': 1 - (exp.failed_tests / exp.num_tests_per_strategy)
                }
                
                # Add confidence intervals
                for interval_type in ['Confidence', 'Prediction']:
                    for change_type in ['Absolute', 'Percentage']:
                        lower_col = f'{change_type} Lower {interval_type}'
                        upper_col = f'{change_type} Upper {interval_type}'
                        if lower_col in metric_data.columns and upper_col in metric_data.columns:
                            summary[f'{change_type} {interval_type} Interval'] = \
                                f"({metric_data[lower_col].iloc[0]:.2f}, {metric_data[upper_col].iloc[0]:.2f})"
                
                summaries.append(summary)
        
        return pd.DataFrame(summaries)
