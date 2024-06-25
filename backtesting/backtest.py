import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
from definitions import Memory
from backtester import Backtester
from strategies import MultiMovingAverageStrategy
from plots_utils import draw_graphs

# results = []

# for i in range(5, 150, 5):
#     backtester = Backtester(
#         initial_balance_a = 889806.0, 
#         initial_balance_b = 0.0, 
#         fee = 0.001,
#         strategy = MultiMovingAverageStrategy(
#             ab_ratio=0.5, 
#             max_duration=i, 
#             min_purchase=0.1,
#             safety_margin=1
#         ),
#     )

#     prices = backtester.load_data('data/prices/DOG_USDT_1m.csv', start=None, end=10000000)
#     memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

#     # Generate Visualization df
#     visualization_df = backtester.generate_visualization_df()
#     extra_plots_price = backtester.moving_averages_extra_plot()

#     # Store the last total_value for the current iteration
#     last_total_value = visualization_df['total_value'].iloc[-1]
#     results.append((i, last_total_value))

#     plot_modes = ['balance_a', 'hold_value', 'total_value', 'balance_b']
#     draw_graphs(visualization_df, plot_modes, extra_plots_price, save_path=f'./data/plot_duration_{i}.png')
#     plt.close()  # Close the figure to avoid creating empty figures

# # Plot the results
# plt.figure()  # Create a new figure for the final plot
# x_values, y_values = zip(*results)
# plt.plot(x_values, y_values, marker='o')
# plt.xlabel('Duration (i)')
# plt.ylabel('Final Total Value')
# plt.title('Final Total Value vs Duration')
# plt.grid(True)
# plt.savefig('./data/final_total_value_vs_duration.png')
# plt.show()






backtester = Backtester(
    initial_balance_a = 100000.0, 
    initial_balance_b = 0.0, 
    fee = 0.001,
    strategy = MultiMovingAverageStrategy(
        ab_ratio=0.5, 
        max_duration=500, 
        min_purchase=0.1,
        safety_margin=1
    ),
)

# prices = backtester.load_data('data/prices/ADA_USD_1m.csv', start=None, end=100000)
prices = backtester.load_data('data/prices/ADA_USD.csv', duration=4320, variation=-0.05, tolerancia=0.01)
memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

# Generate Visualization df
visualization_df = backtester.generate_visualization_df()
extra_plots_price = backtester.moving_averages_extra_plot()

# Store the last total_value for the current iteration
last_total_value = visualization_df['total_value'].iloc[-1]

plot_modes = ['balance_a', 'hold_value', 'total_value', 'balance_b', 'price']
draw_graphs(visualization_df, plot_modes, extra_plots_price)





# import matplotlib.pyplot as plt
# import numpy as np
# from definitions import Memory
# from backtester import Backtester
# from strategies import MultiMovingAverageStrategy
# from plots_utils import draw_graphs
# from tqdm import tqdm

# results = []
# variations = []

# n = 10
# durations = range(5, 51, 5)

# for duration in tqdm(durations, desc="Processing Durations", unit="duration"):
#     for _ in tqdm(range(n), desc=f"Duration {duration}"):
#         variation = np.random.uniform(-0.5, 0.5)
#         backtester = Backtester(
#             initial_balance_a = 100000.0, 
#             initial_balance_b = 0.0, 
#             fee = 0.001,
#             strategy = MultiMovingAverageStrategy(
#                 ab_ratio=0.5, 
#                 max_duration=duration, 
#                 min_purchase=0.1,
#                 safety_margin=1
#             ),
#         )

#         prices = backtester.load_data('data/prices/ADA_USD_1m.csv', duration=4320, variation=variation, tolerancia=0.01)
#         memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

#         # Generate Visualization df
#         visualization_df = backtester.generate_visualization_df()
#         extra_plots_price = backtester.moving_averages_extra_plot()

#         # Store the last total_value for the current iteration
#         last_total_value = visualization_df['total_value'].iloc[-1]
#         initial_total_value = visualization_df['total_value'].iloc[0]
#         percentage_change = ((last_total_value - initial_total_value) / initial_total_value) * 100
#         results.append((duration, percentage_change))
#         variations.append(variation)

#         plot_modes = ['balance_a', 'hold_value', 'total_value', 'balance_b', 'price']
#         # draw_graphs(visualization_df, plot_modes, extra_plots_price, save_path=f'./data/plot_duration_{duration}_variation_{variation:.2f}.png')
#         # plt.close()  # Close the figure to avoid creating empty figures

# # Plot the results
# plt.figure()  # Create a new figure for the final plot
# x_values, y_values = zip(*results)
# colors = variations  # Use variations for color mapping
# scatter = plt.scatter(x_values, y_values, c=colors, cmap='coolwarm', alpha=0.5)
# plt.colorbar(scatter, label='Variation')
# plt.xlabel('Duration')
# plt.ylabel('Percentage Change in Total Value')
# plt.title('Percentage Change in Total Value vs Duration with Random Variations')
# plt.grid(True)
# plt.savefig('./data/percentage_change_total_value_vs_duration_with_variations.png')
# plt.show()