import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import scipy.stats as stats
from typing import Optional, List
import matplotlib.pyplot as plt

from backtesting.backtester import Backtester
from definitions import PlotMode, StrategyExecResult

class MultiBacktest:
    @staticmethod
    def run_multiple_backtests(
        backtester: Backtester = None,
        num_tests_per_strategy = 10,
        data_config: dict = None,
        metrics: List[PlotMode] = None,
    ) -> pd.DataFrame:

        results = []
        failed_tests = 0
        with ProcessPoolExecutor() as executor:
            futures = []
            for i in range(num_tests_per_strategy):
                future = executor.submit(backtester.run_backtest, data_config)
                futures.append((i, future))

            for i, future in tqdm(futures, total=num_tests_per_strategy, desc=f"Running {num_tests_per_strategy} tests", leave=False):
                try:
                    df: StrategyExecResult = future.result()
                    metric_change = MultiBacktest._calculate_metric_change(df, metrics)
                    results.append((metric_change, data_config.get('variation')))
                except Exception as e:
                    failed_tests += 1
                    print(f"Error in backtest {i+1}: {str(e)}")
                    print(f"Data config: {data_config}")
                    continue

        if not results:
            raise ValueError("All backtests failed. Please check your data and strategy.")

        if failed_tests > 0:
            print(f"Warning: {failed_tests} out of {num_tests_per_strategy} backtests failed.")

        df = MultiBacktest._prepare_dataframe(results, num_tests_per_strategy, str(backtester.strategy.__module__))
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
        intervals = []
        for metric in df['Metric'].unique():
            # Calculate confidence intervals for Absolute Change
            abs_data = df.loc[df['Metric'] == metric, 'Absolute Change']
            abs_mean = abs_data.mean()
            abs_std_err = abs_data.sem()
            abs_n = len(abs_data)
            abs_lower, abs_upper = stats.t.interval(confidence, df=abs_n-1, loc=abs_mean, scale=abs_std_err)
            
            # Calculate confidence intervals for Percentage Change
            pct_data = df.loc[df['Metric'] == metric, 'Percentage Change']
            pct_mean = pct_data.mean()
            pct_std_err = pct_data.sem()
            pct_n = len(pct_data)
            pct_lower, pct_upper = stats.t.interval(confidence, df=pct_n-1, loc=pct_mean, scale=pct_std_err)
            
            intervals.append({
                'Metric': metric,
                'Absolute Lower Confidence': abs_lower,
                'Absolute Upper Confidence': abs_upper,
                'Percentage Lower Confidence': pct_lower,
                'Percentage Upper Confidence': pct_upper
            })

        intervals_df = pd.DataFrame(intervals)
        return df.merge(intervals_df, on='Metric', how='left')

    @staticmethod
    def calculate_prediction_interval(df, confidence=0.95):
        intervals = []
        for metric in df['Metric'].unique():
            # Calculate prediction intervals for Absolute Change
            abs_data = df.loc[df['Metric'] == metric, 'Absolute Change']
            abs_mean = abs_data.mean()
            abs_std = abs_data.std(ddof=1)
            abs_n = len(abs_data)
            abs_scale = abs_std * math.sqrt(1 + 1/abs_n)
            abs_lower, abs_upper = stats.t.interval(confidence, df=abs_n-1, loc=abs_mean, scale=abs_scale)
            
            # Calculate prediction intervals for Percentage Change
            pct_data = df.loc[df['Metric'] == metric, 'Percentage Change']
            pct_mean = pct_data.mean()
            pct_std = pct_data.std(ddof=1)
            pct_n = len(pct_data)
            pct_scale = pct_std * math.sqrt(1 + 1/pct_n)
            pct_lower, pct_upper = stats.t.interval(confidence, df=pct_n-1, loc=pct_mean, scale=pct_scale)
            
            intervals.append({
                'Metric': metric,
                'Absolute Lower Prediction': abs_lower,
                'Absolute Upper Prediction': abs_upper,
                'Percentage Lower Prediction': pct_lower,
                'Percentage Upper Prediction': pct_upper
            })

        intervals_df = pd.DataFrame(intervals)
        return df.merge(intervals_df, on='Metric', how='left')

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
                'percentage': ((final_value - initial_value) / initial_value) * 100 if initial_value != 0 else 0
            }
        return results

    @staticmethod
    def _prepare_dataframe(results, num_tests_per_strategy, strategy_name):
        df_data = []
        for metrics, price_variation in results:
            for metric, values in metrics.items():
                df_data.append({
                    'Metric': metric.value,
                    'Absolute Change': values['absolute'],
                    'Percentage Change': values['percentage'],
                    'Price Variation': price_variation,
                    'Tests Per Strategy': num_tests_per_strategy,
                    'Strategy': strategy_name
                })

        return pd.DataFrame(df_data)

    @staticmethod
    def plot_intervals(df: pd.DataFrame, interval_type: str, save_path: Optional[Path] = None, show: bool = True):
        # Create figure with more height and use constrained_layout
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 18), constrained_layout=True)
        
        metrics = df['Metric'].unique()
        y_pos = range(len(metrics))

        for idx, (ax, change_type) in enumerate(zip([ax1, ax2], ['Percentage', 'Absolute'])):
            # Get the appropriate column names for this change type
            lower_col = f'{change_type} Lower {interval_type}'
            upper_col = f'{change_type} Upper {interval_type}'
            
            # Get all values for setting axis limits
            all_values = df[[lower_col, upper_col]].values.flatten()
            all_values = all_values[~np.isnan(all_values) & ~np.isinf(all_values)]  # Filter out NaN and Inf values
            
            if len(all_values) == 0:
                print(f"Warning: No valid values found for {change_type} {interval_type} intervals")
                continue
                
            x_min, x_max = np.min(all_values), np.max(all_values)
            x_range = x_max - x_min

            # Plot intervals for each metric
            for i, metric in enumerate(metrics):
                metric_data = df[df['Metric'] == metric].iloc[0]
                lower, upper = metric_data[lower_col], metric_data[upper_col]
                
                # Skip if values are invalid
                if np.isnan(lower) or np.isnan(upper) or np.isinf(lower) or np.isinf(upper):
                    print(f"Warning: Invalid interval values for metric {metric} in {change_type} {interval_type}")
                    continue
                    
                mid = (lower + upper) / 2

                # Plot interval line and midpoint
                ax.plot([lower, upper], [i, i], 'bo-', linewidth=2, markersize=8)
                ax.plot(mid, i, 'ro', markersize=10)

                # Add annotations
                ax.annotate(f'{lower:.2f}', (lower, i), xytext=(-40, -5), 
                           textcoords='offset points', ha='right', va='center')
                ax.annotate(f'{upper:.2f}', (upper, i), xytext=(40, -5), 
                           textcoords='offset points', ha='left', va='center')
                ax.annotate(f'{mid:.2f}', (mid, i), xytext=(0, 15), 
                           textcoords='offset points', ha='center', va='bottom')

            # Customize the plot
            ax.set_yticks(y_pos)
            ax.set_yticklabels(metrics)
            ax.invert_yaxis()
            ax.set_title(f'{interval_type} Intervals {change_type}', pad=30)

            # Set x-axis limits with padding
            padding = x_range * 0.1
            ax.set_xlim(x_min - padding, x_max + padding)

            # Add grid and improve aesthetics
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.setp(ax.get_yticklabels(), fontsize=10)

            # Add legend
            ax.plot([], [], 'bo-', label=f'{interval_type} Interval')
            ax.plot([], [], 'ro', label='Mean')
            ax.legend(loc='best')

        if save_path:
            fig.savefig(save_path, bbox_inches='tight', dpi=300)
        if show:
            plt.show()
        else:
            plt.close(fig)
