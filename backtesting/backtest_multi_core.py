import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from concurrent.futures import ProcessPoolExecutor, as_completed


import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import matplotlib.pyplot as plt

from backtester import Backtester
from definitions import TradingPhase
from backtest import calculate_percentage_change
from strategies import MultiMovingAverageStrategy


def backtest_percentage_change(
        data_path: Path = Path('data/coinex_prices_raw'),
        num_tests_per_strategy:int = 5,
        max_durations: range = range(5, 201, 50),
        price_duration: float = 5000,
        tolerance: float = 0.01,
        backtester_config: dict = None,
        strategy_config: dict = None,
    ) -> None:
    results = []

    with ProcessPoolExecutor() as executor:
        for duration in tqdm(max_durations, desc="Processing Durations", unit="duration"):
            variations_temp = np.random.uniform(-0.005, 0.005, num_tests_per_strategy)
            backtester = Backtester(
                **backtester_config,
                strategy = MultiMovingAverageStrategy(
                    max_duration=duration,
                    **strategy_config
                ),
            )
            future_to_variation = {
                executor.submit(
                    calculate_percentage_change,
                    variation,
                    backtester,
                    price_duration,
                    tolerance,
                    data_path
                ): variation for variation in variations_temp
            }            
            for future in tqdm(as_completed(future_to_variation), total=num_tests_per_strategy, desc=f"Duration {duration}"):
                variation = future_to_variation[future]
                percentage_change = future.result()
                results.append((duration, percentage_change, variation))

    df = pd.DataFrame(results, columns=['Duration', 'Percentage Change', 'Price Variation'])
    df.to_csv(f'./data/change_vs_duration_n{num_tests_per_strategy}_durations{max_durations.start}-{max_durations.stop}-{max_durations.step}.csv', index=False)

    fig, ax = plt.subplots(figsize=(20, 12))  # Crear una nueva figura con 1 subplot

    # Box plot
    df.boxplot(column='Percentage Change', by='Duration', ax=ax)
    ax.set_xlabel('Duration')
    ax.set_ylabel('Percentage Change')

    plt.tight_layout()
    fig.savefig(f'./data/change_vs_duration_n{num_tests_per_strategy}_durations{max_durations.start}-{max_durations.stop}-{max_durations.step}.png')
    plt.show()


if __name__ == '__main__':
    backtest_percentage_change(        
        data_path = Path('data/coinex_prices_raw'),
        num_tests_per_strategy = 10,
        max_durations = range(5, 201, 50),
        price_duration = 5000,
        tolerance = 0.01,
        backtester_config={
            'initial_balance_a': 100000,
            'initial_balance_b': 0,
            'fee': 0.001,
        },
        strategy_config={
            'min_purchase': 0.1,
            'safety_margin': 1,
            'trading_phase': TradingPhase.DISTRIBUTION,
            'debug': False
        }
    )