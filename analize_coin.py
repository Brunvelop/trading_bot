from tqdm import tqdm
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

import yfinance as yf

def download_currency_data(currency='BTC', days_to_download=30, interval='1h'):
    end = datetime.today()
    start = end - timedelta(days=days_to_download)
    data = yf.download(f'{currency}-USD', start=start, end=end, interval=interval)
    if data.empty:
        print(f"Error occurred: No data was downloaded for {currency}")
    else:
        data = data.drop_duplicates().sort_index()
    return data


def calculate_strategy_1(data):
    # Calculate the 200 hour moving average
    data['MA200'] = data['Close'].rolling(window=200).mean()

    # Define the strategy
    data['Buy_Signal'] = (data['Close'] < data['MA200'])
    data['Sell_Signal'] = (data['Close'] > data['MA200'])
    return data

def backtest(data, usd_balance=10000.0, coin_balance=0.0, buy_amount=10):
    trade_history = []
    order_id = 0
    open_orders = []

    for i, row in tqdm(data.iterrows(), total=data.shape[0]):
        # If there is a buy signal, we buy one unit of coin
        if row['Buy_Signal'] and usd_balance >= buy_amount:
            coin_amount = buy_amount/row['Close']
            usd_amount = buy_amount

            coin_balance += coin_amount
            usd_balance -= usd_amount
            trade = {
                'order_id': order_id, 
                'buy_timestamp': row.name, 
                'buy_price': row['Close'], 
                'buy_amount': coin_amount, 
                'buy_cost': usd_amount, 
                'buy_fees': 0, 
                'closed': False
            }
            trade_history.append(trade)
            open_orders.append(trade)
            order_id += 1

        # If there is a sell signal and we have coin balance, we sell
        elif row['Sell_Signal'] and coin_balance > 0:
            # Find the oldest purchase with at least 2% profitability
            for trade in open_orders:
                if row['Close'] > trade['buy_price'] * 1.02:
                    coin_amount = trade['buy_amount']
                    usd_amount = coin_amount * row['Close']
                    usd_balance += usd_amount
                    coin_balance -= coin_amount
                    trade.update({
                        'sell_timestamp': row.name,
                        'sell_price': row['Close'],
                        'sell_amount': coin_amount,
                        'sell_cost': usd_amount,
                        'sell_fees': 0,
                        'closed': True
                    })
                    open_orders.remove(trade)
                    break

    trade_history = pd.DataFrame(trade_history)
    return usd_balance, coin_balance, trade_history

def plot(trade_history, coin_data_1h, coin):
    fig, axs = plt.subplots(4, 1, figsize=(10, 24))  # Increase the number of subplots
    fig.suptitle('Trade History Over Time')

    # Filter closed trades
    closed_trades = trade_history[trade_history['closed']]

    axs[0].plot(trade_history['buy_timestamp'], trade_history['buy_cost'], label='Buy Cost Over Time', color='blue')
    axs[0].set(ylabel='Buy Cost')
    axs[0].grid(True)
    axs[0].legend()

    axs[1].plot(closed_trades['sell_timestamp'], closed_trades['sell_cost'], label='Sell Cost Over Time', color='green')
    axs[1].set(ylabel='Sell Cost')
    axs[1].grid(True)
    axs[1].legend()

    axs[2].plot(coin_data_1h.index, coin_data_1h['Close'], label=f'{coin}-USD Close Price', color='blue')
    axs[2].plot(coin_data_1h.index, coin_data_1h['MA200'], label='200 Minute MA', color='red')
    axs[2].plot(coin_data_1h[coin_data_1h['Buy_Signal']].index, coin_data_1h['Close'][coin_data_1h['Buy_Signal']], '^', markersize=3, color='g', label='buy')
    axs[2].plot(coin_data_1h[coin_data_1h['Sell_Signal']].index, coin_data_1h['Close'][coin_data_1h['Sell_Signal']], 'v', markersize=3, color='r', label='sell')
    axs[2].set(xlabel='Date', ylabel='Close Price')
    axs[2].grid(True)
    axs[2].legend()

    # Calculate balances
    usd_balance = 10000 - trade_history['buy_cost'].cumsum() + trade_history['sell_cost'].cumsum()
    coin_balance = trade_history['buy_amount'].cumsum() - trade_history['sell_amount'].cumsum()

    # Filter rows with valid sell_timestamp
    valid_sell_timestamps = trade_history['sell_timestamp'].notna()

    # New subplot for balance evolution
    axs[3].plot(trade_history['buy_timestamp'], usd_balance, label='USD Balance Over Time', color='purple')
    axs[3].plot(trade_history.loc[valid_sell_timestamps, 'sell_timestamp'], coin_balance[valid_sell_timestamps], label='BTC Balance Over Time', color='orange')
    axs[3].set(ylabel='Balance')
    axs[3].grid(True)
    axs[3].legend()

    plt.show()

import matplotlib.dates as mdates

def plot_trade_history(trade_history, coin_data_1h, coin):
    fig, ax = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

    # Convert Timestamp to datetime
    trade_history['buy_timestamp'] = pd.to_datetime(trade_history['buy_timestamp']).dt.to_pydatetime()
    trade_history['sell_timestamp'] = pd.to_datetime(trade_history['sell_timestamp']).dt.to_pydatetime()

    # Filter out NaT values
    valid_sell_timestamps = trade_history['sell_timestamp'].notna()

    # Plot strategy on the same graph
    ax[0].plot(coin_data_1h.index, coin_data_1h['Close'], label=f'{coin}-USD Close Price', color='blue')
    ax[0].plot(coin_data_1h.index, coin_data_1h['MA200'], label='200 Minute MA', color='red')
    ax[0].plot(coin_data_1h[coin_data_1h['Buy_Signal']].index, coin_data_1h['Close'][coin_data_1h['Buy_Signal']], '^', markersize=3, color='g', label='buy')
    ax[0].plot(coin_data_1h[coin_data_1h['Sell_Signal']].index, coin_data_1h['Close'][coin_data_1h['Sell_Signal']], 'v', markersize=3, color='r', label='sell')
    ax[0].set(xlabel='Date', ylabel='Close Price')
    ax[0].grid(True)
    ax[0].legend()

    # Set x-axis to display hourly ticks
    ax[0].xaxis.set_major_locator(mdates.HourLocator(interval=1))  # set ticks to display every hour
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # set ticks format to display hour and minute

    # Plot buy and sell amounts on the first graph
    ax[1].bar(trade_history['buy_timestamp'], trade_history['buy_amount'], label='Coin Amount Bought Over Time', color='green')
    # ax[1].bar(trade_history.loc[valid_sell_timestamps, 'sell_timestamp'], trade_history.loc[valid_sell_timestamps, 'sell_amount'], label='Coin Amount Sold Over Time', color='orange')
    ax[1].set(ylabel='Coin Amount')
    ax[1].grid(True)
    ax[1].legend()

    # Set x-axis to display hourly ticks
    ax[1].xaxis.set_major_locator(mdates.HourLocator(interval=1))  # set ticks to display every hour
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # set ticks format to display hour and minute

    plt.tight_layout()
    plt.show()

coin = 'BTC'
coin_data_1h = download_currency_data(coin, days_to_download=20, interval='1h')
coin_data_1h = calculate_strategy_1(coin_data_1h)

usd_balance, coin_balance, trade_history = backtest(coin_data_1h)

plot_trade_history(trade_history,coin_data_1h, coin)


