import os

import ccxt
from dotenv import load_dotenv

class KrakenAPI:
    def __init__(self):
        pass

    def connect_api(self):
        load_dotenv()
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
        exchange = self.connect_api()
        return exchange.cancelOrder(id, symbol)

    def update_stop_loss(self, pair, side, price, amount):
        exchange = self.connect_api()
        # Buscar todas las órdenes abiertas
        open_orders = exchange.fetchOpenOrders(pair)

        # Encontrar la orden de stop loss existente
        stop_loss_order = next((order for order in open_orders if order['type'] == 'stop-loss'), None)

        # Cancelar la orden de stop loss existente si existe
        if stop_loss_order is not None:
            self.cancel_order(stop_loss_order['id'], pair)

        return self.create_order(pair, 'stop-loss', side, amount, price)