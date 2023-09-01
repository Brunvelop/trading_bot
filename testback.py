from trader import KrakenAPI
import time
from datetime import datetime, timedelta

kraken_api = KrakenAPI()
btc_usd = 'BTC/USD'

# Define the time period for historical data
end_time = datetime(2022, 12, 31)  # Last day of 2022
start_time = end_time - timedelta(days=30)  # Last month of 2022

# Fetch historical data in OHLCV (Open, High, Low, Close, Volume) format
exange = kraken_api.connect_api()
historical_data = exange.fetch_ohlcv(btc_usd, '1h', since=int(end_time.timestamp()), limit=2000)

from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Convert timestamp to datetime for plotting
dates = [mdates.date2num(datetime.fromtimestamp(data[0]/1000)) for data in historical_data]
high_prices = [data[2] for data in historical_data]
low_prices = [data[3] for data in historical_data]
open_prices = [data[1] for data in historical_data]
close_prices = [data[4] for data in historical_data]

# Plotting
fig, ax = plt.subplots()

ax.plot_date(dates, high_prices, '-', label='High Price')
ax.plot_date(dates, low_prices, '-', label='Low Price')
ax.plot_date(dates, open_prices, '-', label='Open Price')
ax.plot_date(dates, close_prices, '-', label='Close Price')

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.legend()

plt.show()
