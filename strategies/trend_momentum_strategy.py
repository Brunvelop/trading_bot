from enum import Enum, auto
from typing import List, Tuple
import numpy as np

from definitions import Action, Memory, MarketData
from indicators import Indicators
from .strategy import Strategy

class TrendMomentumStrategy(Strategy):
    class TrendState(Enum):
        STRONG_UPTREND = auto()    # Price > MA200, velocity > 0, acceleration > 0
        WEAK_UPTREND = auto()      # Price > MA200, velocity > 0, acceleration < 0
        TREND_REVERSAL = auto()    # Price crosses MA200 or velocity changes sign
        WEAK_DOWNTREND = auto()    # Price < MA200, velocity < 0, acceleration > 0
        STRONG_DOWNTREND = auto()  # Price < MA200, velocity < 0, acceleration < 0
        NEUTRAL = auto()           # Initial state or undefined conditions

    def __init__(self, 
                 ma_window: int = 200, 
                 velocity_window: int = 10,
                 acceleration_window: int = 5,
                 cost: float = 10,
                 debug: bool = True):
        self.ma_window = ma_window
        self.velocity_window = velocity_window
        self.acceleration_window = acceleration_window
        self.cost = cost
        self.debug = debug
        self.position_quantity = 0

    def calculate_indicators(self, data: MarketData):
        # Calculate MA200
        ma200 = Indicators.calculate_moving_average(data, self.ma_window)
        
        # Calculate velocity using price changes
        velocity = Indicators.calculate_velocity(data['close'], self.velocity_window)
        
        # Calculate acceleration using the velocity
        acceleration = Indicators.calculate_acceleration(velocity['result'], self.acceleration_window)
        
        return [ma200, velocity, acceleration]

    def _determine_trend_state(self, price: float, ma: float, velocity: float, acceleration: float) -> TrendState:
        # Handle NaN values or insufficient data
        if np.isnan(velocity) or np.isnan(acceleration):
            if price > ma:
                return self.TrendState.WEAK_UPTREND
            elif price < ma:
                return self.TrendState.WEAK_DOWNTREND
            return self.TrendState.NEUTRAL

        if price > ma:
            if velocity > 0:
                return (self.TrendState.STRONG_UPTREND 
                       if acceleration > 0 
                       else self.TrendState.WEAK_UPTREND)
            else:
                return self.TrendState.TREND_REVERSAL
        else:  # price < ma
            if velocity < 0:
                return (self.TrendState.STRONG_DOWNTREND 
                       if acceleration < 0 
                       else self.TrendState.WEAK_DOWNTREND)
            else:
                return self.TrendState.TREND_REVERSAL
        
        return self.TrendState.NEUTRAL

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []
        indicators = self.calculate_indicators(data)
        
        current_price = data['close'].iloc[-1]
        current_ma = indicators[0]['result'].iloc[-1]
        current_velocity = indicators[1]['result'].iloc[-1]
        current_acceleration = indicators[2]['result'].iloc[-1]
        
        trend_state = self._determine_trend_state(
            current_price, current_ma, current_velocity, current_acceleration
        )
        
        balance_a = memory.get('balance_a', 0)  # Crypto
        balance_b = memory.get('balance_b', 0)  # USDT
        quantity = self.cost / current_price

        # Stop loss - vende toda la posición si el precio cierra bajo la media
        if current_price < current_ma and self.position_quantity > 0:
            actions.append((Action.SELL_MARKET, current_price, self.position_quantity))
            self.position_quantity = 0
            return actions

        # Trading logic based on trend state
        if trend_state == self.TrendState.WEAK_DOWNTREND and balance_b >= self.cost:
            # Comprar cuando el precio cae pero la aceleración de caída disminuye
            actions.append((Action.BUY_MARKET, current_price, quantity))
            self.position_quantity += quantity
            
        elif trend_state == self.TrendState.WEAK_UPTREND and self.position_quantity > 0:
            # Vender cuando el precio sube pero la fuerza de subida disminuye
            actions.append((Action.SELL_MARKET, current_price, self.position_quantity))
            self.position_quantity = 0

        if not actions:
            actions.append((Action.WAIT, None, None))

        if self.debug:
            print(f"Price: {current_price:.2f}")
            print(f"MA200: {current_ma:.2f}")
            print(f"Velocity: {current_velocity:.4f}")
            print(f"Acceleration: {current_acceleration:.4f}")
            print(f"Trend State: {trend_state}")
            print(f"Position: {self.position_quantity:.4f}")
            print(f"Action: {actions}")

        return actions
