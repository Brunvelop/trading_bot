from tqdm import tqdm
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
plt.plot(btc[btc['Buy_Signal']].index, btc['Close'][btc['Buy_Signal']], '^', markersize=3, color='g', label='buy')

# Plot the sell signals
plt.plot(btc[btc['Sell_Signal']].index, btc['Close'][btc['Sell_Signal']], 'v', markersize=3, color='r', label='sell')

plt.xlabel('Date')
plt.ylabel('Close Price')
plt.title('BTC-USD Close Price with Buy/Sell Signals')
plt.grid(True)
plt.legend()
plt.show()


# Initialize the balance in USD and BTC, and the purchases list
usd_balance = 1000.0
btc_balance = 0.0
purchases = []

# Iterate over each row in the DataFrame
for i, row in tqdm(btc.iterrows(), total=btc.shape[0]):
    # If there is a buy signal and we have enough USD balance, we buy
    if row['Buy_Signal'] and usd_balance >= row['Close']:
        btc_amount = usd_balance / row['Close']
        purchases.append({'price': row['Close'], 'date': i, 'btc_amount': btc_amount})
        usd_balance -= row['Close']
        btc_balance += btc_amount

    # If there is a sell signal, we sell the oldest purchase with at least a 1% gain
    elif row['Sell_Signal'] and purchases:
        for purchase in purchases:
            if row['Close'] > purchase['price'] * 1.01:
                usd_balance += purchase['btc_amount'] * row['Close']  # We add the value of the purchase plus the gain
                btc_balance -= purchase['btc_amount']
                purchases.remove(purchase)
                break

# Print the final balances
print("Final USD Balance: ", usd_balance)
print("Final BTC Balance: ", btc_balance)
