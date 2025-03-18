import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from datetime import datetime

from trader import Trader
from strategies import Strategy, ActionType, Action
from exchange_apis import BaseExchangeAPI
from definitions import MarketData, Memory, Order

class TestTrader(unittest.TestCase):
    def setUp(self):
        """Initial setup for each test."""
        # Create mocks for dependencies
        self.mock_strategy = MagicMock(spec=Strategy)
        self.mock_exchange_api = MagicMock(spec=BaseExchangeAPI)
        
        # Create Trader instance with mocks
        self.trader = Trader(self.mock_strategy, self.mock_exchange_api, 'BTC/USDT')
        
        # Test data
        self.test_price = 50000.0
        self.test_amount = 0.1
        
        # Create test market data
        self.market_data = MagicMock(spec=MarketData)
        
        # Create test memory
        self.memory = Memory(
            orders=[],
            balance_a=np.float64(1.0),  # BTC
            balance_b=np.float64(100000.0)  # USDT
        )
        
        # Simulated exchange response
        self.mock_order_response = {
            'id': '12345',
            'status': 'open',
            'symbol': 'BTC/USDT',
            'type': 'market',
            'side': 'buy',
            'price': self.test_price,
            'amount': self.test_amount
        }
        
        # Configure exchange mock to return simulated response
        self.mock_exchange_api.create_order.return_value = self.mock_order_response
        self.mock_exchange_api.cancel_order.return_value = {'id': '12345', 'status': 'canceled'}
        self.mock_exchange_api.get_order.return_value = self.mock_order_response

    def test_buy_market(self):
        """Test execution of a market buy order."""
        # Execute the method
        result = self.trader.buy_market(self.test_price, self.test_amount)
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.create_order.assert_called_once_with(
            'BTC/USDT', 'market', 'buy', self.test_amount, self.test_price
        )
        
        # Verify the result
        self.assertEqual(result, self.mock_order_response)

    def test_sell_market(self):
        """Test execution of a market sell order."""
        # Execute the method
        result = self.trader.sell_market(self.test_price, self.test_amount)
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.create_order.assert_called_once_with(
            'BTC/USDT', 'market', 'sell', self.test_amount, self.test_price
        )
        
        # Verify the result
        self.assertEqual(result, self.mock_order_response)

    def test_buy_limit(self):
        """Test execution of a limit buy order."""
        # Execute the method
        result = self.trader.buy_limit(self.test_price, self.test_amount)
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.create_order.assert_called_once_with(
            'BTC/USDT', 'limit', 'buy', self.test_amount, self.test_price
        )
        
        # Verify the result
        self.assertEqual(result, self.mock_order_response)

    def test_sell_limit(self):
        """Test execution of a limit sell order."""
        # Execute the method
        result = self.trader.sell_limit(self.test_price, self.test_amount)
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.create_order.assert_called_once_with(
            'BTC/USDT', 'limit', 'sell', self.test_amount, self.test_price
        )
        
        # Verify the result
        self.assertEqual(result, self.mock_order_response)

    def test_set_stop_loss(self):
        """Test setting a stop loss order."""
        # Execute the method
        result = self.trader.set_stop_loss(self.test_price, self.test_amount)
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.create_order.assert_called_once_with(
            'BTC/USDT', 'stop_loss', 'sell', self.test_amount, self.test_price, {'stopPrice': self.test_price}
        )
        
        # Verify the result
        self.assertEqual(result, self.mock_order_response)

    def test_set_take_profit(self):
        """Test setting a take profit order."""
        # Execute the method
        result = self.trader.set_take_profit(self.test_price, self.test_amount)
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.create_order.assert_called_once_with(
            'BTC/USDT', 'take_profit', 'sell', self.test_amount, self.test_price, {'triggerPrice': self.test_price}
        )
        
        # Verify the result
        self.assertEqual(result, self.mock_order_response)

    def test_cancel_order(self):
        """Test cancelling an order."""
        # Execute the method
        result = self.trader.cancel_order('12345')
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.cancel_order.assert_called_once_with('12345', 'BTC/USDT')
        
        # Verify the result
        self.assertEqual(result, {'id': '12345', 'status': 'canceled'})

    def test_get_order_status(self):
        """Test getting the status of an order."""
        # Execute the method
        result = self.trader.get_order_status('12345')
        
        # Verify that the correct exchange API method was called
        self.mock_exchange_api.get_order.assert_called_once_with('12345', 'BTC/USDT')
        
        # Verify the result
        self.assertEqual(result, self.mock_order_response)

    def test_execute_strategy(self):
        """Test executing a strategy."""
        # Configure the strategy mock to return actions
        buy_action = Action(action_type=ActionType.BUY_MARKET, price=np.float64(self.test_price), amount=np.float64(self.test_amount))
        self.mock_strategy.run.return_value = [buy_action]
        
        # Execute the method
        self.trader.execute_strategy(self.market_data, self.memory)
        
        # Verify that the strategy's run method was called
        self.mock_strategy.run.assert_called_once_with(self.market_data, self.memory)
        
        # Verify that the exchange API's create_order method was called
        self.mock_exchange_api.create_order.assert_called_once_with(
            'BTC/USDT', 'market', 'buy', self.test_amount, self.test_price
        )

    def test_execute_strategy_insufficient_balance(self):
        """Test executing a strategy with insufficient balance."""
        # Configure memory with insufficient balance
        memory_low_balance = Memory(
            orders=[],
            balance_a=np.float64(0.01),  # BTC (insufficient for selling 0.1)
            balance_b=np.float64(1000.0)  # USDT (insufficient for buying at 50000)
        )
        
        # Configure actions that require more balance than available
        buy_action = Action(action_type=ActionType.BUY_MARKET, price=np.float64(self.test_price), amount=np.float64(self.test_amount))
        sell_action = Action(action_type=ActionType.SELL_MARKET, price=np.float64(self.test_price), amount=np.float64(self.test_amount))
        self.mock_strategy.run.return_value = [buy_action, sell_action]
        
        # Execute the method
        self.trader.execute_strategy(self.market_data, memory_low_balance)
        
        # Verify that the exchange API's create_order method was not called
        self.mock_exchange_api.create_order.assert_not_called()

    def test_execute_strategy_exception_handling(self):
        """Test exception handling during strategy execution."""
        # Configure the strategy mock to raise an exception
        self.mock_strategy.run.side_effect = Exception("Test error")
        
        # Verify that the exception is propagated
        with self.assertRaises(Exception):
            self.trader.execute_strategy(self.market_data, self.memory)

    def test_execute_strategy_action_exception_handling(self):
        """Test exception handling during action execution."""
        # Configure a valid action
        buy_action = Action(action_type=ActionType.BUY_MARKET, price=np.float64(self.test_price), amount=np.float64(self.test_amount))
        self.mock_strategy.run.return_value = [buy_action]
        
        # Configure the exchange mock to raise an exception
        self.mock_exchange_api.create_order.side_effect = Exception("API error")
        
        # Execute the method (should not raise exception outside the method)
        self.trader.execute_strategy(self.market_data, self.memory)
        
        # Verify that the strategy's run method was called
        self.mock_strategy.run.assert_called_once_with(self.market_data, self.memory)
        
        # Verify that an attempt was made to call the create_order method
        self.mock_exchange_api.create_order.assert_called_once()

if __name__ == '__main__':
    unittest.main()
