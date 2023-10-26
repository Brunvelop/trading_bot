from enum import Enum
from typing import Tuple, List
from abc import ABC, abstractmethod

import pandas as pd

class Action(Enum):
    BUY_MARKET = "buy_market"
    SELL_MARKET = "sell_market"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    WAIT = "wait"

class Strategy(ABC):
    @abstractmethod
    def run(self, data, memory) -> List[Tuple[Action, float, float]]:
        pass # :return: [(action1, price1, quantity1), (action2, price2, quantity2), ...]

class MovingAverageStrategy(Strategy):
    def __init__(self, window_size, cost = 10):
        self.window_size = window_size
        self.cost = cost

    def run(self, data, memory):
        actions = []
        data['moving_average'] = data['price'].rolling(window=self.window_size).mean()

        if data['price'].iloc[-1] < data['moving_average'].iloc[-1] and self.balance_a > 0:
            self.balance_a -= self.cost + self.cost * self.fee
            self.balance_b += self.cost / data['price'].iloc[-1]
            actions.append((Action.BUY, data['price'].iloc[-1], self.cost / data['price'].iloc[-1]))

        elif data['price'].iloc[-1] > data['moving_average'].iloc[-1] and self.balance_b > 0:
            self.balance_b -= self.cost / data['price'].iloc[-1]
            self.balance_a += self.cost - self.cost * self.fee
            actions.append((Action.SELL, data['price'].iloc[-1], self.cost / data['price'].iloc[-1]))

        else:
            actions.append((Action.WAIT, None, None))

        return actions