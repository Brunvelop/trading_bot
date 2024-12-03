import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from definitions import PlotMode
from backtesting.backtester import Backtester
from strategies.multi_moving_average_strategy import MultiMovingAverageStrategy, TradingPhase

if __name__ == "__main__":
    backtester = Backtester(
        strategy=MultiMovingAverageStrategy(
            max_duration=341,
            min_purchase=5.1,
            safety_margin=1,
            trading_phase=TradingPhase.ACCUMULATION,
            debug=False
        ),
        initial_balance_a=0.0,
        initial_balance_b=100000.0,
        fee=0.001,
        verbose=True
    )
    
    df = backtester.run_backtest(
        data_config={
            'data_path': Path('E:/binance_prices_processed'),
            'duration': 43200,
            'variation': 0.10,
            'tolerance': 0.01,
            'normalize': True
        }
    )
    
    backtester.plot_results(
        plot_config={
            'plot_modes': list(PlotMode),
            'save_path': None,
            'show': True
        }
    )
