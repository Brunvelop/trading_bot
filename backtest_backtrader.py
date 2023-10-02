import backtrader as bt
import math

class SuperStrategy(bt.Strategy):
    params = (
        ('ma_period', 10),
        ('range_period', 10),
        ('range_mult', 100),
        ('lookback_period', 300),
    )

    def __init__(self):
        # Calculate moving averages
        self.ma10 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_period)
        self.ma50 = bt.indicators.SimpleMovingAverage(self.data.close, period=50)
        self.ma100 = bt.indicators.SimpleMovingAverage(self.data.close, period=100)
        self.ma200 = bt.indicators.SimpleMovingAverage(self.data.close, period=200)

        # Calculate bar range as percentage of closing price
        self.bar_range = bt.indicators.TrueRange(self.data) / self.data.close * self.params.range_mult

        # Calculate exponential moving averages of bar range
        self.avg_range10 = bt.indicators.ExponentialMovingAverage(self.bar_range, period=self.params.range_period)
        self.avg_range50 = bt.indicators.ExponentialMovingAverage(self.bar_range, period=50)
        self.avg_range100 = bt.indicators.ExponentialMovingAverage(self.bar_range, period=100)
        self.avg_range200 = bt.indicators.ExponentialMovingAverage(self.bar_range, period=200)

        # Calculate the maximum and minimum of the last 300 bars, excluding the current bar
        self.max300 = bt.indicators.Highest(self.data.close(-1), period=self.params.lookback_period)
        self.min300 = bt.indicators.Lowest(self.data.close(-1), period=self.params.lookback_period)

    def next(self):
        # Define the strategy
        close_less_than_min_ma = self.data.close[0] < min(self.ma10[0], self.ma50[0], self.ma100[0], self.ma200[0])
        close_greater_than_max_ma = self.data.close[0] > max(self.ma10[0], self.ma50[0], self.ma100[0], self.ma200[0])
        ma_increasing = self.ma10[0] < self.ma50[0] and self.ma50[0] < self.ma100[0] and self.ma100[0] < self.ma200[0]
        ma_decreasing = self.ma10[0] > self.ma50[0] and self.ma50[0] > self.ma100[0] and self.ma100[0] > self.ma200[0]

        # Add conditions to break the maximum or minimum of the last 300 bars
        volatility_down = self.avg_range10[0] < self.avg_range50[0] and self.avg_range50[0] < self.avg_range100[0] and self.avg_range100[0] < self.avg_range200[0]
        volatility_up = self.avg_range10[0] > self.avg_range50[0] and self.avg_range50[0] > self.avg_range100[0] and self.avg_range100[0] > self.avg_range200[0]

        break_max_300 = self.data.close[0] > self.max300[0]
        break_min_300 = self.data.close[0] < self.min300[0]

        sell_signal = break_min_300 and volatility_down
        sell_signal_super = break_min_300 and volatility_up
        buy_signal = break_max_300 and volatility_up

        if sell_signal:
            self.sell()
        elif sell_signal_super:
            self.sell()
        elif buy_signal:
            self.buy()
