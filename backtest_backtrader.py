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
        ('stop_loss_period', 10),
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
        self.avg_range10 = bt.indicators.SimpleMovingAverage(self.bar_range, period=self.params.range_period)
        self.avg_range50 = bt.indicators.SimpleMovingAverage(self.bar_range, period=50)
        self.avg_range100 = bt.indicators.SimpleMovingAverage(self.bar_range, period=100)
        self.avg_range200 = bt.indicators.SimpleMovingAverage(self.bar_range, period=200)

        # Calculate the maximum and minimum of the last 300 bars, excluding the current bar
        self.max300 = bt.indicators.Highest(self.data.close(-1), period=self.params.lookback_period)
        self.min300 = bt.indicators.Lowest(self.data.close(-1), period=self.params.lookback_period)

        # Calculate the maximum and minimum of the last 10 bars for stop loss and take profit
        self.max10 = bt.indicators.Highest(self.data.close(-1), period=self.params.stop_loss_period)
        self.min10 = bt.indicators.Lowest(self.data.close(-1), period=self.params.stop_loss_period)

        # Initialize order and stop loss order to None
        self.order = None
        self.stop_loss_order = None
        self.take_profit_order = None

    def next(self):
        # Add conditions to break the maximum or minimum of the last 300 bars
        volatility_up = self.avg_range10[0] > self.avg_range50[0] and self.avg_range50[0] > self.avg_range100[0] and self.avg_range100[0] > self.avg_range200[0]

        break_max_300 = self.data.close[0] > self.max300[0]
        break_min_300 = self.data.close[0] < self.min300[0]

        sell_signal = break_min_300 and volatility_up
        buy_signal = break_max_300 and volatility_up

        # If there is an open order, do nothing
        if self.order:
            return

        # If there is an open position and the stop loss or take profit has been hit, cancel the remaining orders
        if self.position and (self.stop_loss_order or self.take_profit_order):
            if self.stop_loss_order:
                self.cancel(self.stop_loss_order)
                self.stop_loss_order = None
            if self.take_profit_order:
                self.cancel(self.take_profit_order)
                self.take_profit_order = None
        else:
            # If there is a sell signal, sell and set the stop loss and take profit
            # Si hay una señal de venta, vende y establece el stop loss y el take profit
            if sell_signal:
                self.order = self.sell()
                print(f'Sell Order: Price {self.data.close[0]}')  # Add this line
                stop_loss_price = self.max10[0]
                print(f'Sell Order: Stop Loss set at {stop_loss_price}')  # Agregar esta línea
                self.stop_loss_order = self.sell(exectype=bt.Order.Stop, price=stop_loss_price)
                take_profit_price = self.data.close[0] + (self.data.close[0] - stop_loss_price)
                print(f'Sell Order: Take Profit set at {take_profit_price}')  # Agregar esta línea
                self.take_profit_order = self.sell(exectype=bt.Order.Limit, price=take_profit_price)

            # Si hay una señal de compra, compra y establece el stop loss y el take profit
            elif buy_signal:
                self.order = self.buy()
                print(f'Buy Order: Price {self.data.close[0]}')  # Add this line
                stop_loss_price = self.min10[0]
                print(f'Buy Order: Stop Loss set at {stop_loss_price}')  # Agregar esta línea
                self.stop_loss_order = self.buy(exectype=bt.Order.Stop, price=stop_loss_price)
                take_profit_price = self.data.close[0] + (self.data.close[0] - stop_loss_price)
                print(f'Buy Order: Take Profit set at {take_profit_price}')  # Agregar esta línea
                self.take_profit_order = self.buy(exectype=bt.Order.Limit, price=take_profit_price)

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
