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
    
    def get_balance_b(self, memory):
        df = pd.DataFrame(memory)

        if df.empty:
            return 0

        total_bought = df.loc[(df['type'] == 'buy_market') & (df['executed'] == True), 'amount'].sum()
        total_sold = df.loc[(df['type'] == 'sell_market') & (df['executed'] == True), 'amount'].sum()

        total_balance = total_bought - total_sold

        return total_balance

class MovingAverageStrategy(Strategy):
    def __init__(self, window_size, cost = 10):
        self.window_size = window_size
        self.cost = cost

    def run(self, data, memory):
        actions = []

        data['moving_average'] = data['Close'].rolling(window=self.window_size).mean()
        balance_b = self.get_balance_b(memory)

        if data['Close'].iloc[-1] < data['moving_average'].iloc[-1]:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))

        elif data['Close'].iloc[-1] > data['moving_average'].iloc[-1] and balance_b > self.cost / data['Close'].iloc[-1]:
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))

        else:
            actions.append((Action.WAIT, None, None))

        return actions