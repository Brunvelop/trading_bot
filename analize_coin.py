from tqdm import tqdm
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

import yfinance as yf

def download_currency_data(currency, days_to_download=30, interval='1m'):
    end = datetime.today()
    start = end - timedelta(days=7) if interval == '1m' else end - timedelta(days=730)
    data = pd.DataFrame()

    while (end - start).days <= days_to_download:
        downloaded_data = yf.download(f'{currency}-USD', start=start, end=end, interval=interval)
        if downloaded_data.empty:
            print(f"Error occurred: No data was downloaded for {currency}")
            break
        data = pd.concat([data, downloaded_data])
        end = start
        start = end - timedelta(days=7 if interval == '1m' else 730)

    data = data.drop_duplicates().sort_index()
    return data


def calculate_strategy_1(data):
    # Calculate the 200 hour moving average
    data['MA200'] = data['Close'].rolling(window=200).mean()

    # Define the strategy
    data['Buy_Signal'] = (data['Close'] < data['MA200'])
    data['Sell_Signal'] = (data['Close'] > data['MA200'])
    return data

def backtest(data, usd_balance=10000.0, coin_balance=0.0, buy_amount=100):
    trade_history = pd.DataFrame(columns=['order_id', 'buy_timestamp', 'buy_price', 'buy_amount', 'buy_cost', 'buy_fees', 'closed', 'sell_timestamp', 'sell_price', 'sell_amount', 'sell_cost', 'sell_fees'])
    fee_rate = 0.0012  # 0.12% fee
    order_id = 0
    for i, row in tqdm(data.iterrows(), total=data.shape[0]):
        # If there is a buy signal, we buy one unit of coin
        if row['Buy_Signal'] and usd_balance >= buy_amount/row['Close']:
            coin_amount = buy_amount/row['Close']
            usd_amount = buy_amount
            fee = usd_amount * fee_rate
            coin_balance += coin_amount
            usd_balance -= usd_amount + fee
            trade_history = trade_history.append(
                {
                    'order_id': order_id, 
                    'buy_timestamp': row.name, 
                    'buy_price': row['Close'], 
                    'buy_amount': coin_amount, 
                    'buy_cost': usd_amount, 
                    'buy_fees': fee, 
                    'closed': False
                }, 
                ignore_index=True
            )
            order_id += 1

        # If there is a sell signal and we have coin balance, we sell
        elif row['Sell_Signal'] and coin_balance > 0:
            # Find the oldest purchase with at least 2% profitability
            for j, trade in trade_history.iterrows():
                if not trade['closed'] and row['Close'] > trade['buy_price'] * 1.02:
                    coin_amount = trade['buy_amount']
                    usd_amount = coin_amount * row['Close']
                    fee = usd_amount * fee_rate
                    usd_balance += usd_amount - fee
                    coin_balance -= coin_amount
                    trade_history.loc[j, 'sell_timestamp'] = row.name
                    trade_history.loc[j, 'sell_price'] = row['Close']
                    trade_history.loc[j, 'sell_amount'] = coin_amount
                    trade_history.loc[j, 'sell_cost'] = usd_amount
                    trade_history.loc[j, 'sell_fees'] = fee
                    trade_history.loc[j, 'closed'] = True
                    break
            
    return usd_balance, coin_balance, trade_history

coin = 'BTC'
coin_data_1h = download_currency_data(coin, days_to_download=730, interval='1m')
coin_data_1h = calculate_strategy_1(coin_data_1h)
usd_balance, coin_balance, trade_history = backtest(coin_data_1h)

fig, axs = plt.subplots(3, 1, figsize=(10, 18))
fig.suptitle('USD and Coin Balance Over Time')

axs[0].plot(balance_history['Date'], balance_history['USD_Balance'], label='USD Balance Over Time', color='blue')
axs[0].set(ylabel='USD Balance')
axs[0].grid(True)
axs[0].legend()

axs[1].plot(balance_history['Date'], balance_history['Coin_Balance'], label='Coin Balance Over Time', color='green')
axs[1].set(ylabel='Coin Balance')
axs[1].grid(True)
axs[1].legend()

axs[2].plot(coin_data_1h.index, coin_data_1h['Close'], label=f'{coin}-USD Close Price', color='blue')
axs[2].plot(coin_data_1h.index, coin_data_1h['MA200'], label='200 Minute MA', color='red')  # Changed label to '200 Minute MA'
axs[2].plot(coin_data_1h[coin_data_1h['Buy_Signal']].index, coin_data_1h['Close'][coin_data_1h['Buy_Signal']], '^', markersize=3, color='g', label='buy')
axs[2].plot(coin_data_1h[coin_data_1h['Sell_Signal']].index, coin_data_1h['Close'][coin_data_1h['Sell_Signal']], 'v', markersize=3, color='r', label='sell')
axs[2].set(xlabel='Date', ylabel='Close Price')
axs[2].grid(True)
axs[2].legend()

plt.show()

