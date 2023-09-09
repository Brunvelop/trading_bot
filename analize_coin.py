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
    trade_history = []
    fee_rate = 0.0012  # 0.12% fee
    order_id = 0
    open_orders = []

    for i, row in tqdm(data.iterrows(), total=data.shape[0]):
        fee = buy_amount * fee_rate
        # If there is a buy signal, we buy one unit of coin
        if row['Buy_Signal'] and usd_balance >= (buy_amount + fee):
            buy_amount -= fee
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
                'buy_fees': fee, 
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
                    fee = usd_amount * fee_rate
                    usd_balance += usd_amount - fee
                    coin_balance -= coin_amount
                    trade.update({
                        'sell_timestamp': row.name,
                        'sell_price': row['Close'],
                        'sell_amount': coin_amount,
                        'sell_cost': usd_amount,
                        'sell_fees': fee,
                        'closed': True
                    })
                    open_orders.remove(trade)
                    break

    trade_history = pd.DataFrame(trade_history)
    return usd_balance, coin_balance, trade_history

def plot_trade_history(trade_history, coin_data_1h, coin):
    fig, axs = plt.subplots(3, 1, figsize=(10, 18))
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

    plt.show()

coin = 'BTC'
coin_data_1h = download_currency_data(coin, days_to_download=730, interval='1h')
coin_data_1h = calculate_strategy_1(coin_data_1h)

usd_balance, coin_balance, trade_history = backtest(coin_data_1h)

plot_trade_history(trade_history, coin_data_1h, coin)


