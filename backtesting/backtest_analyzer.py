import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm
from pathlib import Path
import scipy.stats as stats
from typing import Optional, List
import matplotlib.pyplot as plt

from backtester import Backtester
from definitions import PlotMode, StrategyExecResult

class BacktestAnalyzer:
    @staticmethod
    def run_multiple_backtests(
        backtester: Backtester = None,
        num_tests_per_strategy = 10,
        data_config: dict = None,
        metrics: List[PlotMode] = None,
    ) -> pd.DataFrame:

        results = []
        with ProcessPoolExecutor() as executor:
            futures = []
            for _ in range(num_tests_per_strategy):
                future = executor.submit(backtester.run_backtest, data_config)
                futures.append(future)

            for future in tqdm(as_completed(futures), total=num_tests_per_strategy, desc=f"Running {num_tests_per_strategy} tests"):
                df: StrategyExecResult = future.result()
                metric_change = BacktestAnalyzer._calculate_metric_change(df, metrics)
                results.append((metric_change, data_config.get('variation')))

        df = BacktestAnalyzer._prepare_dataframe(results, num_tests_per_strategy)
        return df
    
    @staticmethod
    def plot_results(df: pd.DataFrame, save_path: Optional[Path] = None, show: bool = True):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16))

        for ax, change_type in zip([ax1, ax2], ['Percentage Change', 'Absolute Change']):
            # Prepare data for boxplot
            metrics = df['Metric'].unique()
            data = [df[df['Metric'] == metric][change_type] for metric in metrics]

            # Create horizontal boxplot
            bp = ax.boxplot(data, vert=False, patch_artist=True, labels=metrics)

            # Customize boxplot colors
            for box in bp['boxes']:
                box.set(facecolor='lightblue', alpha=0.7)

            # Calculate the range of x values
            all_values = df[change_type].values
            x_min, x_max = min(all_values), max(all_values)
            x_range = x_max - x_min

            # Add individual points and annotations
            for i, (metric, d) in enumerate(zip(metrics, data)):
                y = [i + 1] * len(d)
                ax.scatter(d, y, color='red', alpha=0.5, s=20)

                # Add annotations for min, max, and mean
                min_val, max_val = d.min(), d.max()
                mean_val = d.mean()
                ax.annotate(f'{min_val:.2f}', (min_val, i+1), xytext=(-40, -5), textcoords='offset points', ha='right', va='center')
                ax.annotate(f'{max_val:.2f}', (max_val, i+1), xytext=(40, -5), textcoords='offset points', ha='left', va='center')
                ax.annotate(f'{mean_val:.2f}', (mean_val, i+1), xytext=(0, 15), textcoords='offset points', ha='center', va='bottom')

            # Customize the plot
            ax.set_ylabel(change_type)

            # Set x-axis limits with padding
            padding = x_range * 0.1  # 10% padding on each side
            ax.set_xlim(x_min - padding, x_max + padding)

            # Add grid for better readability
            ax.grid(True, axis='x', linestyle='--', alpha=0.7)

            # Improve aesthetics
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.setp(ax.get_yticklabels(), fontsize=10, ha="right", va="center")

            # Add legend
            ax.add_patch(plt.Rectangle((0,0), 1, 1, fc="lightblue", alpha=0.7, ec="black", label="IQR"))
            ax.plot([], [], 'k-', linewidth=2, label='Whiskers')
            ax.plot([], [], 'r-', linewidth=2, label='Median')
            ax.scatter([], [], color='red', alpha=0.5, s=20, label='Individual Points')
            ax.legend(loc='best')

        # Adjust layout
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, bbox_inches='tight', dpi=300)
        if show:
            plt.show()
        else:
            plt.close(fig)

    @staticmethod
    def calculate_confidence_interval(df, confidence=0.95):
        intervals = {}
        for metric in df['Metric'].unique():
            for change_type in ['Percentage Change', 'Absolute Change']:
                data = df.loc[df['Metric'] == metric, change_type]
                mean = data.mean()
                std_err = data.sem()
                n = len(data)

                # Calculate the confidence interval using the Student's t-distribution
                interval = stats.t.interval(confidence, df=n-1, loc=mean, scale=std_err)
                intervals[f"{metric} ({change_type})"] = interval
        return intervals

    @staticmethod
    def calculate_prediction_interval(df, confidence=0.95):
        intervals = {}
        for metric in df['Metric'].unique():
            for change_type in ['Percentage Change', 'Absolute Change']:
                data = df.loc[df['Metric'] == metric, change_type]
                mean = data.mean()
                std = data.std(ddof=1)
                n = len(data)

                # Calculate the prediction interval using the Student's t-distribution
                scale = std * math.sqrt(1 + 1/n)
                interval = stats.t.interval(confidence, df=n-1, loc=mean, scale=scale)
                intervals[f"{metric} ({change_type})"] = interval
        return intervals

    @staticmethod
    def _calculate_metric_change(
            df: StrategyExecResult,
            metrics: List[PlotMode]
        ):
        results = {}
        for metric in metrics:
            initial_value = df[metric.value].iloc[0]
            final_value = df[metric.value].iloc[-1]
            results[metric] = {
                'absolute': final_value - initial_value,
                'percentage': ((final_value - initial_value) / initial_value) * 100
            }
        return results

    @staticmethod
    def _prepare_dataframe(results, num_tests_per_strategy):
        df_data = []
        for metrics, price_variation in results:
            for metric, values in metrics.items():
                df_data.append({
                    'Metric': metric.value,
                    'Absolute Change': values['absolute'],
                    'Percentage Change': values['percentage'],
                    'Price Variation': price_variation,
                    'Tests Per Strategy': num_tests_per_strategy,
                })

        return pd.DataFrame(df_data)

    @staticmethod
    def _plot_intervals(intervals: dict, save_path: Optional[Path] = None, show: bool = True):
        # Set up the plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Prepare data for plotting
        metrics = list(intervals.keys())
        y_pos = range(len(metrics))
        
        # Calculate the range of x values
        all_values = [val for interval in intervals.values() for val in interval]
        x_min, x_max = min(all_values), max(all_values)
        x_range = x_max - x_min

        # Plot intervals
        for i, (metric, interval) in enumerate(intervals.items()):
            lower, upper = interval
            mid = (lower + upper) / 2
            ax.plot([lower, upper], [i, i], 'bo-', linewidth=2, markersize=8)
            ax.plot(mid, i, 'ro', markersize=10)

            # Add annotations for the values
            ax.annotate(f'{lower:.2f}', (lower, i), xytext=(-40, -5), textcoords='offset points', ha='right', va='center')
            ax.annotate(f'{upper:.2f}', (upper, i), xytext=(40, -5), textcoords='offset points', ha='left', va='center')
            ax.annotate(f'{mid:.2f}', (mid, i), xytext=(0, 15), textcoords='offset points', ha='center', va='bottom')

        # Customize the plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(metrics)
        ax.invert_yaxis()  # Labels read top-to-bottom
        ax.set_xlabel('Confidence Interval')
        ax.set_title('Confidence Intervals for Metrics', fontsize=16)

        # Set x-axis limits with padding
        padding = x_range * 0.1  # 10% padding on each side
        ax.set_xlim(x_min - padding, x_max + padding)

        # Add grid for better readability
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Improve aesthetics
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.setp(ax.get_yticklabels(), fontsize=10)

        # Add legend
        ax.plot([], [], 'bo-', label='Confidence Interval')
        ax.plot([], [], 'ro', label='Mean')
        ax.legend(loc='best')

        # Adjust layout
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, bbox_inches='tight', dpi=300)
        if show:
            plt.show()
        else:
            plt.close(fig)
if __name__ == '__main__':
    import strategies
    from definitions import TradingPhase

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
        'data_path': Path('data/coinex_prices_raw'),
        'duration': 1000,
        'variation': 0.0,
        'tolerance': 1,
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

    result_df = BacktestAnalyzer.run_multiple_backtests(
        backtester = Backtester(
            strategy=strategies.MultiMovingAverageStrategy(
                max_duration = 400,
                **strategy_static_config
            ),
            **backtester_static_config
        ),
        num_tests_per_strategy=50,
        data_config=data_config,
        metrics=metrics,
    )
    BacktestAnalyzer.plot_results(result_df)
    
    intervals = BacktestAnalyzer.calculate_confidence_interval(
        df=result_df,
        confidence=0.99
    )
    print(strategy_static_config['trading_phase'])
    print(f"Duracion: {data_config['duration']}")
    print(f"Variación: {data_config['variation']*100}%:")
    for metric, interval in intervals.items():
        print(f"  {metric}: [{interval[0]:.4f}, {interval[1]:.4f}] -> {abs(interval[1] - interval[0]):4f}")

    # Plot the intervals
    BacktestAnalyzer._plot_intervals(intervals, show=True)
