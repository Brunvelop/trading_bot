"""
Unit tests for the indicators module.

This module contains tests for the technical indicators implemented in the indicators.py module.
Each test verifies that the indicators are calculated correctly and handle edge cases appropriately.
"""

import unittest
import pandas as pd
import numpy as np
from pandas.testing import assert_series_equal

from indicators import Indicators, Indicator, IndicatorTypes
from definitions import MarketData


class TestIndicators(unittest.TestCase):
    """Test cases for the Indicators class."""

    def setUp(self):
        """Set up test data for each test."""
        # Create a simple market data DataFrame for testing
        self.data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=30),
            'open': np.linspace(100, 110, 30),
            'high': np.linspace(101, 111, 30),
            'low': np.linspace(99, 109, 30),
            'close': np.linspace(100, 110, 30),
            'volume': np.linspace(1000, 2000, 30)
        })
        
        # Add some noise to make the data more realistic
        np.random.seed(42)  # For reproducibility
        self.data['close'] = self.data['close'] + np.random.normal(0, 1, 30)
        self.data['high'] = self.data['close'] + np.random.uniform(0, 1, 30)
        self.data['low'] = self.data['close'] - np.random.uniform(0, 1, 30)
        self.data['volume'] = self.data['volume'] + np.random.normal(0, 100, 30)
        
        # Validate the data using MarketData schema
        self.market_data = MarketData.validate(self.data)

    def test_moving_average(self):
        """Test the calculate_moving_average method."""
        window = 5
        ma = Indicators.calculate_moving_average(self.market_data, window)
        
        # Check the result type
        self.assertIsInstance(ma, Indicator)
        self.assertEqual(ma.name, f'ma_{window}')
        self.assertEqual(ma.type, IndicatorTypes.Price.SIMPLE_MOVING_AVERAGE)
        
        # Check the calculation
        expected = self.market_data['close'].rolling(window=window).mean()
        assert_series_equal(ma.result, expected)
        
        # First (window-1) values should be NaN
        self.assertTrue(ma.result.iloc[:window-1].isna().all())
        
        # Values after window should not be NaN
        self.assertTrue(ma.result.iloc[window:].notna().all())

    def test_bollinger_bands(self):
        """Test the calculate_bollinger_bands method."""
        window = 5
        num_std = 2.0
        bands = Indicators.calculate_bollinger_bands(self.market_data, window, num_std)
        
        # Check the result type
        self.assertEqual(len(bands), 3)
        for band in bands:
            self.assertIsInstance(band, Indicator)
            self.assertEqual(band.type, IndicatorTypes.Price.BOLLINGER_BANDS)
        
        # Check the calculation
        sma = self.market_data['close'].rolling(window=window).mean()
        std = self.market_data['close'].rolling(window=window).std()
        expected_middle = sma
        expected_upper = sma + (std * num_std)
        expected_lower = sma - (std * num_std)
        
        assert_series_equal(bands[0].result, expected_middle)
        assert_series_equal(bands[1].result, expected_upper)
        assert_series_equal(bands[2].result, expected_lower)
        
        # Upper band should always be greater than middle band (ignoring NaN values)
        self.assertTrue((bands[1].result.dropna() >= bands[0].result.dropna()).all())
        
        # Lower band should always be less than middle band (ignoring NaN values)
        self.assertTrue((bands[2].result.dropna() <= bands[0].result.dropna()).all())

    def test_macd(self):
        """Test the calculate_macd method."""
        fast_period = 5
        slow_period = 10
        signal_period = 3
        macd_indicators = Indicators.calculate_macd(
            self.market_data, fast_period, slow_period, signal_period
        )
        
        # Check the result type
        self.assertEqual(len(macd_indicators), 3)
        for indicator in macd_indicators:
            self.assertIsInstance(indicator, Indicator)
            self.assertEqual(indicator.type, IndicatorTypes.Price.MACD)
        
        # Check the calculation
        exp1 = self.market_data['close'].ewm(span=fast_period, adjust=False).mean()
        exp2 = self.market_data['close'].ewm(span=slow_period, adjust=False).mean()
        expected_macd = exp1 - exp2
        expected_signal = expected_macd.ewm(span=signal_period, adjust=False).mean()
        expected_histogram = expected_macd - expected_signal
        
        assert_series_equal(macd_indicators[0].result, expected_macd)
        assert_series_equal(macd_indicators[1].result, expected_signal)
        assert_series_equal(macd_indicators[2].result, expected_histogram)

    def test_rsi(self):
        """Test the calculate_rsi method."""
        window = 5
        rsi = Indicators.calculate_rsi(self.market_data, window)
        
        # Check the result type
        self.assertIsInstance(rsi, Indicator)
        self.assertEqual(rsi.name, f'rsi_{window}')
        self.assertEqual(rsi.type, IndicatorTypes.Extra.RELATIVE_STRENGTH_INDEX)
        
        # RSI should be between 0 and 100
        self.assertTrue((rsi.result.dropna() >= 0).all() and (rsi.result.dropna() <= 100).all())
        
        # First few values should be NaN (due to diff and rolling window)
        self.assertTrue(rsi.result.iloc[:window].isna().any())

    def test_volume_sma(self):
        """Test the calculate_volume_sma method."""
        window = 5
        vol_sma = Indicators.calculate_volume_sma(self.market_data, window)
        
        # Check the result type
        self.assertIsInstance(vol_sma, Indicator)
        self.assertEqual(vol_sma.name, f'volume_sma_{window}')
        self.assertEqual(vol_sma.type, IndicatorTypes.Extra.VOLUME_SMA)
        
        # Check the calculation
        expected = self.market_data['volume'].rolling(window=window).mean()
        assert_series_equal(vol_sma.result, expected)

    def test_velocity(self):
        """Test the calculate_velocity method."""
        window = 3
        series = self.market_data['close']
        velocity = Indicators.calculate_velocity(series, window)
        
        # Check the result type
        self.assertIsInstance(velocity, Indicator)
        self.assertEqual(velocity.name, f'velocity_{window}')
        self.assertEqual(velocity.type, IndicatorTypes.Extra.VELOCITY)
        
        # Check the calculation
        expected = series.diff(periods=1).rolling(window=window).mean()
        assert_series_equal(velocity.result, expected)

    def test_acceleration(self):
        """Test the calculate_acceleration method."""
        window = 3
        series = self.market_data['close']
        velocity = series.diff(periods=1)
        acceleration = Indicators.calculate_acceleration(velocity, window)
        
        # Check the result type
        self.assertIsInstance(acceleration, Indicator)
        self.assertEqual(acceleration.name, f'acceleration_{window}')
        self.assertEqual(acceleration.type, IndicatorTypes.Extra.ACCELERATION)
        
        # Check the calculation
        expected = velocity.diff(periods=1).rolling(window=window).mean()
        assert_series_equal(acceleration.result, expected)

    def test_exponential_moving_average(self):
        """Test the calculate_exponential_moving_average method."""
        window = 5
        ema = Indicators.calculate_exponential_moving_average(self.market_data, window)
        
        # Check the result type
        self.assertIsInstance(ema, Indicator)
        self.assertEqual(ema.name, f'ema_{window}')
        self.assertEqual(ema.type, IndicatorTypes.Price.SIMPLE_MOVING_AVERAGE)
        
        # Check the calculation
        expected = self.market_data['close'].ewm(span=window, adjust=False).mean()
        assert_series_equal(ema.result, expected)

    def test_atr(self):
        """Test the calculate_atr method."""
        window = 5
        atr = Indicators.calculate_atr(self.market_data, window)
        
        # Check the result type
        self.assertIsInstance(atr, Indicator)
        self.assertEqual(atr.name, f'atr_{window}')
        
        # ATR should always be positive
        self.assertTrue((atr.result.dropna() >= 0).all())
        
        # First few values should be NaN (due to shift and rolling window)
        self.assertTrue(atr.result.iloc[:window].isna().any())


if __name__ == '__main__':
    unittest.main()
