from enum import Enum, auto
from typing import Tuple, List

import numpy as np

from definitions import Memory, MarketData
from indicators import Indicators, Indicator
from .strategy import Strategy, Action, ActionType

class MultiMovingAverageStrategy(Strategy):
    class Alignment(Enum):
        UP = auto()
        DOWN = auto()
        NONE = auto()
    
    class TradingPhase(Enum):
        ACCUMULATION = auto()
        DISTRIBUTION = auto()
        NEUTRAL = auto()

    def __init__(self, 
            max_duration: int = 500, 
            min_purchase: float = 5.1,
            safety_margin: float = 3, 
            windows: List[int] = [10, 50, 100, 200],
            trading_phase: TradingPhase = TradingPhase.NEUTRAL,
            debug: bool = True
        ) -> None:
        self.max_duration = max_duration
        self.min_purchase = min_purchase
        self.safety_margin = safety_margin
        self.windows = windows
        self.distribution_length = 0
        self.acumulation_length = 0
        self.trading_phase = trading_phase
        self.debug = debug

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []
        balance_a, balance_b = memory.balance_a, memory.balance_b
        current_price = data['close'].iloc[-1]

        alignment = self._determine_alignment(data)
        amount = self._calculate_amount(balance_a, balance_b, current_price)

        if self.trading_phase == self.TradingPhase.ACCUMULATION:
            if alignment == self.Alignment.UP and self._can_sell(balance_a, amount):
                self.acumulation_length -=1
                actions.append(Action(action_type=ActionType.SELL_MARKET, price=current_price, amount=amount))
            elif alignment == self.Alignment.DOWN and self._can_buy(balance_b, amount, current_price):
                self.acumulation_length +=1
                actions.append(Action(action_type=ActionType.BUY_MARKET, price=current_price, amount=amount))
        elif self.trading_phase == self.TradingPhase.DISTRIBUTION:
            if alignment == self.Alignment.UP and self._can_sell(balance_a, amount):
                self.distribution_length +=1
                actions.append(Action(action_type=ActionType.SELL_MARKET, price=current_price, amount=amount))
            elif alignment == self.Alignment.DOWN and self._can_buy(balance_b, amount, current_price):
                self.distribution_length -=1
                actions.append(Action(action_type=ActionType.BUY_MARKET, price=current_price, amount=amount))
        else:
            actions.append(Action(action_type=ActionType.WAIT, price=current_price, amount=np.float64(0)))

        if self.debug:
            print("time:", str(data['date'].iloc[-1]))
            print(self.trading_phase)
            print(alignment)
            print("blance_a:", balance_a,"|", "balance_b:", balance_b)
            print("distribution_n:", self.distribution_length, "acumulation_n:", self.acumulation_length)
            print("can_sell:", self._can_sell(balance_a, amount),"|", "can_buy:", self._can_buy(balance_b, amount, current_price))
            print("amount:", amount)
            print("amount_price:", amount * current_price)
            print(actions)

        return actions
    
    def calculate_indicators(self, data: MarketData) -> List[Indicator]:
        return [Indicators.calculate_moving_average(data, window) for window in self.windows]

    def _determine_alignment(self, data: MarketData) -> Alignment:
        moving_averages = self.calculate_indicators(data)
        current_price = data['close'].iloc[-1]
        
        if (current_price > moving_averages[0].result.iloc[-1] > 
            moving_averages[1].result.iloc[-1] > 
            moving_averages[2].result.iloc[-1] > 
            moving_averages[3].result.iloc[-1]):
            return self.Alignment.UP
        elif (current_price < moving_averages[0].result.iloc[-1] < 
            moving_averages[1].result.iloc[-1] < 
            moving_averages[2].result.iloc[-1] < 
            moving_averages[3].result.iloc[-1]):
            return self.Alignment.DOWN
        return self.Alignment.NONE

    def _calculate_amount(self, balance_a: float, balance_b: float, current_price: float) -> float:
        if self.trading_phase == self.TradingPhase.NEUTRAL:
            return 0
        elif self.trading_phase == self.TradingPhase.ACCUMULATION:
            amount = balance_b / (self.max_duration * self.safety_margin * current_price)
        elif self.trading_phase == self.TradingPhase.DISTRIBUTION:
            amount = balance_a / ( self.max_duration * self.safety_margin )

        return max(amount, self.min_purchase / current_price)

    def _can_sell(self, balance_a: float, amount: float) -> bool:
        enough_amount_to_sell = balance_a > amount
        if self.trading_phase == self.TradingPhase.ACCUMULATION:
            return enough_amount_to_sell and self.acumulation_length > 0
        elif self.trading_phase == self.TradingPhase.DISTRIBUTION:
            return enough_amount_to_sell 
        return enough_amount_to_sell
    
    def _can_buy(self, balance_b: float, amount: float, current_price: float) -> bool:
        enough_amount_to_buy = balance_b > amount * current_price
        if self.trading_phase == self.TradingPhase.ACCUMULATION:
            return enough_amount_to_buy 
        elif self.trading_phase == self.TradingPhase.DISTRIBUTION:
            return enough_amount_to_buy and self.distribution_length > 0
        return enough_amount_to_buy
