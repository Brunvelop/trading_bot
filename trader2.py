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

        for i, bar in enumerate(bars[:max_period], start=1):
            price = bar[1]
            for j, period in enumerate(periods):
                if i < period:
                    sma_totals[j] += price
                elif i == period:
                    smas.append(sma_totals[j] / period)

        return smas
    
    def cancel_order(self, id, symbol):
        # Cancelar la orden
        return self.cancelOrder(id, symbol)

    def update_stop_loss(self, pair, side, price):
        # Buscar todas las órdenes abiertas
        open_orders = self.fetchOpenOrders(pair)

        # Encontrar la orden de stop loss existente
        stop_loss_order = next((order for order in open_orders if order['type'] == 'stopLoss'), None)

        # Cancelar la orden de stop loss existente si existe
        if stop_loss_order is not None:
            self.cancel_order(stop_loss_order['id'], pair)

        # Aquí asumimos que la cantidad de la orden de stop loss es todo el saldo disponible
        # Puedes cambiar esto según tus necesidades
        balance = self.get_account_balance(pair.split('/')[0])
        amount = balance['free']

        # Crear una nueva orden de stop loss
        # El tipo de orden es 'stopLoss', el precio es el precio de stop loss
        # y la cantidad es la cantidad calculada anteriormente
        return self.create_order(pair, 'stopLoss', side, amount, price)


class Trader:
    def __init__(self, pair='BTC/USD', cost=5, time_period='1h'):
        self.kraken_api = KrakenAPI()
        self.pair = pair
        self.cost = cost
        self.time_period = time_period
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
    
    def update_position(self):
        last_position = self.db.get_last_position()
        # Si no hay ninguna posición, establecer la posición en 1
        if last_position is None:
            position = 1
        else:
            position = last_position + 1

        self.db.update_null_positions(position)

    def sell(self):
        self.update_position()
        orders = self.db.get_orders_with_highest_position()

        # Calcular el precio medio de los pedidos
        total_price = sum(order['price'] for order in orders)
        average_price = total_price / len(orders) if orders else 0

        # Calcular el precio de stop loss que es el 1% por debajo del precio medio
        stop_loss_price = average_price * 1.01

        self.kraken_api.update_stop_loss(self.pair, 'sell', stop_loss_price)

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

trader = Trader(
    pair='BTC/EUR', 
    cost=10, 
    time_period='15m'
)

trader.run_strategy()




