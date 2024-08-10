import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    
if __name__ == '__main__':
    import strategies
    from definitions import TradingPhase

    strategy_static_config = {
        'min_purchase' : 5.1,
        'safety_margin' : 1,
        'trading_phase' : TradingPhase.DISTRIBUTION,
        'debug' : False
    }
    backtester_static_config = {
        'initial_balance_a': 5000.0,
        'initial_balance_b': 0000.0,
        'fee': 0.001,
        'verbose': False
    }
    data_config={
        'data_path': Path('data/coinex_prices_raw'),
        'duration': 4320,
        'variation': 0.1,
        'tolerance': 0.01,
        'normalize': True
    }
    metrics= [
        PlotMode.TOTAL_VALUE_A,
        PlotMode.TOTAL_VALUE_B,
        PlotMode.ADJUSTED_A_BALANCE
    ]

    result_df = BacktestAnalyzer.run_multiple_backtests(
        backtester = Backtester(
            strategy=strategies.MultiMovingAverageStrategy(
                max_duration = 400,
                **strategy_static_config
            ),
            **backtester_static_config
        ),
        num_tests_per_strategy=100,
        data_config=data_config,
        metrics=metrics,
    )
    intervals = BacktestAnalyzer.calculate_confidence_interval(
        df=result_df,
        confidence=0.99
    )
    print(f"Variación de {data_config['variation']*100}%:")
    for metric, interval in intervals.items():
        print(f"  {metric}: [{interval[0]:.4f}, {interval[1]:.4f}] -> {abs(interval[1] - interval[0]):4f}")