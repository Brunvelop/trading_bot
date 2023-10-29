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
    def __init__(self, window_size = 200, cost = 10):
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
    
class MultiMovingAverageStrategy(Strategy):
    def __init__(self, windows=[10, 50, 100, 200], cost=10):
        self.windows = windows
        self.cost = cost

    def run(self, data, memory):
        actions = []
        balance_b = self.get_balance_b(memory).iloc[-1]

        # Calculamos las medias móviles para cada ventana
        moving_averages = [data['Close'].rolling(window=window).mean() for window in self.windows]

        # Comprobamos si las medias móviles están alineadas
        aligned_up = all(ma1.iloc[-1] > ma2.iloc[-1] for ma1, ma2 in zip(moving_averages, moving_averages[1:]))
        aligned_down = all(ma1.iloc[-1] < ma2.iloc[-1] for ma1, ma2 in zip(moving_averages, moving_averages[1:]))

        # Comprobamos si el precio de cierre está por encima o por debajo de todas las medias móviles
        above_all = all(data['Close'].iloc[-1] > ma.iloc[-1] for ma in moving_averages)
        below_all = all(data['Close'].iloc[-1] < ma.iloc[-1] for ma in moving_averages)

        if above_all and aligned_up and balance_b > self.cost / data['Close'].iloc[-1]:
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        elif below_all and aligned_down:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        else:
            actions.append((Action.WAIT, None, None))

        return actions