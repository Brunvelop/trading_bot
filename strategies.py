from typing import Tuple, List
from abc import ABC, abstractmethod

import pandas as pd

from indicators import Indicators
from definitions import Action, Memory, MarketData, OscilationAnalysis


class Strategy(ABC):
    @abstractmethod
    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        pass # :return: [(action1, price1, quantity1), (action2, price2, quantity2), ...]

class MovingAverageStrategy(Strategy):
    def __init__(self, window_size: int = 200, cost: float = 10) -> None:
        self.window_size = window_size
        self.cost = cost

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []

        moving_average = Indicators.calculate_moving_average(data, self.window_size).iloc[-1]
        balance_b = memory.get('balance_b', 0)
        current_price = data['Close'].iloc[-1]
        quantity = self.cost / current_price

        if current_price < moving_average:
            actions.append((Action.BUY_MARKET, current_price, quantity))
        elif current_price > moving_average and balance_b > quantity:
            actions.append((Action.SELL_MARKET, current_price, quantity))
        else:
            actions.append((Action.WAIT, None, None))

        return actions
    
class MultiMovingAverageStrategy(Strategy):
    def __init__(self, ab_ratio: float = 1, max_duration: int = 500, min_purchase:float = 5,
                 safety_margin: float = 3, windows: List[int] = [10, 50, 100, 200] ) -> None:
        self.windows = windows
        self.ab_ratio = ab_ratio
        self.max_duration = max_duration
        self.safety_margin = safety_margin
        self.min_purchase = min_purchase
        self.distribution_length = 0
        self.acumulation_length = 0
        
    def run(self, data: MarketData, memory: Memory) -> List[Action]:
        actions = []
        balance_a = memory.get('balance_a', 0)
        balance_b = memory.get('balance_b', 0)
        current_price = data['Close'].iloc[-1]

        # Calculamos las medias móviles para cada ventana
        moving_averages = [Indicators.calculate_moving_average(data, window).iloc[-1] for window in self.windows]

        # Comprobamos si las medias móviles están alineadas
        aligned_up = current_price > moving_averages[0] > moving_averages[1] > moving_averages[2] >  moving_averages[3]
        aligned_down = current_price < moving_averages[0] < moving_averages[1] < moving_averages[2] <  moving_averages[3]

        # Calculamos que estado
        acumulation = current_price * balance_a < self.ab_ratio * balance_b 
        distribution = current_price * balance_a > self.ab_ratio * balance_b
        
        if acumulation:
            amount = balance_b / (self.max_duration * self.safety_margin * current_price)
            enough_amount_to_sell = balance_a > amount and amount * current_price > self.min_purchase
            enough_amount_to_buy = balance_b > amount * current_price and amount * current_price > self.min_purchase
            if aligned_up and enough_amount_to_sell:
                self.acumulation_length -=1
                actions.append((Action.SELL_MARKET, current_price, amount))
            elif aligned_down and enough_amount_to_buy:
                self.acumulation_length +=1
                actions.append((Action.BUY_MARKET, current_price, amount))
        elif distribution:
            amount = balance_a / ( self.max_duration * self.safety_margin )
            enough_amount_to_sell = balance_a > amount and amount * current_price > self.min_purchase
            enough_amount_to_buy = balance_b > amount * current_price and amount * current_price > self.min_purchase
            if aligned_up and enough_amount_to_sell:
                self.distribution_length +=1
                actions.append((Action.SELL_MARKET, current_price, amount))
            elif aligned_down and enough_amount_to_buy:
                self.distribution_length -=1
                actions.append((Action.BUY_MARKET, current_price, amount))
        else:
            actions.append((Action.WAIT, None, None))

        return actions