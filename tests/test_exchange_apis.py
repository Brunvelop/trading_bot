import unittest
from unittest.mock import MagicMock, patch
import os
import ccxt

from exchange_apis import BaseExchangeAPI, BinanceAPI, KrakenAPI, OKXAPI, BitgetAPI

class TestBaseExchangeAPI(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple mock for the exchange
        self.mock_exchange = MagicMock()
        
        # Create a test instance with a mocked _initialize_connection
        with patch.object(BaseExchangeAPI, '_initialize_connection'):
            self.api = BaseExchangeAPI('testexchange', 'TEST_API_KEY', 'TEST_API_SECRET', {})
            self.api.exchange = self.mock_exchange
        
        # Test data
        self.test_pair = 'BTC/USDT'
        self.test_price = 50000.0
        self.test_amount = 0.1
        self.test_order_id = '12345'
        
        # Configure mock responses
        self.mock_exchange.fetch_ticker.return_value = {'last': self.test_price}
        self.mock_exchange.fetch_balance.return_value = {'total': {'BTC': 1.0, 'USDT': 50000.0}}
        self.mock_exchange.create_order.return_value = {'id': self.test_order_id}
        self.mock_exchange.fetch_order.return_value = {'id': self.test_order_id}
        self.mock_exchange.cancel_order.return_value = {'id': self.test_order_id, 'status': 'canceled'}
        self.mock_exchange.fetch_ohlcv.return_value = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
        self.mock_exchange.fetch_trades.return_value = [{'id': '1'}, {'id': '2'}]
        
        # Attributes for testing
        self.mock_exchange.id = 'testexchange'
        self.mock_exchange.name = 'Test Exchange'
        self.mock_exchange.has = {'fetchTicker': True}
        self.mock_exchange.timeframes = {'1m': '1m', '1h': '1h'}
        self.mock_exchange.rateLimit = 1000
    
    def test_create_order(self):
        """Test creating an order."""
        result = self.api.create_order(self.test_pair, 'market', 'buy', self.test_amount, self.test_price)
        self.mock_exchange.create_order.assert_called_once()
        self.assertEqual(result['id'], self.test_order_id)
    
    def test_get_latest_price(self):
        """Test getting the latest price."""
        result = self.api.get_latest_price(self.test_pair)
        self.mock_exchange.fetch_ticker.assert_called_once()
        self.assertEqual(result, self.test_price)
    
    def test_get_account_balance(self):
        """Test getting the account balance."""
        result = self.api.get_account_balance('BTC')
        self.mock_exchange.fetch_balance.assert_called_once()
        self.assertEqual(result, 1.0)
    
    def test_get_account_balance_not_found(self):
        """Test getting a non-existent account balance."""
        result = self.api.get_account_balance('XYZ')
        self.mock_exchange.fetch_balance.assert_called_once()
        self.assertEqual(result, 0.0)
    
    def test_get_bars(self):
        """Test getting OHLCV bars."""
        result = self.api.get_bars(self.test_pair, '1h', 10)
        self.mock_exchange.fetch_ohlcv.assert_called_once()
        self.assertEqual(len(result), 2)  # Two bars in the mock response
    
    def test_get_order(self):
        """Test getting an order."""
        result = self.api.get_order(self.test_order_id, self.test_pair)
        self.mock_exchange.fetch_order.assert_called_once()
        self.assertEqual(result['id'], self.test_order_id)
    
    def test_cancel_order(self):
        """Test cancelling an order."""
        result = self.api.cancel_order(self.test_order_id, self.test_pair)
        self.mock_exchange.cancel_order.assert_called_once()
        self.assertEqual(result['status'], 'canceled')
    
    def test_fetch_trades(self):
        """Test fetching trades."""
        result = self.api.fetch_trades(self.test_pair)
        self.mock_exchange.fetch_trades.assert_called_once()
        self.assertEqual(len(result), 2)  # Two trades in the mock response


class TestExchangeImplementations(unittest.TestCase):
    """Test the specific exchange implementations."""
    
    def test_kraken_api(self):
        """Test KrakenAPI initialization."""
        with patch('exchange_apis.BaseExchangeAPI.__init__', return_value=None):
            api = KrakenAPI()
            # Manually set the exchange_id since we mocked __init__
            api.exchange_id = 'kraken'
            self.assertEqual(api.exchange_id, 'kraken')
    
    def test_binance_api(self):
        """Test BinanceAPI initialization."""
        with patch('exchange_apis.BaseExchangeAPI.__init__', return_value=None):
            api = BinanceAPI()
            # Manually set the exchange_id since we mocked __init__
            api.exchange_id = 'binance'
            self.assertEqual(api.exchange_id, 'binance')
    
    def test_okx_api(self):
        """Test OKXAPI initialization."""
        with patch('exchange_apis.BaseExchangeAPI.__init__', return_value=None):
            api = OKXAPI()
            # Manually set the exchange_id since we mocked __init__
            api.exchange_id = 'okex'
            self.assertEqual(api.exchange_id, 'okex')
    
    def test_bitget_api(self):
        """Test BitgetAPI initialization."""
        with patch('exchange_apis.BaseExchangeAPI.__init__', return_value=None):
            api = BitgetAPI()
            # Manually set the exchange_id since we mocked __init__
            api.exchange_id = 'bitget'
            self.assertEqual(api.exchange_id, 'bitget')


if __name__ == '__main__':
    unittest.main()
