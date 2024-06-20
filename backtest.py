from definitions import Memory
from backtester import Backtester
from strategies import MultiMovingAverageStrategy
from plots_utils import draw_graphs


backtester = Backtester(
    initial_balance_a = 889806.0, 
    initial_balance_b = 0.0, 
    fee = 0.001,
    strategy = MultiMovingAverageStrategy(
        ab_ratio=0.5, 
        max_duration=341, 
        min_purchase=5.1,
        safety_margin=2
    ),
)

prices = backtester.load_data('data/prices/DOG_USDT_1m.csv', start=None, end=3000)
memory: Memory = backtester.simulate_real_time_execution(window_size = 350)

#Generate Visualization df
visualization_df = backtester.generate_visualization_df()
extra_plots_price = backtester.moving_averages_extra_plot()

plot_modes = ['balance_a', 'hold_value', 'total_value', 'balance_b', 'price']
draw_graphs(visualization_df, plot_modes, extra_plots_price)