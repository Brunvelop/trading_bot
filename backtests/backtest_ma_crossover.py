import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from definitions import PlotMode
from backtesting.backtester import Backtester
from strategies.ma_crossover_strategy import MACrossoverStrategy

if __name__ == "__main__":
    backtester = Backtester(
        strategy=MACrossoverStrategy(),
        initial_balance_a=0.0,
        initial_balance_b=100000.0,  # Starting with 100k USDT
        fee=0.001,  # 0.1% fee
        verbose=True
    )
    
    df = backtester.run_backtest(
        data_config={
            'data_path': Path('E:/binance_prices_processed'),
            'duration': 4320,
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
