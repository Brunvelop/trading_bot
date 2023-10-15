import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trader import KrakenAPI
from db import DB


def get_data_from_db():
    db = DB()
    all_orders = db.get_all_orders().data
    return all_orders

def get_last_position():
    db = DB()
    all_orders = db.get_open_trades_with_highest_position()
    return all_orders

def get_current_trades():
    db = DB()
    all_orders = db.get_current_trades()
    return all_orders


def get_bars_from_api():
    kraken_api = KrakenAPI()
    bars = kraken_api.get_bars('BTC/EUR', '15m', 500)
    return bars


def extract_prices_and_timestamps(bars):

    return prices, timestamps


def calculate_mid_buy_price(buy_prices):
    mid_buy_price = sum(buy_prices) / len(buy_prices)
    return mid_buy_price


def find_first_buy_timestamp(buy_timestamps):
    first_buy_timestamp = min(buy_timestamps)
    return first_buy_timestamp


def calculate_xmin(first_buy_timestamp, timestamps):
    xmin = (first_buy_timestamp - min(timestamps)) / (max(timestamps) - min(timestamps))
    return xmin


def plot_graph(timestamps, prices, buy_timestamps, buy_prices, mid_buy_price):
    plt.figure(figsize=(14, 7))
    plt.plot(timestamps, prices, label='Precio de BTC')
    plt.plot(buy_timestamps, buy_prices, '^', markersize=3, color='g', label='Puntos de compra')
    plt.axhline(y=mid_buy_price, color='g', linestyle='-', label='Punto medio de compra')
    plt.text(max(timestamps), mid_buy_price, 'PM: {:.2f}'.format(mid_buy_price), verticalalignment='bottom', horizontalalignment='left')
    plt.legend()
    plt.show()



import pandas as pd

bars = get_bars_from_api()
prices = [bar[4] for bar in bars]
timestamps = [bar[0] for bar in bars]

all_orders = get_data_from_db()
df = pd.DataFrame(all_orders)
df.to_csv('analisys/all_orders.csv', index=False)

buy_prices = [order['buy_price'] for order in all_orders]
buy_timestamps = [int(datetime.strptime(order['buy_timestamp'], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000) for order in all_orders]
mid_buy_price = calculate_mid_buy_price(buy_prices)
first_buy_timestamp = find_first_buy_timestamp(buy_timestamps)
xmin = calculate_xmin(first_buy_timestamp, timestamps)

plot_graph(timestamps, prices, buy_timestamps, buy_prices, mid_buy_price)