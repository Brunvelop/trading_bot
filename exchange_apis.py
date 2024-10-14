import os
from typing import Dict, List, Optional, Any

import ccxt
from dotenv import load_dotenv

load_dotenv()

class BaseExchangeAPI:
    def __init__(self, exchange_id: str, api_key: str, api_secret: str, options: Dict[str, Any]):
        self.exchange_id: str = exchange_id
        self.api_key: str = api_key
        self.api_secret: str = api_secret
        self.options: Dict[str, Any] = options

    def connect_api(self) -> ccxt.Exchange:
        load_dotenv()
        exchange: ccxt.Exchange = getattr(ccxt, self.exchange_id)({
            'apiKey': os.getenv(self.api_key),
            'secret': os.getenv(self.api_secret),
            **self.options
        })
        return exchange

    def create_order(self, pair: str, order_type: str, side: str, amount: float, price: float, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        exchange: ccxt.Exchange = self.connect_api()
        return exchange.create_order(pair, order_type, side, amount, price, params)

    def get_latest_price(self, pair: str) -> float:
        exchange: ccxt.Exchange = self.connect_api()
        ticker: Dict[str, Any] = exchange.fetch_ticker(pair)
        return ticker['last']

    def get_account_balance(self, currency: str) -> float:
        exchange: ccxt.Exchange = self.connect_api()
        balance: Dict[str, Any] = exchange.fetch_balance()
        return balance['total'][currency]

    def get_bars(self, pair: str, timeframe: str, limit: int) -> List[List[float]]:
        exchange: ccxt.Exchange = self.connect_api()
        return exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)[::-1]

    def get_order(self, order_id: str, symbol: str = '') -> Dict[str, Any]:
        exchange: ccxt.Exchange = self.connect_api()
        return exchange.fetch_order(order_id, symbol)

    def cancel_order(self, id: str, symbol: str) -> Dict[str, Any]:
        exchange: ccxt.Exchange = self.connect_api()
        return exchange.cancelOrder(id, symbol)
    
    def fetch_trades(self, pair: str, since: Optional[int] = None, limit: Optional[int] = None, params: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        exchange: ccxt.Exchange = self.connect_api()
        return exchange.fetch_trades(pair, since, limit, params)

class KrakenAPI(BaseExchangeAPI):
    def __init__(self):
        super().__init__('kraken', 'KRAKEN_API_KEY', 'KRAKEN_API_SECRET', {
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })

class OKXAPI(BaseExchangeAPI):
    def __init__(self, api_key: str = 'OKX_API_KEY', api_secret: str = 'OKX_API_SECRET'):
        super().__init__('okex', api_key, api_secret, options={
            'password': os.getenv('OKX_PASSWORD'),
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })   

class BinanceAPI(BaseExchangeAPI):
    def __init__(self):
        super().__init__('binance', 'BINANCE_API_KEY', 'BINANCE_API_SECRET', {
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })

class BitgetAPI(BaseExchangeAPI):
    def __init__(self, api_key: str = 'BITGET_API_KEY', api_secret: str = 'BITGET_API_SECRET'):
        super().__init__('bitget', api_key, api_secret, options={
            'password': os.getenv('BITGET_API_PASSWORD')
        })
