import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path

import strategies
from backtester import Backtester
from definitions import PlotMode, TradingPhase, VisualizationDataframe
from plots_utils import draw_graphs, calculate_moving_averages_extra_plot

def backtest_simple(
        backtester: Backtester,
        data_config: dict = None,
        plot_config: dict = {
            'plot_modes': list(PlotMode),
            'save_path': None,
            'show': False
        }
) -> VisualizationDataframe:
    backtester.load_data(**data_config)
    backtester.simulate_real_time_execution()

    visualization_df = backtester.generate_visualization_df()
    extra_plots_price = None
    if plot_config.get('show', None):
        if isinstance(backtester.strategy, strategies.MultiMovingAverageStrategy):
            extra_plots_price = calculate_moving_averages_extra_plot(backtester.data)
        draw_graphs(
            visualization_df=visualization_df,  
            extra_plots_price=extra_plots_price,
            **plot_config
        )
    
    return visualization_df

def calculate_percentage_change(backtester: Backtester, data_config: dict = None) -> float:    
    backtester.load_data(**data_config)
    backtester.simulate_real_time_execution()
 
    # Generate Visualization df
    visualization_df = backtester.generate_visualization_df()

    # Store the last total_value for the current iteration
    last_total_value = visualization_df['total_value_b'].iloc[-1]
    initial_total_value = visualization_df['total_value_b'].iloc[0]
    percentage_change = ((last_total_value - initial_total_value) / initial_total_value) * 100

    return percentage_change


if __name__ == "__main__":
    backtest_simple(
        backtester=Backtester(
            strategy=strategies.MultiMovingAverageStrategy(
                max_duration = 200,
                min_purchase = 5.1,
                safety_margin = 1,
                trading_phase = TradingPhase.DISTRIBUTION,
                debug = False
            ),
            initial_balance_a=5000.0,
            initial_balance_b=0000.0,
            fee=0.001
        ),
        data_config={
            'data_path': Path('data/coinex_prices_raw'),
            'duration': 4320,
            'variation': 0,
            'tolerance': 0.01,
            'normalize': True
        },
        plot_config= {
            'plot_modes': list(PlotMode),
            'save_path': None, #Path('data/prueba.png'),
            'show': True
        }
    )