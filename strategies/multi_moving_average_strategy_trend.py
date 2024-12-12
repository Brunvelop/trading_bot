from enum import Enum, auto
from datetime import datetime
from typing import Tuple, List
import numpy as np

from definitions import Action, Memory, MarketData, TradingPhase
from indicators import Indicators
from .strategy import Strategy

class MultiMovingAverageStrategyTrend(Strategy):
    class Alignment(Enum):
        UP = auto()
        DOWN = auto()
        NONE = auto()

    def __init__(self, 
            windows: List[int] = [10, 50, 100, 200],
            trading_phase: TradingPhase = TradingPhase.NEUTRAL,
            debug: bool = True
        ) -> None:
        self.windows = windows
        self.trading_phase = trading_phase
        self.current_alignment = self.Alignment.NONE
        self.opening_position = False
        self.closing_position = False
        self.debug = debug

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []
        balance_a, balance_b = memory.balance_a, memory.balance_b

        moving_averages = self.calculate_indicators(data)
        current_price = data['close'].iloc[-1]
        
        if (current_price > moving_averages[0].result.iloc[-1] > 
            moving_averages[1].result.iloc[-1] > 
            moving_averages[2].result.iloc[-1] > 
            moving_averages[3].result.iloc[-1]):
            alignment = self.Alignment.UP
        elif (current_price < moving_averages[0].result.iloc[-1] < 
            moving_averages[1].result.iloc[-1] < 
            moving_averages[2].result.iloc[-1] < 
            moving_averages[3].result.iloc[-1]):
            alignment = self.Alignment.DOWN
        else:
            alignment = self.Alignment.NONE

        if alignment != self.Alignment.NONE and alignment != self.current_alignment:
            self.current_alignment = alignment
            if balance_b > 0:
                self.opening_position = True
        
        if self.opening_position:
            if self.current_alignment == self.Alignment.UP and current_price < moving_averages[0].result.iloc[-1]:
                actions.append((Action.BUY_MARKET, current_price, balance_b/current_price))
                self.opening_position = False
                self.closing_position = True
        
        elif self.closing_position:
            if current_price < data['close'].iloc[:100].min():
                actions.append((Action.SELL_MARKET, current_price, balance_a))
                self.closing_position = False
            elif alignment == self.Alignment.UP:
                actions.append((Action.SELL_MARKET, current_price, balance_a/400))
                
        else:
            actions.append((Action.WAIT, None, None))

        if self.debug:
            print("\n=== Strategy Debug Info ===")
            print(f"Time: {str(data['date'].iloc[-1])}")
            print(f"Trading Phase: {self.trading_phase}")
            print(f"Current Price: {current_price}")
            print("\nMoving Averages:")
            for i, ma in enumerate(moving_averages):
                print(f"MA{self.windows[i]}: {ma.result.iloc[-1]:.2f}")
            print(f"\nCurrent Alignment: {self.current_alignment}")
            print(f"Opening Position: {self.opening_position}")
            print(f"Closing Position: {self.closing_position}")
            print(f"\nBalances:")
            print(f"Balance A: {balance_a}")
            print(f"Balance B: {balance_b}")
            print(f"\nActions: {actions}")
            print("========================\n")

        return actions
    
    def calculate_indicators(self, data: MarketData):
        return [Indicators.calculate_moving_average(data, window) for window in self.windows]
