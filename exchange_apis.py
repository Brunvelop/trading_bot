import os
import ccxt
from dotenv import load_dotenv

load_dotenv()
class BaseExchangeAPI:
    def __init__(self, exchange_id, api_key, api_secret, options):
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.options = options

    def connect_api(self):
        load_dotenv()
        exchange = getattr(ccxt, self.exchange_id)({
            'apiKey': os.getenv(self.api_key),
            'secret': os.getenv(self.api_secret),
            **self.options
        })
        return exchange

    def create_order(self, pair, order_type, side, amount, price):
        exchange = self.connect_api()
        return exchange.create_order(pair, order_type, side, amount, price)

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

    def get_order(self, order_id, symbol=''):
        exchange = self.connect_api()
        return exchange.fetch_order(order_id)

    def cancel_order(self, id, symbol):
        exchange = self.connect_api()
        return exchange.cancelOrder(id, symbol)

    def update_stop_loss(self, pair, side, price, amount):
        exchange = self.connect_api()
        open_orders = exchange.fetchOpenOrders(pair)
        stop_loss_order = next((order for order in open_orders if order['type'] == 'stop-loss'), None)
        if stop_loss_order is not None:
            self.cancel_order(stop_loss_order['id'], pair)
        return self.create_order(pair, 'stop-loss', side, amount, price)

class KrakenAPI(BaseExchangeAPI):
    def __init__(self):
        super().__init__('kraken', 'KRAKEN_API_KEY', 'KRAKEN_API_SECRET', {
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })

class OKXAPI(BaseExchangeAPI):
    def __init__(self, api_key='OKX_API_KEY', api_secret='OKX_API_SECRET'):
        super().__init__('okex',api_key, api_secret, options={
            'password' : os.getenv('OKX_PASSWORD'),
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })

    def get_order(self, order_id, symbol=''):
        exchange = self.connect_api()
        return exchange.fetch_order(order_id, symbol)

    def create_order_with_stop_loss(self, pair, order_type, side, amount, price, stop_loss_price, leverage):
        exchange = self.connect_api()
        order_type='conditional'
        params = {
            'marginMode': 'isolated',
            'leverage': str(leverage),
            'reduceOnly': True,
            'slTriggerPx': stop_loss_price,
        }
        return exchange.create_order(pair, order_type, side, amount, price, params)

    def create_order(self, pair, order_type, side, amount, price):
        exchange = self.connect_api()
        params = {
            'marginMode': 'isolated',
            'leverage': '3'
        }
        return exchange.create_order(pair, order_type, side, amount, price), #params)

    def fetchOpenOrders(self, symbol, since=None, limit=None, params={}):
        exchange = self.connect_api()
        return exchange.fetchOpenOrders(symbol, since, limit, params)
    
    def fetchPosition(self, symbols, params={}):
        exchange = self.connect_api()
        return exchange.fetchPosition(symbols, params)
    
class BinanceAPI(BaseExchangeAPI):
    def __init__(self):
        super().__init__('binance', 'BINANCE_API_KEY', 'BINANCE_API_SECRET', {
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })

    def get_order(self, order_id, symbol=''):
        exchange = self.connect_api()
        return exchange.fetch_order(order_id, symbol)

    def create_order_with_stop_loss(self, pair, order_type, side, amount, price, stop_loss_price):
        exchange = self.connect_api()
        order_type='conditional'
        params = {
            'marginMode': 'isolated',
            'leverage': '50',
            'reduceOnly': True,
            'slTriggerPx': stop_loss_price,
        }
        return exchange.create_order(pair, order_type, side, amount, price, params)

    def create_order(self, pair, order_type, side, amount, price):
        exchange = self.connect_api()
        params = {
            'marginMode': 'isolated',
            'leverage': '3'
        }
        return exchange.create_order(pair, order_type, side, amount, price, params)

    def fetchOpenOrders(self, symbol, since=None, limit=None, params={}):
        exchange = self.connect_api()
        return exchange.fetchOpenOrders(symbol, since, limit, params)
    
    def fetchPosition(self, symbols, params={}):
        exchange = self.connect_api()
        return exchange.fetchPosition(symbols, params)

    def fetch_currencies(self):
        exchange = self.connect_api()
        return exchange.fetch_currencies()