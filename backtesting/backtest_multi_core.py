import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import concurrent.futures

import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

from backtester import Backtester
from definitions import TradingPhase
from backtest import calculate_percentage_change
from strategies import MultiMovingAverageStrategy


def backtest_percentage_change(
        num_tests_per_strategy:int = 5,
        max_durations: range = range(5, 201, 50),
        backtester_config: dict = None,
        strategy_config: dict = None
    ) -> None:
    results = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for duration in tqdm(max_durations, desc="Processing Durations", unit="duration"):
            variations_temp = np.random.uniform(-0.005, 0.005, num_tests_per_strategy)
            backtester = Backtester(
                **backtester_config,
                strategy = MultiMovingAverageStrategy(
                    max_duration=duration,
                    **strategy_config
                ),
            )
            futures = [executor.submit(calculate_percentage_change, backtester, variation) for variation in variations_temp]
            for future in tqdm(concurrent.futures.as_completed(futures), total=num_tests_per_strategy, desc=f"Duration {duration}"):
                percentage_change, variation = future.result()
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
        num_tests_per_strategy = 40,
        max_durations = range(5, 151, 10),
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