import os
from dotenv import load_dotenv

import time
import ccxt

from db import DB

load_dotenv()

class KrakenAPI:
    def __init__(self):
        pass

    def connect_api(self):
        exchange = ccxt.kraken({
            'apiKey': os.getenv('KRAKEN_API_KEY'),
            'secret': os.getenv('KRAKEN_API_SECRET'),
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })
        return exchange

    def get_latest_price(self, pair):
        exchange = self.connect_api()
        ticker = exchange.fetch_ticker(pair)
        return ticker['last']
    
    def get_account_balance(self, currency):
        exchange = self.connect_api()
        balance = exchange.fetch_balance()
        return balance['total'][currency]

    def get_bars(self, pair, timeframe, limit):
        exchange = self.connect_api()
        return exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)[::-1]

    def get_order(self, order_id):
        exchange = self.connect_api()
        return exchange.fetch_order(order_id)

    def create_order(self, pair, order_type, side, amount, price):
        exchange = self.connect_api()
        return exchange.create_order(pair, order_type, side, amount, price)

    def get_smas(self, bars, periods=(10, 50, 100, 200)):
        smas = []
        sma_totals = [0] * len(periods)
        max_period = max(periods)

        for i, bar in enumerate(bars[:max_period]):
            price = bar[1]
            for j, period in enumerate(periods):
                if i < period:
                    sma_totals[j] += price
                elif i == period:
                    smas.append(sma_totals[j] / period)

        return smas

    def get_order_book(self, pair):
        exchange = self.connect_api()
        orderbook = exchange.fetch_order_book(pair)
        return orderbook


class Trader:
    def __init__(self, pair='BTC/USD', cost=5, time_period='1h', gain_threshold=0.05):
        self.kraken_api = KrakenAPI()
        self.pair = pair
        self.cost = cost
        self.time_period = time_period
        self.gain_threshold = gain_threshold
        self.db = DB()

    def get_amount(self, price):
        return self.cost / price

    def run_strategy(self):
        bars = self.kraken_api.get_bars(self.pair, self.time_period, 200)
        sma_10, sma_50, sma_100, sma_200 = self.kraken_api.get_smas(bars)
        price = self.kraken_api.get_latest_price(self.pair)
        
        print("price:", price, "smas(10,50,100,200)=", sma_10, sma_50, sma_100, sma_200)
        if price > sma_10 > sma_50 > sma_100 > sma_200:
            print('Trying to sell...', flush=True)
            self.sell()
        elif price < sma_10 < sma_50 < sma_100 < sma_200:
            print('Buying...', flush=True)
            self.buy()
        else:
            print('Waiting...', flush=True)

    def buy(self):
        price = self.kraken_api.get_latest_price(self.pair)
        amount = self.get_amount(price)
        order = self.kraken_api.create_order(self.pair, 'market', 'buy', amount, price)
        order_executed_info = self.get_order_info(order['id'])
        self.db.insert_order(
                order_executed_info['id'],
                order_executed_info['timestamp'],
                order_executed_info['price'],
                order_executed_info['amount'],
                order_executed_info['cost'],
                order_executed_info['fees'],
                False
            )
        return self.get_order_info(order['id'])

    def sell(self):
        price = self.kraken_api.get_latest_price(self.pair)
        orders = self.db.get_orders_below(price*(1-self.gain_threshold))
        if orders:
            amount = orders[0][3]
            order = self.kraken_api.create_order(self.pair, 'market', 'sell', amount, price)
            order_info = self.get_order_info(order['id'])
            self.db.update_order(
                    orders[0][0],
                    order_info['timestamp'],
                    order_info['price'],
                    order_info['amount'],
                    order_info['cost'],
                    order_info['fees'],
            )
            return order_info
        return None

    def sell_to_market(self, order_id):
        order = self.db.get_order_by_id(order_id)[0]
        amount = order[3]
        price = self.kraken_api.get_latest_price(self.pair)
        order_new = self.kraken_api.create_order(self.pair, 'market', 'sell', amount, price)
        order_new_info = self.get_order_info(order_new['id'])
        self.db.update_order(
                    order_id,
                    order_new_info['timestamp'],
                    order_new_info['price'],
                    order_new_info['amount'],
                    order_new_info['cost'],
                    order_new_info['fees'],
            )
        return order_new_info

    def get_order_info(self, order_id):
        order = self.kraken_api.get_order(order_id)
        return {
            'id': order['id'],
            'timestamp': order['timestamp'],
            'price': order['price'], 
            'amount': order['amount'], 
            'cost': order['cost'], 
            'fees': order['fees'][0]['cost'],
        }


if __name__ == '__main__':

    trader = Trader(
        pair='BTC/EUR', 
        cost=5, 
        time_period='1h',
        gain_threshold= 5 / 100
    )

    while True:
        trader.run_strategy()
        time.sleep(60*60)