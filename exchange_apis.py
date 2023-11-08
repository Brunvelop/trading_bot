import os
import ccxt
from dotenv import load_dotenv

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
    def __init__(self):
        super().__init__('okex', 'OKX_API_KEY', 'OKX_API_SECRET', {
            'password' : os.getenv('OKX_PASSWORD'),
            'enableRateLimit': True,
            'options':{
                'defaultType': 'future',
            }
        })

    def create_order(self, pair, order_type, side, amount, price):
        exchange = self.connect_api()
        params = {
            'marginMode': 'isolated',
            'leverage': '50'
        }
        return exchange.create_order(pair, order_type, side, amount, price, params)
    

# api = OKXAPI()
# pair = 'BTC/USD'

# def find_btc_usd_pairs(pairs):
#     return [pair for pair in pairs if 'BTC/USD' in pair]

# exchange = api.connect_api()
# pairs = exchange.load_markets()
# btc_usd_pairs = find_btc_usd_pairs(pairs)

#################################################

# api = OKXAPI()
# pair = 'BTC/USD:BTC'
# price = api.get_latest_price(pair=pair)
# order = api.create_order(pair=pair, order_type='market', side='buy', amount=1, price=price)
# order_info = api.get_order(order.get('info').get('ordId'), pair)