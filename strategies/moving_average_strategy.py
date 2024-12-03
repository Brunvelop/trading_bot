from typing import List, Tuple
from definitions import Action, Memory, MarketData
from indicators import Indicators
from .strategy import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, window_size: int = 200) -> None:
        self.window_size = window_size

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        price = data['close'].iloc[-1]
        ma = self.calculate_indicators(data)[0]['result'].iloc[-1]
        
        if price > ma and memory.balance_b > 0:
            return [(Action.BUY_MARKET, price, memory.balance_b / price)]
        
        if price < ma and memory.balance_a > 0:
            return [(Action.SELL_MARKET, price, memory.balance_a)]
            
        return [(Action.WAIT, None, None)]
    
    def calculate_indicators(self, data: MarketData):
        return [Indicators.calculate_moving_average(data, self.window_size)]
