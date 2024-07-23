import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Tuple

import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

from backtester import Backtester
from strategies import MultiMovingAverageStrategy
from definitions import Memory, PlotMode, TradingPhase
from plots_utils import draw_graphs, calculate_moving_averages_extra_plot

def backtest_001():
    backtester = Backtester(
        initial_balance_a = 100000.0,
        initial_balance_b = 0.0, 
        fee = 0.001,
        strategy = MultiMovingAverageStrategy(
            max_duration = 500, 
            min_purchase = 0.1,
            safety_margin = 1,
            trading_phase = TradingPhase.DISTRIBUTION,
            debug = False
        ),
    )

    # prices = backtester.load_data('data/prices/ADA_USD_1m.csv', start=None, end=100000)
    prices = backtester.load_data('data/prices_old/ADA_USD.csv', duration=4320, variation=-0.05, tolerancia=0.01)
    memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

    # Generate Visualization df
    visualization_df = backtester.generate_visualization_df()
    extra_plots_price = calculate_moving_averages_extra_plot(backtester.data)

    # Store the last total_value for the current iteration
    last_total_value = visualization_df['total_value'].iloc[-1]

    plot_modes = [
        PlotMode.PRICE,
        PlotMode.BALANCE_A,
        PlotMode.BALANCE_B,
        PlotMode.HOLD_VALUE,
        PlotMode.TOTAL_VALUE_A,
        PlotMode.TOTAL_VALUE_B,
        PlotMode.ADJUSTED_B_BALANCE
    ]
    draw_graphs(visualization_df, plot_modes, extra_plots_price)

def backtest_002():
    results = []

    for i in range(5, 150, 50):
        backtester = Backtester(
            initial_balance_a = 889806.0, 
            initial_balance_b = 0.0, 
            fee = 0.001,
            strategy = MultiMovingAverageStrategy(
                max_duration=i, 
                min_purchase=0.1,
                safety_margin=1,
                trading_phase = TradingPhase.DISTRIBUTION,
                debug = False
            ),
        )

        prices = backtester.load_data('data/old/DOG_USDT_1m.csv', start=None, end=4320)
        memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

        # Generate Visualization df
        visualization_df = backtester.generate_visualization_df()
        extra_plots_price = calculate_moving_averages_extra_plot(backtester.data)

        # Store the last total_value for the current iteration
        last_total_value = visualization_df['total_value_b'].iloc[-1]
        results.append((i, last_total_value))

        plot_modes = [
            PlotMode.PRICE,
            PlotMode.BALANCE_A,
            PlotMode.BALANCE_B,
            PlotMode.HOLD_VALUE,
            PlotMode.TOTAL_VALUE_A,
            PlotMode.TOTAL_VALUE_B,
            PlotMode.ADJUSTED_B_BALANCE
        ]
        draw_graphs(
        visualization_df,
        plot_modes, 
        extra_plots_price, 
        save_path=f'./data/plot_duration_{i}.png',
        show=False
        )
        plt.close()  # Close the figure to avoid creating empty figures

    # Plot the results
    plt.figure()  # Create a new figure for the final plot
    x_values, y_values = zip(*results)
    plt.plot(x_values, y_values, marker='o')
    plt.xlabel('Duration (i)')
    plt.ylabel('Final Total Value')
    plt.title('Final Total Value vs Duration')
    plt.grid(True)
    plt.savefig('./data/final_total_value_vs_duration.png')
    plt.show()

def backtest_003():
    results = []
    variations = []

    n = 5
    durations = range(5, 151, 50)

    for duration in tqdm(durations, desc="Processing Durations", unit="duration"):
        for _ in tqdm(range(n), desc=f"Duration {duration}"):
            variation = np.random.uniform(-0.5, 0.5)
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
            results.append((duration, percentage_change))
            variations.append(variation)

            plot_modes = ['balance_a', 'hold_value', 'total_value', 'balance_b', 'price']
            # draw_graphs(visualization_df, plot_modes, extra_plots_price, save_path=f'./data/plot_duration_{duration}_variation_{variation:.2f}.png')
            # plt.close()  # Close the figure to avoid creating empty figures

    # Plot the results
    plt.figure()  # Create a new figure for the final plot
    x_values, y_values = zip(*results)
    colors = variations  # Use variations for color mapping
    scatter = plt.scatter(x_values, y_values, c=colors, cmap='coolwarm', alpha=0.5)
    plt.colorbar(scatter, label='Variation')
    plt.xlabel('Duration')
    plt.ylabel('Percentage Change in Total Value')
    plt.title('Percentage Change in Total Value vs Duration with Random Variations')
    plt.grid(True)
    plt.savefig('./data/percentage_change_total_value_vs_duration_with_variations.png')
    plt.show()

def calculate_percentage_change(backtester: Backtester, variation: float) -> Tuple[float, float]:

    prices = backtester.load_data('data/prices_old/ADA_USD.csv', duration=4320, variation=variation, tolerancia=0.01)
    memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

    # Generate Visualization df
    visualization_df = backtester.generate_visualization_df()
    extra_plots_price = calculate_moving_averages_extra_plot(backtester.data)

    # Store the last total_value for the current iteration
    last_total_value = visualization_df['total_value_b'].iloc[-1]
    initial_total_value = visualization_df['total_value_b'].iloc[0]
    percentage_change = ((last_total_value - initial_total_value) / initial_total_value) * 100

    return percentage_change, variation


if __name__ == "__main__":
    backtest_001()
    backtest_002()
    backtest_003()