import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from definitions import PlotMode
from backtesting import Backtester
from strategies import MomentumRsiStrategy

if __name__ == "__main__":
    backtester = Backtester(
        strategy=MomentumRsiStrategy(
            max_duration=341,
            min_purchase=5.1,
            safety_margin=1,
            rsi_window=14,
            rsi_oversold=30,
            rsi_overbought=70,
            ma_windows=[20, 50],
            momentum_window=10,
            trading_phase=MomentumRsiStrategy.TradingPhase.ACCUMULATION,
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
