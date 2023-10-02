import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.test import SMA

import yfinance as yf
from datetime import datetime, timedelta


def Highest(series, n):
    return pd.Series(series).rolling(n).max()

def Lowest(series, n):
    return pd.Series(series).rolling(n).min()

# def SMA(array, n):
#     return sma(array, n)

def download_currency_data(currency='BTC', days_to_download=30, interval='1h'):
    end = datetime.today()
    start = end - timedelta(days=days_to_download)
    data = yf.download(f'{currency}-USD', start=start, end=end, interval=interval)
    if data.empty:
        print(f"Error occurred: No data was downloaded for {currency}")
    else:
        data = data.drop_duplicates().sort_index()
    return data

class SuperStrategy(Strategy):
    ma_period = 10
    range_period = 10
    range_mult = 100
    lookback_period = 300
    stop_loss_period = 10

    def init(self):
        # Calculate moving averages
        self.ma10 = self.I(SMA, self.data.Close, 10)
        self.ma50 = self.I(SMA, self.data.Close, 50)
        self.ma100 = self.I(SMA, self.data.Close, 100)
        self.ma200 = self.I(SMA, self.data.Close, 200)

        # Calculate bar range as percentage of closing price
        self.bar_range = (self.data.High - self.data.Low) / self.data.Close * self.range_mult

        # Calculate exponential moving averages of bar range
        self.avg_range10 = self.I(SMA, self.bar_range, 10)
        self.avg_range50 = self.I(SMA, self.bar_range, 50)
        self.avg_range100 = self.I(SMA, self.bar_range, 100)
        self.avg_range200 = self.I(SMA, self.bar_range, 200)

        # Calculate the maximum and minimum of the last 300 bars, excluding the current bar
        self.max300 = self.I(Highest, self.data.Close, self.lookback_period)
        self.min300 = self.I(Lowest, self.data.Close, self.lookback_period)

        # Calculate the maximum and minimum of the last 10 bars for stop loss and take profit
        self.max10 = self.I(Highest, self.data.Close, self.stop_loss_period)
        self.min10 = self.I(Lowest, self.data.Close, self.stop_loss_period)

    def next(self):
        # Add conditions to break the maximum or minimum of the last 300 bars
        volatility_up = self.avg_range10 > self.avg_range50 and self.avg_range50 > self.avg_range100 and self.avg_range100 > self.avg_range200

        break_max_300 = self.data.Close > self.max300
        break_min_300 = self.data.Close < self.min300

        sell_signal = break_min_300 and volatility_up
        buy_signal = break_max_300 and volatility_up

        # If there is a sell signal, sell and set the stop loss and take profit
        if sell_signal and not self.position:
            self.sell()
            stop_loss_price = self.max10
            take_profit_price = self.data.Close + (self.data.Close - stop_loss_price)

        # If there is a buy signal, buy and set the stop loss and take profit
        elif buy_signal and not self.position:
            self.buy()
            stop_loss_price = self.min10
            take_profit_price = self.data.Close + (self.data.Close - stop_loss_price)

if __name__ == '__main__':
    data = download_currency_data('BTC', 60, '15m')
    bt = Backtest(data, SuperStrategy, cash=100000, commission=.002)
    stats = bt.run()
    bt.plot()
