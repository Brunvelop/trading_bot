import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from definitions import PlotMode
from backtesting.backtester import Backtester
from backtesting.multi_backtest import MultiBacktest
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
    data_config = {
        'data_path': Path('E:/binance_prices_processed'),
        'duration': 4320,
        'variation': 0.1,
        'tolerance': 0.01,
        'normalize': True
    }
    metrics = [
        PlotMode.BALANCE_A,
        PlotMode.BALANCE_B,
        PlotMode.TOTAL_VALUE_A,
        PlotMode.TOTAL_VALUE_B,
        PlotMode.ADJUSTED_A_BALANCE,
        PlotMode.ADJUSTED_B_BALANCE,
    ]

    # Ejecutar backtests y obtener resultados base
    result_df = MultiBacktest.run_multiple_backtests(
        backtester=backtester,
        num_tests_per_strategy=10,
        data_config=data_config,
        metrics=metrics,
    )

    # Mostrar resultados base
    MultiBacktest.plot_results(result_df)

    # Calcular y añadir intervalos de confianza
    result_df = MultiBacktest.calculate_confidence_interval(
        df=result_df,
        confidence=0.99
    )

    # Calcular y añadir intervalos de predicción
    result_df = MultiBacktest.calculate_prediction_interval(
        df=result_df,
        confidence=0.99
    )

    # Mostrar información general
    print(f"\nConfiguración del backtest:")
    print(f"Duración: {data_config['duration']}")
    print(f"Variación: {data_config['variation']*100}%")

    # Visualizar intervalos
    MultiBacktest.plot_intervals(result_df, "Confidence", show=True)
    MultiBacktest.plot_intervals(result_df, "Prediction", show=True)
