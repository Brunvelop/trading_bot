@/strategies/multi_moving_average_strategy.py 
@/strategies/momentum_rsi_strategy.py 

son las mejores estrategia de trading que tengo ahoramismo. Aqui tienes sus resultados:
backtests\results\duration_43200\variations_-0.5_0.5\tests_100\summaries\MomentumRsiStrategy.csv
backtests\results\duration_43200\variations_-0.5_0.5\tests_100\summaries\MultiMovingAverageStrategy.csv

Quiero que me ayudes a diseñar una nueva estrategia que pueda batir sus resultados. Posteriormente hare el backtest y te dire los resultados para que iteremos y sigamos mejorando.

Puedes crear los indicadores que consideres pero recuerda incluirlos en @/indicators.py

Fijate en @/strategies/strategy.py @/drawer/indicator_drawer.py @/strategies/__init__.py 

Para hacer el código compatible

Finalmente crea un backtest similar al de @/backtests/backtest_multi_moving_average.py con la nueva estrategia y Escribe un archivo similar a @/backtests/experiment_multi_moving_average.py para la nueva estrategia