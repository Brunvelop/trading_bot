import os
import datetime
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
        prices = [bar[4] for bar in bars]

        for period in periods:
            if len(prices) >= period:  # Ensure there are enough prices to calculate SMA
                sma = sum(prices[:period]) / period  # Calculate SMA for first 'period' prices
                smas.append(sma)

        return smas
    
    def cancel_order(self, id, symbol):
        # Cancelar la orden
        return self.cancelOrder(id, symbol)

    def update_stop_loss(self, pair, side, price, amount):
        exchange = self.connect_api()
        # Buscar todas las órdenes abiertas
        open_orders = exchange.fetchOpenOrders(pair)

        # Encontrar la orden de stop loss existente
        stop_loss_order = next((order for order in open_orders if order['type'] == 'stopLoss'), None)

        # Cancelar la orden de stop loss existente si existe
        if stop_loss_order is not None:
            self.cancel_order(stop_loss_order['id'], pair)

        return self.create_order(pair, 'stopLoss', side, amount, price)


class Trader:
    def __init__(self, pair='BTC/USD', cost=5, time_period='1h', gain_threshold=0.005):
        self.kraken_api = KrakenAPI()
        self.pair = pair
        self.cost = cost
        self.time_period = time_period
        self.db = DB()
        self.gain_threshold = gain_threshold

    def get_amount(self, price):
        return self.cost / price

    def run_strategy(self):
        bars = self.kraken_api.get_bars(self.pair, self.time_period, 200)
        sma_10, sma_50, sma_100, sma_200 = self.kraken_api.get_smas(bars)
        price = self.kraken_api.get_latest_price(self.pair)
        
        print("price:", price, "smas(10,50,100,200)=", sma_10, sma_50, sma_100, sma_200)
        if price > sma_10 > sma_50 > sma_100 > sma_200:
            print('Trying to sell...', flush=True)
            self.update_position()
            self.sell()
            self.set_stop_loss(sma_200)
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
                datetime.datetime.fromtimestamp(int(order_executed_info['timestamp']/1000)).isoformat(),
                order_executed_info['price'],
                order_executed_info['amount'],
                order_executed_info['cost'],
                order_executed_info['fees'],
                False
            )
        return self.get_order_info(order['id'])
    
    def update_position(self):
        last_position = self.db.get_last_position()
        # Si no hay ninguna posición, establecer la posición en 1
        if last_position is None:
            position = 1
        else:
            position = last_position + 1

        self.db.update_null_positions(position)

    def sell(self):
        orders = self.db.get_open_trades_with_highest_position()

        price = self.kraken_api.get_latest_price(self.pair)
        orders = self.db.get_orders_below(price*(1-self.gain_threshold)).data
        print("Price below: ", price*(1-self.gain_threshold))

        if orders:
            amount = orders[0][3]
            order = self.kraken_api.create_order(self.pair, 'market', 'sell', amount, price)
            order_info = self.get_order_info(order['id'])
            self.db.update_order(
                    orders[0][0],
                    datetime.datetime.fromtimestamp(int(order_info['timestamp']/1000)).isoformat(),
                    order_info['price'],
                    order_info['amount'],
                    order_info['cost'],
                    order_info['fees'],
            )
            return order_info
        return None

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
    
    def set_stop_loss(self, sma_200):
        orders = self.db.get_open_trades_with_highest_position()

        total_price = sum(order['buy_price'] for order in orders)
        total_amount = sum(order['amount'] for order in orders)

        average_price = total_price / len(orders) if orders else 0
        stop_loss_price = sma_200 * 0.9990
        
        print("Average price: ", average_price)
        print("Stop loss price ", stop_loss_price * (1 - self.gain_threshold))
        if average_price < stop_loss_price * (1 - self.gain_threshold):
            return self.kraken_api.update_stop_loss(self.pair, 'sell', stop_loss_price, total_amount)
        else:
            return None




if __name__ == "__main__":
    import time
    import schedule

    trader = Trader(
        pair='BTC/EUR', 
        cost=3, 
        time_period='1m'
    )


    def job():
        start_time = time.time()  # Inicio del tiempo de ejecución
        print("----------- RUN -----------")
        trader.run_strategy()
        end_time = time.time()  # Fin del tiempo de ejecución
        print("Tiempo de ejecución: {} segundos".format(end_time - start_time))

    schedule.every().minute.at(":06").do(job)

    while True:
        # print("Esperando el próximo trabajo...")
        schedule.run_pending()
        time.sleep(1)



