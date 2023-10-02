import backtrader as bt
import math
import yfinance as yf
from datetime import datetime, timedelta

# Import the necessary module
from backtrader.feeds import PandasData

# Define a new class to include 'Volume' in the data feed
class PandasDataVolume(PandasData):
    lines = ('volume',)
    params = (('volume', -1),)



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
        # Add conditions to break the maximum or minimum of the last 300 bars
        volatility_up = self.avg_range10[0] > self.avg_range50[0] and self.avg_range50[0] > self.avg_range100[0] and self.avg_range100[0] > self.avg_range200[0]

        break_max_300 = self.data.close[0] > self.max300[0]
        break_min_300 = self.data.close[0] < self.min300[0]

        sell_signal = break_min_300 and volatility_up
        buy_signal = break_max_300 and volatility_up

        if sell_signal:
            self.sell()
        elif buy_signal:
            self.buy()

def download_currency_data(currency='BTC', days_to_download=30, interval='1h'):
    end = datetime.today()
    start = end - timedelta(days=days_to_download)
    data = yf.download(f'{currency}-USD', start=start, end=end, interval=interval)
    if data.empty:
        print(f"Error occurred: No data was downloaded for {currency}")
    else:
        data = data.drop_duplicates().sort_index()
    return data

# Create a cerebro instance
cerebro = bt.Cerebro()

# Add the strategy
cerebro.addstrategy(SuperStrategy)

# Load the BTC data
data = download_currency_data('BTC', 60, '15m')

# Convert the DataFrame to a DataFeed
data_feed = PandasDataVolume(dataname=data)

# Add the data to cerebro
cerebro.adddata(data_feed)


# Set the initial capital
cerebro.broker.setcash(100000)

# Set the commission
cerebro.broker.setcommission(commission=0.001)

# Print out the starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run over everything
cerebro.run()

# Print out the final result
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plot()