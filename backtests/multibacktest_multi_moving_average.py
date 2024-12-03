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
    # Configuración de datos
    data_config = {
        'data_path': Path('E:/binance_prices_processed'),
        'duration': 4320,
        'variation': 0.1,
        'tolerance': 0.01,
        'normalize': True
    }

    # Métricas a analizar
    metrics = [
        PlotMode.BALANCE_A,
        PlotMode.BALANCE_B,
        PlotMode.TOTAL_VALUE_A,
        PlotMode.TOTAL_VALUE_B,
        PlotMode.ADJUSTED_A_BALANCE,
        PlotMode.ADJUSTED_B_BALANCE,
    ]

    # Ejecutar análisis múltiple
    result_df = MultiBacktest.run_multiple_backtests(
        backtester=backtester,
        num_tests_per_strategy=10,
        data_config=data_config,
        metrics=metrics,
    )

    # Mostrar resultados
    MultiBacktest.plot_results(result_df)

    # Calcular y mostrar intervalos
    confidence_intervals = MultiBacktest.calculate_confidence_interval(
        df=result_df,
        confidence=0.99
    )
    prediction_intervals = MultiBacktest.calculate_prediction_interval(
        df=result_df,
        confidence=0.99
    )

    print(f"Duración: {data_config['duration']}")
    print(f"Variación: {data_config['variation']*100}%:")
    for metric, interval in confidence_intervals.items():
        print(f"  {metric}: [{interval[0]:.4f}, {interval[1]:.4f}] -> {abs(interval[1] - interval[0]):4f}")

    MultiBacktest.plot_intervals(confidence_intervals, "Confidence", show=True)
    MultiBacktest.plot_intervals(prediction_intervals, "Prediction", show=True)
