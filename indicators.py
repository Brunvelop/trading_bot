from typing import Type

import pandas as pd

from definitions import MarketData

class Indicators:
    
    def calculate_max(self, data, period=300):
        max_value = data['close'][-(period+1):-2].max()
        return max_value

    def calculate_min(self, data, period=300):
        min_value = data['close'][-(period+1):-2].min()
        return min_value


    def calculate_std_dev_and_avg_range(self, data, window=200):
        volatility = self.calculate_volatility(data)
        avg_range = volatility.ewm(span=window).mean()
        std_dev = avg_range.rolling(window=window).std()
        return volatility, std_dev, avg_range


    def calculate_volatility(self, data):
        volatility = (data['high'] - data['low']).abs() / data['low'] * 100
        return volatility

    def calculate_avg_volatility(self, volatility, span):
        avg_volatility = volatility.ewm(span=span, adjust=False).mean()
        return avg_volatility
    
    @staticmethod
    def calculate_moving_average(data: Type[MarketData], window: int) -> pd.Series:
        return data['close'].rolling(window=window).mean()