import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt

from backtester import Backtester
from strategies import MultiMovingAverageStrategy
from definitions import PlotMode, VisualizationDataframe


def run_multicore_backtest(
        num_tests_per_strategy = 10,
        max_durations = range(5, 201, 50), 
        data_config: dict = None,
        backtester_config: dict = None,
        strategy_config: dict = None,
        metrics: list[PlotMode] = None,
        save_path: Optional[Path] = None, 
        show: bool = True
    ) -> None:

    results = []
    with ProcessPoolExecutor() as executor:
        for duration in tqdm(max_durations, desc="Processing Durations", unit="duration"):
            backtester = Backtester(
                **backtester_config,
                strategy = MultiMovingAverageStrategy(
                    max_duration=duration,
                    **strategy_config
                ),
            )
            futures = []
            for _ in range(num_tests_per_strategy):
                future = executor.submit(
                    backtester.run_backtest,
                    data_config={**data_config, 'variation': data_config.get('variation')},
                )
                futures.append(future)
        
            for future in tqdm(as_completed(futures), total=num_tests_per_strategy, desc=f"Duration {duration}"):
                visualization_df: VisualizationDataframe = future.result()
                metrics = _calculate_metrics(visualization_df, metrics)
                results.append((duration, metrics, data_config.get('variation')))

    df = _prepare_dataframe(results, num_tests_per_strategy)

    if save_path:
        # Determine the CSV file path
        if save_path.suffix.lower() == '.png':
            csv_path = save_path.with_suffix('.csv')
        else:
            csv_path = save_path / f'change_vs_duration_n{num_tests_per_strategy}_durations{max_durations.start}-{max_durations.stop}-{max_durations.step}.csv'
        
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)

    _plot_results(df, save_path, show)

def _calculate_metrics(visualization_df: VisualizationDataframe, metrics: list[PlotMode]):
    results = {}
    for metric in metrics:
        initial_value = visualization_df[metric.value].iloc[0]
        final_value = visualization_df[metric.value].iloc[-1]
        
        absolute_change = final_value - initial_value
        percentage_change = ((final_value - initial_value) / initial_value) * 100
        
        results[metric] = {
            'absolute': absolute_change,
            'percentage': percentage_change
        }
    
    return results

def _prepare_dataframe(results, num_tests_per_strategy):
    df_data = []
    for duration, metrics, price_variation in results:
        for metric, values in metrics.items():
            df_data.append({
                'Metric': metric.value,
                'Absolute Change': values['absolute'],
                'Percentage Change': values['percentage'],
                'Duration': duration,
                'Price Variation': price_variation,
                'Tests Per Strategy': num_tests_per_strategy,
            })
    
    return pd.DataFrame(df_data)

def _plot_results(df: pd.DataFrame, save_path: Optional[Path] = None, show: bool = True, plot_type: str = 'percentage'):
    metrics = df['Metric'].unique()
    num_cols = 2 if plot_type == 'both' else 1
    fig, axes = plt.subplots(len(metrics), num_cols, figsize=(10 * num_cols, 6 * len(metrics)))
    
    for i, metric in enumerate(metrics):
        metric_data = df[df['Metric'] == metric]
        
        if plot_type in ['absolute', 'both']:
            ax = axes[i, 0] if plot_type == 'both' else axes[i]
            metric_data.boxplot(column='Absolute Change', by='Duration', ax=ax)
            ax.set_title(f'{metric}\nAbsolute Change', fontsize=10)
            ax.set_xlabel('')
        
        if plot_type in ['percentage', 'both']:
            ax = axes[i, 1] if plot_type == 'both' else axes[i]
            metric_data.boxplot(column='Percentage Change', by='Duration', ax=ax)
            ax.set_title(f'{metric}\nPercentage Change', fontsize=10)
            ax.set_xlabel('')

    plt.tight_layout(h_pad=3, w_pad=3)
    fig.suptitle('Metric Changes by Duration', fontsize=16, y=1.02)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close(fig)



if __name__ == '__main__':
    from definitions import TradingPhase

    run_multicore_backtest(
        num_tests_per_strategy = 10,
        max_durations = range(5, 201, 50),
        save_path = Path('data/prueba.png'), 
        show = True,
        metrics= [
            # PlotMode.BALANCE_A,
            # PlotMode.BALANCE_B,
            # PlotMode.HOLD_VALUE,
            PlotMode.TOTAL_VALUE_A,
            PlotMode.TOTAL_VALUE_B,
            PlotMode.ADJUSTED_A_BALANCE
        ],
        data_config={
            'data_path': Path('data/coinex_prices_raw'),
            'duration': 4320,
            'variation': 0,
            'tolerance': 0.01,
            'normalize': True
        },
        backtester_config={
            'initial_balance_a': 100000,
            'initial_balance_b': 0,
            'fee': 0.001,
        },
        strategy_config={
            'min_purchase': 5.1,
            'safety_margin': 1,
            'trading_phase': TradingPhase.DISTRIBUTION,
            'debug': False
        }
    )