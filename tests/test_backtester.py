import unittest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.backtester import Backtester
from strategies.strategy import Strategy
from definitions import Action, MarketData

class MockStrategy(Strategy):
    def __init__(self, actions=None):
        self.actions = actions if actions is not None else []
        self.current_index = 0
    
    def run(self, data: MarketData, memory: dict):
        if self.current_index < len(self.actions):
            action = self.actions[self.current_index]
            self.current_index += 1
            return [action]
        return []

    def calculate_indicators(self, data: MarketData):
        return []

class TestBacktester(unittest.TestCase):
    def setUp(self):
        # Create sample market data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        self.sample_data = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 2000, 100)
        })

    def test_initialization(self):
        """Test backtester initialization"""
        initial_balance_a = 100.0
        initial_balance_b = 1000.0
        fee = 0.002
        
        backtester = Backtester(
            strategy=MockStrategy(),
            initial_balance_a=initial_balance_a,
            initial_balance_b=initial_balance_b,
            fee=fee
        )
        
        self.assertEqual(backtester.memory['balance_a'], initial_balance_a)
        self.assertEqual(backtester.memory['balance_b'], initial_balance_b)
        self.assertEqual(backtester.fee, fee)
        self.assertEqual(len(backtester.memory['orders']), 0)

    def test_buy_order_execution(self):
        """Test execution of buy orders"""
        initial_balance_a = 0.0
        initial_balance_b = 1000.0
        price = 100.0
        amount = 1.0
        fee = 0.001
        
        # Create strategy that will execute one buy order
        strategy = MockStrategy(actions=[(Action.BUY_MARKET, price, amount)])
        
        backtester = Backtester(
            strategy=strategy,
            initial_balance_a=initial_balance_a,
            initial_balance_b=initial_balance_b,
            fee=fee
        )
        
        # Run backtest with our sample data
        backtester.marketdata = self.sample_data
        backtester._execute_strategy(self.sample_data)
        
        # Check balances after buy order
        expected_balance_a = amount * (1 - fee)  # Received amount minus fee
        expected_balance_b = initial_balance_b - (price * amount)  # Spent amount
        
        self.assertAlmostEqual(backtester.memory['balance_a'], expected_balance_a)
        self.assertAlmostEqual(backtester.memory['balance_b'], expected_balance_b)
        self.assertEqual(len(backtester.memory['orders']), 1)

    def test_sell_order_execution(self):
        """Test execution of sell orders"""
        initial_balance_a = 1.0
        initial_balance_b = 1000.0
        price = 100.0
        amount = 1.0
        fee = 0.001
        
        # Create strategy that will execute one sell order
        strategy = MockStrategy(actions=[(Action.SELL_MARKET, price, amount)])
        
        backtester = Backtester(
            strategy=strategy,
            initial_balance_a=initial_balance_a,
            initial_balance_b=initial_balance_b,
            fee=fee
        )
        
        # Run backtest with our sample data
        backtester.marketdata = self.sample_data
        backtester._execute_strategy(self.sample_data)
        
        # Check balances after sell order
        expected_balance_a = initial_balance_a - amount
        expected_balance_b = initial_balance_b + (price * amount * (1 - fee))
        
        self.assertAlmostEqual(backtester.memory['balance_a'], expected_balance_a)
        self.assertAlmostEqual(backtester.memory['balance_b'], expected_balance_b)
        self.assertEqual(len(backtester.memory['orders']), 1)

    def test_multiple_orders(self):
        """Test execution of multiple orders"""
        initial_balance_a = 1.0
        initial_balance_b = 1000.0
        price = 100.0
        amount = 0.5
        fee = 0.001
        
        # Create strategy that will execute multiple orders
        strategy = MockStrategy(actions=[
            (Action.SELL_MARKET, price, amount),
            (Action.BUY_MARKET, price, amount)
        ])
        
        backtester = Backtester(
            strategy=strategy,
            initial_balance_a=initial_balance_a,
            initial_balance_b=initial_balance_b,
            fee=fee
        )
        
        # Run backtest with our sample data
        backtester.marketdata = self.sample_data
        backtester._execute_strategy(self.sample_data)  # First order
        backtester._execute_strategy(self.sample_data)  # Second order
        
        # Verify number of orders
        self.assertEqual(len(backtester.memory['orders']), 2)

    def test_fee_calculation(self):
        """Test proper fee calculation"""
        initial_balance_a = 1.0
        initial_balance_b = 1000.0
        price = 100.0
        amount = 1.0
        fee = 0.002  # 0.2% fee
        
        strategy = MockStrategy(actions=[(Action.SELL_MARKET, price, amount)])
        
        backtester = Backtester(
            strategy=strategy,
            initial_balance_a=initial_balance_a,
            initial_balance_b=initial_balance_b,
            fee=fee
        )
        
        backtester.marketdata = self.sample_data
        backtester._execute_strategy(self.sample_data)
        
        # Check if fee was recorded correctly in order
        order = backtester.memory['orders'][0]
        expected_fee = price * amount * fee
        self.assertAlmostEqual(order['fee'], expected_fee)

if __name__ == '__main__':
    unittest.main()
