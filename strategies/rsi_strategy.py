from typing import List, Tuple
from definitions import Action, Memory, MarketData
from indicators import Indicators
from .strategy import Strategy

class RSIStrategy(Strategy):
    def __init__(self, rsi_period: int = 14, overbought: float = 70, oversold: float = 30, cost: float = 10):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.cost = cost

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []

        rsi = self.calculate_indicators(data)
        current_rsi = rsi[0]['result'].iloc[-1]
        balance_a = memory.get('balance_a', 0)
        balance_b = memory.get('balance_b', 0)
        current_price = data['close'].iloc[-1]
        quantity = self.cost / current_price

        if current_rsi < self.oversold and balance_b >= self.cost:
            actions.append((Action.BUY_MARKET, current_price, quantity))
        elif current_rsi > self.overbought and balance_a >= quantity:
            actions.append((Action.SELL_MARKET, current_price, quantity))
        else:
            actions.append((Action.WAIT, None, None))

        return actions

    def calculate_indicators(self, data: MarketData):
        return [Indicators.calculate_rsi(data, self.rsi_period)]
