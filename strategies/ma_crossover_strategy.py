from typing import Tuple, List
from definitions import Action, Memory, MarketData
from indicators import Indicators, Indicator
from strategies.strategy import Strategy
import numpy as np

class MACrossoverStrategy(Strategy):
    def calculate_indicators(self, data: MarketData) -> List[Indicator]:
        ma_200 = Indicators.calculate_moving_average(data, 200)
        ma_50 = Indicators.calculate_moving_average(data, 50)
        return [ma_200, ma_50]

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        # Calculate indicators
        indicators = self.calculate_indicators(data)
        ma_200 = indicators[0].result
        ma_50 = indicators[1].result
        
        # Get current price
        current_price = data['close'].iloc[-1]
        
        # Check for crossovers using the last two periods
        if len(ma_200) < 2 or len(ma_50) < 2:
            return [(Action.WAIT, 0, 0)]
            
        prev_ma_200 = ma_200.iloc[-2]
        prev_ma_50 = ma_50.iloc[-2]
        curr_ma_200 = ma_200.iloc[-1]
        curr_ma_50 = ma_50.iloc[-1]
        
        # Bullish crossover (MA50 crosses above MA200)
        if prev_ma_50 <= prev_ma_200 and curr_ma_50 > curr_ma_200:
            # Buy with all available balance_b
            quantity = memory.balance_b / current_price
            if quantity > 0:
                return [(Action.BUY_MARKET, current_price, quantity)]
                
        # Bearish crossover (MA50 crosses below MA200)
        elif prev_ma_50 >= prev_ma_200 and curr_ma_50 < curr_ma_200:
            # Sell all available balance_a
            quantity = memory.balance_a
            if quantity > 0:
                return [(Action.SELL_MARKET, current_price, quantity)]
        
        return [(Action.WAIT, np.float64(0), np.float64(0))]
