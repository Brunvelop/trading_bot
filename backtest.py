from trader import KrakenAPI
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

import yfinance as yf

# Download historical data for BTC
end = datetime.today()
start = end - timedelta(days=730)
btc = yf.download('BTC-USD', start=start, end=end, interval='1h')

# Calculate the 200 hour moving average
btc['MA200'] = btc['Close'].rolling(window=200).mean()

# Define the strategy
btc['Buy_Signal'] = (btc['Close'] < btc['MA200'])
btc['Sell_Signal'] = (btc['Close'] > btc['MA200'])

# Plot the closing prices and moving average
plt.figure(figsize=(10, 6))
plt.plot(btc.index, btc['Close'], label='BTC-USD Close Price', color='blue')
plt.plot(btc.index, btc['MA200'], label='200 Hour MA', color='red')

# Plot the buy signals
plt.plot(btc[btc['Buy_Signal']].index, btc['Close'][btc['Buy_Signal']], '^', markersize=10, color='g', label='buy')

# Plot the sell signals
plt.plot(btc[btc['Sell_Signal']].index, btc['Close'][btc['Sell_Signal']], 'v', markersize=10, color='r', label='sell')

plt.xlabel('Date')
plt.ylabel('Close Price')
plt.title('BTC-USD Close Price with Buy/Sell Signals')
plt.grid(True)
plt.legend()
plt.show()
