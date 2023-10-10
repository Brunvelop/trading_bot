from datetime import datetime
import matplotlib.pyplot as plt

from trader2 import KrakenAPI
from db import DB


def get_data_from_db():
    db = DB()
    all_orders = db.get_all_orders().data
    return all_orders


def get_bars_from_api():
    kraken_api = KrakenAPI()
    bars = kraken_api.get_bars('BTC/EUR', '15m', 500)
    return bars


def extract_prices_and_timestamps(bars):
    prices = [bar[4] for bar in bars]
    timestamps = [bar[0] for bar in bars]
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


def plot_graph(timestamps, prices, buy_timestamps, buy_prices, mid_buy_price, xmin):
    plt.figure(figsize=(14, 7))
    plt.plot(timestamps, prices, label='Precio de BTC')
    plt.plot(buy_timestamps, buy_prices, '^', markersize=3, color='g', label='Puntos de compra')
    plt.axhline(y=mid_buy_price, color='g', linestyle='-', label='Punto medio de compra', xmin=xmin)
    plt.text(max(timestamps), mid_buy_price, 'PM: {:.2f}'.format(mid_buy_price), verticalalignment='bottom', horizontalalignment='left')
    plt.legend()
    plt.show()



all_orders = get_data_from_db()
bars = get_bars_from_api()
prices, timestamps = extract_prices_and_timestamps(bars)
buy_prices = [order['buy_price'] for order in all_orders]
buy_timestamps = [int(datetime.strptime(order['buy_timestamp'], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000) for order in all_orders]
mid_buy_price = calculate_mid_buy_price(buy_prices)
first_buy_timestamp = find_first_buy_timestamp(buy_timestamps)
xmin = calculate_xmin(first_buy_timestamp, timestamps)

plot_graph(timestamps, prices, buy_timestamps, buy_prices, mid_buy_price, xmin)