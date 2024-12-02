from typing import List, Tuple
from definitions import Action, Memory, MarketData
from indicators import Indicators
from .strategy import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, window_size: int = 200, cost: float = 10) -> None:
        self.window_size = window_size
        self.cost = cost

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []

        moving_average = Indicators.calculate_moving_average(data, self.window_size)['result'].iloc[-1]
        balance_b = memory.get('balance_b', 0)
        current_price = data['close'].iloc[-1]
        quantity = self.cost / current_price

        if current_price < moving_average:
            actions.append((Action.BUY_MARKET, current_price, quantity))
        elif current_price > moving_average and balance_b > quantity:
            actions.append((Action.SELL_MARKET, current_price, quantity))
        else:
            actions.append((Action.WAIT, None, None))

        return actions
