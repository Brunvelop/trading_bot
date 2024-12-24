from enum import Enum, auto
from typing import Tuple, List
from collections import deque

import numpy as np
import pandas as pd

from definitions import Memory, MarketData
from indicators import Indicators, Indicator
from .strategy import Strategy, Action, ActionType

class AdaptiveMovingAverageStrategy(Strategy):
    class MarketCondition(Enum):
        STRONG_BULLISH = auto()
        BULLISH = auto()
        BEARISH = auto()
        STRONG_BEARISH = auto()
        NEUTRAL = auto()
    
    class TradingPhase(Enum):
        ACCUMULATION = auto()
        DISTRIBUTION = auto()
        NEUTRAL = auto()

    def __init__(self, 
            max_duration: int = 500,
            min_purchase: float = 5.1,
            safety_margin: float = 3,
            ma_windows: List[int] = [10, 50, 100, 200],
            rsi_window: int = 14,
            rsi_oversold: int = 30,
            rsi_overbought: int = 70,
            volume_window: int = 20,
            momentum_window: int = 10,
            condition_memory: int = 50,
            debug: bool = True
        ) -> None:
        self.max_duration = max_duration
        self.min_purchase = min_purchase
        self.safety_margin = safety_margin
        self.ma_windows = ma_windows
        self.rsi_window = rsi_window
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.volume_window = volume_window
        self.momentum_window = momentum_window
        self.distribution_length = 0
        self.accumulation_length = 0
        self.debug = debug
        
        # Market memory
        self.condition_memory = condition_memory
        self.recent_conditions = deque(maxlen=condition_memory)
        self.recent_volumes = deque(maxlen=condition_memory)
        self.trading_phase = self.TradingPhase.NEUTRAL

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []
        balance_a, balance_b = memory.balance_a, memory.balance_b
        current_price = data['close'].iloc[-1]

        # Update market analysis
        market_condition = self._analyze_market_condition(data)
        self.recent_conditions.append(market_condition)
        self.recent_volumes.append(data['volume'].iloc[-1])
        
        # Auto-detect trading phase
        self._update_trading_phase(data)
        
        amount = self._calculate_amount(balance_a, balance_b, current_price)

        if self.trading_phase == self.TradingPhase.ACCUMULATION:
            if market_condition in [self.MarketCondition.STRONG_BULLISH, self.MarketCondition.BULLISH] and self._can_sell(balance_a, amount):
                self.accumulation_length -= 1
                actions.append(Action(action_type=ActionType.SELL_MARKET, price=current_price, amount=amount))
            elif market_condition in [self.MarketCondition.STRONG_BEARISH, self.MarketCondition.BEARISH] and self._can_buy(balance_b, amount, current_price):
                self.accumulation_length += 1
                actions.append(Action(action_type=ActionType.BUY_MARKET, price=current_price, amount=amount))
        elif self.trading_phase == self.TradingPhase.DISTRIBUTION:
            if market_condition in [self.MarketCondition.STRONG_BULLISH, self.MarketCondition.BULLISH] and self._can_sell(balance_a, amount):
                self.distribution_length += 1
                actions.append(Action(action_type=ActionType.SELL_MARKET, price=current_price, amount=amount))
            elif market_condition in [self.MarketCondition.STRONG_BEARISH, self.MarketCondition.BEARISH] and self._can_buy(balance_b, amount, current_price):
                self.distribution_length -= 1
                actions.append(Action(action_type=ActionType.BUY_MARKET, price=current_price, amount=amount))
        else:
            actions.append(Action(action_type=ActionType.WAIT, price=current_price, amount=np.float64(0)))

        if self.debug:
            print("time:", str(data['date'].iloc[-1]))
            print("Market Condition:", market_condition)
            print("Trading Phase:", self.trading_phase)
            print("balance_a:", balance_a, "|", "balance_b:", balance_b)
            print("distribution_n:", self.distribution_length, "accumulation_n:", self.accumulation_length)
            print("can_sell:", self._can_sell(balance_a, amount), "|", "can_buy:", self._can_buy(balance_b, amount, current_price))
            print("amount:", amount)
            print("amount_price:", amount * current_price)
            print(actions)

        return actions

    def calculate_indicators(self, data: MarketData) -> List[Indicator]:
        indicators = []
        
        # Calculate Moving Averages
        for window in self.ma_windows:
            ma = Indicators.calculate_moving_average(data, window)
            indicators.append(ma)
        
        # Calculate RSI
        rsi = Indicators.calculate_rsi(data, self.rsi_window)
        indicators.append(rsi)
        
        # Calculate Volume SMA
        volume_sma = Indicators.calculate_volume_sma(data, self.volume_window)
        indicators.append(volume_sma)
        
        # Calculate Momentum indicators
        velocity = Indicators.calculate_velocity(data['close'], self.momentum_window)
        indicators.append(velocity)
        
        acceleration = Indicators.calculate_acceleration(velocity.result, self.momentum_window)
        indicators.append(acceleration)
        
        return indicators

    def _analyze_market_condition(self, data: MarketData) -> MarketCondition:
        indicators = self.calculate_indicators(data)
        
        # Get latest values
        ma_values = [ind.result.iloc[-1] for ind in indicators[:len(self.ma_windows)]]
        rsi = indicators[len(self.ma_windows)].result.iloc[-1]
        volume_sma = indicators[len(self.ma_windows) + 1].result.iloc[-1]
        velocity = indicators[len(self.ma_windows) + 2].result.iloc[-1]
        acceleration = indicators[len(self.ma_windows) + 3].result.iloc[-1]
        
        current_price = data['close'].iloc[-1]
        current_volume = data['volume'].iloc[-1]
        
        # Check moving average alignment
        ma_aligned_up = all(ma_values[i] > ma_values[i+1] for i in range(len(ma_values)-1))
        ma_aligned_down = all(ma_values[i] < ma_values[i+1] for i in range(len(ma_values)-1))
        
        # Strong bullish conditions
        if (ma_aligned_up and
            current_price > ma_values[0] and
            velocity > 0 and 
            acceleration > 0 and 
            rsi > self.rsi_overbought and
            current_volume > volume_sma):
            return self.MarketCondition.STRONG_BULLISH
            
        # Strong bearish conditions
        if (ma_aligned_down and
            current_price < ma_values[0] and
            velocity < 0 and 
            acceleration < 0 and 
            rsi < self.rsi_oversold and
            current_volume > volume_sma):
            return self.MarketCondition.STRONG_BEARISH
            
        # Bullish conditions
        if (current_price > ma_values[0] > ma_values[1] and 
            velocity > 0):
            return self.MarketCondition.BULLISH
            
        # Bearish conditions
        if (current_price < ma_values[0] < ma_values[1] and 
            velocity < 0):
            return self.MarketCondition.BEARISH
            
        return self.MarketCondition.NEUTRAL

    def _update_trading_phase(self, data: MarketData) -> None:
        if len(self.recent_conditions) < self.condition_memory:
            return
        
        # Count recent conditions
        bullish_count = sum(1 for c in self.recent_conditions 
                          if c in [self.MarketCondition.BULLISH, self.MarketCondition.STRONG_BULLISH])
        bearish_count = sum(1 for c in self.recent_conditions 
                          if c in [self.MarketCondition.BEARISH, self.MarketCondition.STRONG_BEARISH])
        
        # Calculate volume trend
        avg_volume = sum(self.recent_volumes) / len(self.recent_volumes)
        current_volume = data['volume'].iloc[-1]
        volume_increasing = current_volume > avg_volume
        
        # Phase detection logic
        bullish_ratio = bullish_count / self.condition_memory
        bearish_ratio = bearish_count / self.condition_memory
        
        if bullish_ratio > 0.6 and volume_increasing:
            self.trading_phase = self.TradingPhase.DISTRIBUTION
        elif bearish_ratio > 0.6 and volume_increasing:
            self.trading_phase = self.TradingPhase.ACCUMULATION
        elif abs(bullish_ratio - bearish_ratio) < 0.2:
            self.trading_phase = self.TradingPhase.NEUTRAL

    def _calculate_amount(self, balance_a: float, balance_b: float, current_price: float) -> float:
        if self.trading_phase == self.TradingPhase.NEUTRAL:
            return 0
        elif self.trading_phase == self.TradingPhase.ACCUMULATION:
            amount = balance_b / (self.max_duration * self.safety_margin * current_price)
        elif self.trading_phase == self.TradingPhase.DISTRIBUTION:
            amount = balance_a / (self.max_duration * self.safety_margin)

        return max(amount, self.min_purchase / current_price)

    def _can_sell(self, balance_a: float, amount: float) -> bool:
        enough_amount_to_sell = balance_a > amount
        if self.trading_phase == self.TradingPhase.ACCUMULATION:
            return enough_amount_to_sell and self.accumulation_length > 0
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
