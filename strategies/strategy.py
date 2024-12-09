from abc import ABC, abstractmethod
from typing import Tuple, List
from definitions import Action, Memory, MarketData
from indicators import Indicator

class Strategy(ABC):
    @abstractmethod
    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        pass # :return: [(action1, price1, quantity1), (action2, price2, quantity2), ...]

    def calculate_indicators(data: MarketData) -> List[Indicator]:
        pass
