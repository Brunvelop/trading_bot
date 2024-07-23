import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import concurrent.futures

import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

from definitions import Memory, TradingPhase
from backtester import Backtester
from strategies import MultiMovingAverageStrategy
from plots_utils import calculate_moving_averages_extra_plot

def run_simulation(duration, variation):
    backtester = Backtester(
        initial_balance_a = 100000.0, 
        initial_balance_b = 0.0, 
        fee = 0.001,
        strategy = MultiMovingAverageStrategy(
            max_duration=duration, 
            min_purchase=0.1,
            safety_margin=1,
            trading_phase = TradingPhase.DISTRIBUTION,
            debug = False
        ),
    )

    prices = backtester.load_data('data/prices_old/ADA_USD.csv', duration=4320, variation=variation, tolerancia=0.01)
    memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

    # Generate Visualization df
    visualization_df = backtester.generate_visualization_df()
    extra_plots_price = calculate_moving_averages_extra_plot(backtester.data)

    # Store the last total_value for the current iteration
    last_total_value = visualization_df['total_value_b'].iloc[-1]
    initial_total_value = visualization_df['total_value_b'].iloc[0]
    percentage_change = ((last_total_value - initial_total_value) / initial_total_value) * 100

    return (duration, percentage_change, variation)

def backtest_001(run_simulation):
    results = []
    variations = np.array([])

    n = 5
    durations = range(5, 251, 25)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for duration in tqdm(durations, desc="Processing Durations", unit="duration"):
            variations_temp = np.random.uniform(-0.005, 0.005, n)
            futures = [executor.submit(run_simulation, duration, variation) for variation in variations_temp]
            for future in tqdm(concurrent.futures.as_completed(futures), total=n, desc=f"Duration {duration}"):
                result = future.result()
                results.append(result[:2])
                variations = np.append(variations, result[2])

    df = pd.DataFrame(results, columns=['Duration', 'Percentage Change'])
    df['Variation'] = variations
    df.to_csv(f'./data/change_vs_duration_n{n}_durations{durations.start}-{durations.stop}-{durations.step}.csv', index=False)

    # Plot the results

    x_values, y_values = zip(*results)
    colors = variations  # Use variations for color mapping
    # New box plot using matplotlib in the same figure
    fig, axs = plt.subplots(2, figsize=(20, 12))  # Create a new figure with 2 subplots

    # Scatter plot
    scatter = axs[0].scatter(x_values, y_values, c=colors, cmap='coolwarm', alpha=0.5)
    fig.colorbar(scatter, ax=axs[0], label='Variation')
    axs[0].set_xlabel('Duration')
    axs[0].set_ylabel('Percentage Change in Total Value')
    axs[0].set_title('Percentage Change in Total Value vs Duration with Random Variations')
    axs[0].grid(True)

    # Box plot
    df.boxplot(column='Percentage Change', by='Duration', ax=axs[1])
    axs[1].set_title('Box plot of Percentage Change by Duration')
    axs[1].set_xlabel('Duration')
    axs[1].set_ylabel('Percentage Change')

    plt.tight_layout()
    fig.savefig(f'./data/change_vs_duration_n{n}_durations{durations.start}-{durations.stop}-{durations.step}.png')
    plt.show()


if __name__ == '__main__':
    backtest_001(run_simulation)