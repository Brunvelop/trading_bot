from typing import List, Tuple
import numpy as np

from definitions import Action, Memory, MarketData
from indicators import Indicators
from .strategy import Strategy

class VolumeTrendMomentumStrategy(Strategy):
    def __init__(self, 
                 ma_window: int = 120, 
                 velocity_window: int = 1,
                 acceleration_window: int = 60,
                 cost: float = 10,
                 debug: bool = False):
        self.ma_window = ma_window
        self.velocity_window = velocity_window
        self.acceleration_window = acceleration_window
        self.cost = cost
        self.debug = debug

    def calculate_indicators(self, data: MarketData):
        ma = Indicators.calculate_moving_average(data, self.ma_window)
        velocity = Indicators.calculate_velocity(ma.result, self.velocity_window)
        acceleration = Indicators.calculate_acceleration(velocity.result, self.acceleration_window)
        return [ma, velocity, acceleration]

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []
        indicators = self.calculate_indicators(data)
        
        current_price = data['close'].iloc[-1]
        current_ma = indicators[0].result.iloc[-1]
        current_velocity = indicators[1].result.iloc[-1]
        current_acceleration = indicators[2].result.iloc[-1]
        
        balance_a = memory.balance_a
        balance_b = memory.balance_b

        # Buy conditions: price < MA, velocity < 0, acceleration > 0
        if (balance_b >= self.cost and 
            current_price < current_ma and 
            current_velocity < 0 and 
            current_acceleration > 0):
            actions.append((Action.BUY_MARKET, np.float64(current_price), np.float64(self.cost)))
            
        # Sell conditions: price > MA, velocity > 0, acceleration < 0
        elif (balance_a >= self.cost/current_price and 
              current_price > current_ma and 
              current_velocity > 0 and 
              current_acceleration < 0):
            actions.append((Action.SELL_MARKET, np.float64(current_price), np.float64(self.cost/current_price)))

        if not actions:
            actions.append((Action.WAIT, None, None))

        if self.debug:
            print(f"Price: {current_price:.2f}")
            print(f"ma: {current_ma:.2f}")
            print(f"Velocity: {current_velocity:.4f}")
            print(f"Acceleration: {current_acceleration:.4f}")
            print(f"Action: {actions}")

        return actions
