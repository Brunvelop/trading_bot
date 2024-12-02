from enum import Enum, auto
from datetime import datetime
from typing import Tuple, List
from abc import ABC, abstractmethod
import numpy as np

from indicators import Indicators
from definitions import Action, Memory, MarketData, TradingPhase


class Strategy(ABC):
    @abstractmethod
    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        pass # :return: [(action1, price1, quantity1), (action2, price2, quantity2), ...]

    def calculate_indicators(data: MarketData):
        pass # return : 

class MovingAverageStrategy(Strategy):
    def __init__(self, window_size: int = 200, cost: float = 10) -> None:
        self.window_size = window_size
        self.cost = cost

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []

        moving_average = Indicators.calculate_moving_average(data, self.window_size)['result'].iloc[-1]
        balance_b = memory.get('balance_b', 0)
        current_price = data['close'].iloc[-1]
        quantity = self.cost / current_price

        if current_price < moving_average:
            actions.append((Action.BUY_MARKET, current_price, quantity))
        elif current_price > moving_average and balance_b > quantity:
            actions.append((Action.SELL_MARKET, current_price, quantity))
        else:
            actions.append((Action.WAIT, None, None))

        return actions
    
class MultiMovingAverageStrategy(Strategy):
    class Alignment(Enum):
        UP = auto()
        DOWN = auto()
        NONE = auto()

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

    def run(self, data: MarketData, memory: Memory) -> List[Action]:
        actions = []
        balance_a, balance_b = memory.get('balance_a', 0), memory.get('balance_b', 0)
        current_price = data['close'].iloc[-1]

        alignment = self._determine_alignment(data)
        amount = self._calculate_amount(balance_a, balance_b, current_price)

        if self.trading_phase == TradingPhase.ACCUMULATION:
            if alignment == self.Alignment.UP and self._can_sell(balance_a, amount):
                self.acumulation_length -=1
                actions.append((Action.SELL_MARKET, current_price, amount))
            elif alignment == self.Alignment.DOWN and self._can_buy(balance_b, amount, current_price):
                self.acumulation_length +=1
                actions.append((Action.BUY_MARKET, current_price, amount))
        elif self.trading_phase == TradingPhase.DISTRIBUTION:
            if alignment == self.Alignment.UP and self._can_sell(balance_a, amount):
                self.distribution_length +=1
                actions.append((Action.SELL_MARKET, current_price, amount))
            elif alignment == self.Alignment.DOWN and self._can_buy(balance_b, amount, current_price):
                self.distribution_length -=1
                actions.append((Action.BUY_MARKET, current_price, amount))
        else:
            actions.append((Action.WAIT, None, None))

        if self.debug:
            print("time:", datetime.fromtimestamp(int(data['date'].iloc[-1]) / 1000).strftime('%Y-%m-%d %H:%M'))
            print(self.trading_phase)
            print(alignment)
            print("blance_a:", balance_a,"|", "balance_b:", balance_b)
            print("distribution_n:", self.distribution_length, "acumulation_n:", self.acumulation_length)
            print("can_sell:", self._can_sell(balance_a, amount),"|", "can_buy:", self._can_buy(balance_a, amount, current_price))
            print("amount:", amount)
            print("amount_price:", amount * current_price)
            print(actions)

        return actions
    
    def calculate_indicators(self, data: MarketData):
        return [Indicators.calculate_moving_average(data, window) for window in self.windows]

    def _determine_alignment(self, data: MarketData) -> Alignment:
        moving_averages = self.calculate_indicators(data)
        current_price = data['close'].iloc[-1]
        
        if (current_price > moving_averages[0]['result'].iloc[-1] > 
            moving_averages[1]['result'].iloc[-1] > 
            moving_averages[2]['result'].iloc[-1] > 
            moving_averages[3]['result'].iloc[-1]):
            return self.Alignment.UP
        elif (current_price < moving_averages[0]['result'].iloc[-1] < 
            moving_averages[1]['result'].iloc[-1] < 
            moving_averages[2]['result'].iloc[-1] < 
            moving_averages[3]['result'].iloc[-1]):
            return self.Alignment.DOWN
        return self.Alignment.NONE

    def _calculate_amount(self, balance_a: float, balance_b: float, current_price: float) -> float:
        if self.trading_phase == TradingPhase.NEUTRAL:
            return 0
        elif self.trading_phase == TradingPhase.ACCUMULATION:
            amount = balance_b / (self.max_duration * self.safety_margin * current_price)
        elif self.trading_phase == TradingPhase.DISTRIBUTION:
            amount = balance_a / ( self.max_duration * self.safety_margin )

        return max(amount, self.min_purchase / current_price)

    def _can_sell(self, balance_a: float, amount: float) -> bool:
        enough_amount_to_sell = balance_a > amount
        if self.trading_phase == TradingPhase.ACCUMULATION:
            return enough_amount_to_sell and self.acumulation_length > 0
        elif self.trading_phase == TradingPhase.DISTRIBUTION:
            return enough_amount_to_sell 
        return enough_amount_to_sell
    
    def _can_buy(self, balance_b: float, amount: float, current_price: float) -> bool:
        enough_amount_to_buy = balance_b > amount * current_price
        if self.trading_phase == TradingPhase.ACCUMULATION:
            return enough_amount_to_buy 
        elif self.trading_phase == TradingPhase.DISTRIBUTION:
            return enough_amount_to_buy and self.distribution_length > 0
        return enough_amount_to_buy

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
