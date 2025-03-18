"""
Unit tests for the data_manager module.

This module contains tests for the DataManager, CoinexManager, and BinanceManager classes.
"""

import io
import csv
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from datetime import datetime

from data_manager import DataManager, DataSource, CoinexManager, BinanceManager
from definitions import MarketData

class TestDataManager(unittest.TestCase):
    """Test cases for the DataManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create sample data for testing
        self.sample_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=100, freq='1h'),
            'open': np.linspace(100, 200, 100).astype(np.float64),
            'high': np.linspace(110, 210, 100).astype(np.float64),
            'low': np.linspace(90, 190, 100).astype(np.float64),
            'close': np.linspace(105, 205, 100).astype(np.float64),
            'volume': np.random.rand(100) * 1000
        })
        
        # Save sample data to CSV
        self.sample_data_path = self.test_dir / 'sample_data.csv'
        self.sample_data.to_csv(self.sample_data_path, index=False)
        
        # Create a directory with multiple CSV files
        self.multi_data_dir = self.test_dir / 'multi_data'
        self.multi_data_dir.mkdir()
        
        for i in range(3):
            df = pd.DataFrame({
                'date': pd.date_range(start=f'2023-0{i+1}-01', periods=50, freq='1h'),
                'open': np.linspace(100 * (i+1), 200 * (i+1), 50).astype(np.float64),
                'high': np.linspace(110 * (i+1), 210 * (i+1), 50).astype(np.float64),
                'low': np.linspace(90 * (i+1), 190 * (i+1), 50).astype(np.float64),
                'close': np.linspace(105 * (i+1), 205 * (i+1), 50).astype(np.float64),
                'volume': np.random.rand(50) * 1000
            })
            df.to_csv(self.multi_data_dir / f'data_{i}.csv', index=False)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory and all its contents
        shutil.rmtree(self.test_dir)
    
    def test_choose_random_data_path(self):
        """Test _choose_random_data_path method."""
        # Test with a directory
        result = DataManager._choose_random_data_path(self.multi_data_dir)
        self.assertTrue(result.exists())
        self.assertTrue(result.is_file())
        self.assertTrue(str(result).endswith('.csv'))
        
        # Test with a file
        result = DataManager._choose_random_data_path(self.sample_data_path)
        self.assertEqual(result, self.sample_data_path)
        
        # Test with a directory that has no CSV files
        empty_dir = self.test_dir / 'empty'
        empty_dir.mkdir()
        with self.assertRaises(ValueError):
            DataManager._choose_random_data_path(empty_dir)
    
    def test_normalize_data(self):
        """Test _normalize_data method."""
        # Create test data
        df = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=5, freq='1h'),
            'open': np.array([100, 110, 120, 130, 140], dtype=np.float64),
            'high': np.array([105, 115, 125, 135, 145], dtype=np.float64),
            'low': np.array([95, 105, 115, 125, 135], dtype=np.float64),
            'close': np.array([102, 112, 122, 132, 142], dtype=np.float64),
            'volume': np.array([1000, 1100, 1200, 1300, 1400], dtype=np.float64)
        })
        
        # Normalize the data
        normalized = DataManager._normalize_data(df)
        
        # Check that close prices are normalized
        max_close = 142
        np.testing.assert_almost_equal(normalized['close'].values, df['close'].values / max_close)
        
        # Check that other price columns are normalized
        np.testing.assert_almost_equal(normalized['open'].values, df['open'].values / max_close)
        np.testing.assert_almost_equal(normalized['high'].values, df['high'].values / max_close)
        np.testing.assert_almost_equal(normalized['low'].values, df['low'].values / max_close)
        
        # Check that volume is not normalized
        np.testing.assert_array_equal(normalized['volume'].values, df['volume'].values)
        
        # Test with zero max close
        df_zero = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=5, freq='1h'),
            'open': np.zeros(5, dtype=np.float64),
            'high': np.zeros(5, dtype=np.float64),
            'low': np.zeros(5, dtype=np.float64),
            'close': np.zeros(5, dtype=np.float64),
            'volume': np.array([1000, 1100, 1200, 1300, 1400], dtype=np.float64)
        })
        
        # Should not raise an error and return the original data
        result = DataManager._normalize_data(df_zero)
        pd.testing.assert_frame_equal(result, df_zero)
    
    def test_select_time_segment(self):
        """Test _select_time_segment method."""
        # Create test data
        df = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=10, freq='1h'),
            'open': (np.arange(10) * 10).astype(np.float64),
            'high': (np.arange(10) * 10 + 5).astype(np.float64),
            'low': (np.arange(10) * 10 + 1).astype(np.float64),  # Ensure all values are positive
            'close': (np.arange(10) * 10 + 2).astype(np.float64),
            'volume': (np.arange(10) * 100).astype(np.float64)
        })
        
        # Test with start only
        result = DataManager._select_time_segment(3, None, df)
        self.assertEqual(len(result), 7)
        pd.testing.assert_frame_equal(result, df.iloc[3:])
        
        # Test with end only
        result = DataManager._select_time_segment(None, 7, df)
        self.assertEqual(len(result), 7)
        pd.testing.assert_frame_equal(result, df.iloc[:7])
        
        # Test with both start and end
        result = DataManager._select_time_segment(2, 8, df)
        self.assertEqual(len(result), 6)
        pd.testing.assert_frame_equal(result, df.iloc[2:8])
        
        # Test with start >= end
        result = DataManager._select_time_segment(5, 5, df)
        self.assertEqual(len(result), 0)
        
        # Test with start > end
        result = DataManager._select_time_segment(8, 5, df)
        self.assertEqual(len(result), 0)
    
    def test_select_variation_segment(self):
        """Test _select_variation_segment method."""
        # Create test data with known variations
        df = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=100, freq='1h'),
            'open': (np.random.rand(100) * 100 + 1).astype(np.float64),  # Ensure all values are positive
            'high': (np.random.rand(100) * 100 + 10).astype(np.float64),
            'low': (np.random.rand(100) * 100 + 1).astype(np.float64),   # Ensure all values are positive
            'close': np.zeros(100, dtype=np.float64),
            'volume': (np.random.rand(100) * 1000).astype(np.float64)
        })
        
        # Set close prices to create specific variations
        # Segment 0-9: 10% increase
        df.loc[0:9, 'close'] = np.linspace(100, 110, 10).astype(np.float64)
        
        # Segment 10-19: 20% increase
        df.loc[10:19, 'close'] = np.linspace(100, 120, 10).astype(np.float64)
        
        # Segment 20-29: 10% decrease
        df.loc[20:29, 'close'] = np.linspace(100, 90, 10).astype(np.float64)
        
        # Segment 30-39: 20% decrease
        df.loc[30:39, 'close'] = np.linspace(100, 80, 10).astype(np.float64)
        
        # Rest of the data: random
        df.loc[40:, 'close'] = (np.random.rand(60) * 100 + 1).astype(np.float64)  # Ensure all values are positive
        
        # Test finding a segment with 10% increase
        with patch('numpy.random.randint', side_effect=[0, 10, 20, 30, 40]):
            result = DataManager._select_variation_segment(10, 0.1, 0.01, df)
            self.assertEqual(len(result), 10)
            self.assertAlmostEqual(result.iloc[0]['close'], 100)
            self.assertAlmostEqual(result.iloc[-1]['close'], 110)
        
        # Test finding a segment with 20% increase
        with patch('numpy.random.randint', side_effect=[10, 0, 20, 30, 40]):
            result = DataManager._select_variation_segment(10, 0.2, 0.01, df)
            self.assertEqual(len(result), 10)
            self.assertAlmostEqual(result.iloc[0]['close'], 100)
            self.assertAlmostEqual(result.iloc[-1]['close'], 120)
        
        # Test finding a segment with 10% decrease
        with patch('numpy.random.randint', side_effect=[20, 0, 10, 30, 40]):
            result = DataManager._select_variation_segment(10, -0.1, 0.01, df)
            self.assertEqual(len(result), 10)
            self.assertAlmostEqual(result.iloc[0]['close'], 100)
            self.assertAlmostEqual(result.iloc[-1]['close'], 90)
        
        # Test finding a segment with 20% decrease
        with patch('numpy.random.randint', side_effect=[30, 0, 10, 20, 40]):
            result = DataManager._select_variation_segment(10, -0.2, 0.01, df)
            self.assertEqual(len(result), 10)
            self.assertAlmostEqual(result.iloc[0]['close'], 100)
            self.assertAlmostEqual(result.iloc[-1]['close'], 80)
        
        # Test with duration >= data length
        result = DataManager._select_variation_segment(200, 0.1, 0.01, df)
        self.assertEqual(len(result), 100)  # Should return the full dataset
        
        # Test with no matching segment - use a smaller range to avoid timeout
        with patch('numpy.random.randint', side_effect=range(100)):
            with patch('data_manager.DataManager.MAX_ATTEMPTS', 100):  # Reduce max attempts for test
                with self.assertRaises(ValueError):
                    DataManager._select_variation_segment(10, 0.5, 0.001, df)
    
    @patch('data_manager.DataManager._normalize_data')
    @patch('data_manager.DataManager._select_time_segment')
    @patch('data_manager.DataManager._select_variation_segment')
    def test_get_marketdata_sample_with_file(self, mock_select_variation, mock_select_time, mock_normalize):
        """Test get_marketdata_sample with a specific file."""
        # Setup mocks to return the input data
        mock_select_variation.side_effect = lambda *args: args[3]
        mock_select_time.side_effect = lambda *args: args[2]
        mock_normalize.side_effect = lambda x: x
        
        # Test with a specific file
        market_data, metadata = DataManager.get_marketdata_sample(
            data_path=self.sample_data_path
        )
        
        # Check that the result is valid
        self.assertEqual(len(market_data), 100)
        self.assertEqual(metadata['data_path'], str(self.sample_data_path))
        self.assertEqual(metadata['rows'], 100)
    
    @patch('data_manager.DataManager._choose_random_data_path')
    @patch('data_manager.DataManager._normalize_data')
    @patch('data_manager.DataManager._select_time_segment')
    @patch('data_manager.DataManager._select_variation_segment')
    def test_get_marketdata_sample_with_directory(self, mock_select_variation, mock_select_time, 
                                                mock_normalize, mock_choose_path):
        """Test get_marketdata_sample with a directory."""
        # Setup mocks
        mock_choose_path.return_value = self.sample_data_path
        mock_select_variation.side_effect = lambda *args: args[3]
        mock_select_time.side_effect = lambda *args: args[2]
        mock_normalize.side_effect = lambda x: x
        
        # Test with a directory
        market_data, metadata = DataManager.get_marketdata_sample(
            data_path=self.multi_data_dir
        )
        
        # Check that the result is valid
        self.assertEqual(len(market_data), 100)
        self.assertEqual(metadata['data_path'], str(self.sample_data_path))
        self.assertEqual(metadata['rows'], 100)
    
    @patch('data_manager.DataManager._normalize_data')
    @patch('data_manager.DataManager._select_time_segment')
    @patch('data_manager.DataManager._select_variation_segment')
    def test_get_marketdata_sample_with_time_segment(self, mock_select_variation, mock_select_time, mock_normalize):
        """Test get_marketdata_sample with time segment selection."""
        # Setup mocks
        mock_select_variation.side_effect = lambda *args: args[3]
        
        # Create a smaller segment for time selection
        segment = self.sample_data.iloc[20:50].copy()
        mock_select_time.return_value = segment
        
        mock_normalize.side_effect = lambda x: x
        
        # Test with time segment selection
        market_data, metadata = DataManager.get_marketdata_sample(
            data_path=self.sample_data_path,
            start=20,
            end=50
        )
        
        # Check that the result is valid
        self.assertEqual(len(market_data), 30)
        self.assertEqual(metadata['start'], 20)
        self.assertEqual(metadata['end'], 50)
        self.assertEqual(metadata['rows'], 30)
    
    @patch('data_manager.DataManager._normalize_data')
    @patch('data_manager.DataManager._select_time_segment')
    @patch('data_manager.DataManager._select_variation_segment')
    def test_get_marketdata_sample_with_normalization(self, mock_select_variation, mock_select_time, mock_normalize):
        """Test get_marketdata_sample with normalization."""
        # Setup mocks
        mock_select_variation.side_effect = lambda *args: args[3]
        mock_select_time.side_effect = lambda *args: args[2]
        
        # Create normalized data with max close = 1.0
        normalized_data = self.sample_data.copy()
        max_close = normalized_data['close'].max()
        normalized_data['close'] = normalized_data['close'] / max_close
        normalized_data['open'] = normalized_data['open'] / max_close
        normalized_data['high'] = normalized_data['high'] / max_close
        normalized_data['low'] = normalized_data['low'] / max_close
        
        mock_normalize.return_value = normalized_data
        
        # Test with normalization
        market_data, metadata = DataManager.get_marketdata_sample(
            data_path=self.sample_data_path,
            normalize=True
        )
        
        # Check that the result is valid
        self.assertEqual(len(market_data), 100)
        self.assertTrue(metadata['normalize'])
        self.assertEqual(metadata['rows'], 100)
        
        # Check that prices are normalized
        self.assertLessEqual(market_data['close'].max(), 1.0)
    
    @patch('data_manager.CoinexManager.download_prices')
    def test_download_prices_coinex(self, mock_download):
        """Test download_prices with Coinex source."""
        # Test downloading from Coinex
        DataManager.download_prices(
            source=DataSource.COINEX,
            download_folder=self.test_dir,
            base_currency='USDT',
            pairs_to_download=['BTC/USDT', 'ETH/USDT']
        )
        
        mock_download.assert_called_once_with(
            self.test_dir,
            'USDT',
            ['BTC/USDT', 'ETH/USDT']
        )
    
    @patch('data_manager.BinanceManager.download_prices')
    def test_download_prices_binance(self, mock_download):
        """Test download_prices with Binance source."""
        # Test downloading from Binance
        DataManager.download_prices(
            source=DataSource.BINANCE,
            download_folder=self.test_dir,
            base_currency='USDT'
        )
        
        mock_download.assert_called_once_with(
            self.test_dir,
            'USDT',
            None
        )


class TestCoinexManager(unittest.TestCase):
    """Test cases for the CoinexManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create a mock coinex_pairs.txt file
        self.pairs_file = Path('data/coinex_pairs.txt')
        self.pairs_content = "BTC/USDT\nETH/USDT\nLTC/USDT\nBTC/BTC\nETH/BTC"
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory and all its contents
        shutil.rmtree(self.test_dir)
    
    def test_download_prices(self):
        """Test download_prices method."""
        # Create a mock for the Path.exists method
        with patch('pathlib.Path.exists', return_value=True):
            # Create a mock for the open function
            with patch('builtins.open', new_callable=mock_open) as mock_file:
                # Setup mock file with actual content
                mock_file.return_value.__enter__.return_value.read.return_value = self.pairs_content
                
                # Create a mock for the Path.glob method
                with patch('pathlib.Path.glob') as mock_glob:
                    # Setup mock glob to return no existing files
                    mock_glob.return_value = []
                    
                    # Create a mock for the download_pair method
                    with patch('data_manager.CoinexManager.download_pair') as mock_download_pair:
                        # Test with default parameters
                        CoinexManager.download_prices(
                            download_folder=self.test_dir,
                            base_currency='USDT'
                        )
                        
                        # Should have called download_pair for all USDT pairs
                        self.assertEqual(mock_download_pair.call_count, 3)
                        mock_download_pair.assert_any_call('BTC/USDT', self.test_dir)
                        mock_download_pair.assert_any_call('ETH/USDT', self.test_dir)
                        mock_download_pair.assert_any_call('LTC/USDT', self.test_dir)
    
    def test_download_pair(self):
        """Test download_pair method."""
        # Create a mock for the Path.open method
        with patch('pathlib.Path.open', new_callable=mock_open) as mock_file:
            # Create a mock for requests.get
            with patch('requests.get') as mock_get:
                # Setup mock response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = b'mock content'
                mock_get.return_value.__enter__.return_value = mock_response
                
                # Create a mock for zipfile.ZipFile
                with patch('zipfile.ZipFile') as mock_zipfile:
                    # Setup mock zip
                    mock_zip = MagicMock()
                    mock_zip.namelist.return_value = ['data.csv']
                    mock_zip.read.return_value = b'header\n1609459200,100,110,90,105,1000\n1609462800,105,115,95,110,1100'
                    mock_zipfile.return_value.__enter__.return_value = mock_zip
                    
                    # Create other necessary mocks
                    with patch('pathlib.Path.exists', return_value=False):
                        with patch('pathlib.Path.touch') as mock_touch:
                            with patch('pathlib.Path.stat') as mock_stat:
                                with patch('pandas.read_csv') as mock_read_csv:
                                    with patch('pandas.DataFrame.sort_values') as mock_sort_values:
                                        with patch('pandas.DataFrame.drop_duplicates') as mock_drop_duplicates:
                                            with patch('pandas.DataFrame.to_csv') as mock_to_csv:
                                                # Setup additional mocks
                                                mock_stat.return_value.st_size = 0
                                                mock_df = MagicMock()
                                                mock_read_csv.return_value = mock_df
                                                mock_sort_values.return_value = mock_df
                                                mock_drop_duplicates.return_value = mock_df
                                                
                                                # Mock datetime to use a fixed date
                                                with patch('datetime.datetime') as mock_datetime:
                                                    mock_datetime.now.return_value = datetime(2025, 2, 18)
                                                    
                                                    # Test download_pair
                                                    CoinexManager.download_pair('BTC/USDT', self.test_dir)
                                                    
                                                    # Check that the file was created
                                                    mock_touch.assert_called_once()
                                                    
                                                    # Check that requests.get was called with the correct URL
                                                    mock_get.assert_called_with(
                                                        'https://file.coinexstatic.com/BTCUSDT-Kline-MINUTE-Spot-2025-02.zip',
                                                        stream=True
                                                    )
                                                    
                                                    # Check that the zip file was read
                                                    mock_zip.read.assert_called_with('data.csv')
                                                    
                                                    # Check that the file was written
                                                    mock_file.assert_called()
                                                    
                                                    # Check that the data was processed and saved
                                                    mock_read_csv.assert_called_once()
                                                    mock_sort_values.assert_called_once_with('date')
                                                    mock_drop_duplicates.assert_called_once_with(subset='date', keep='first')
                                                    mock_to_csv.assert_called_once_with(self.test_dir / 'BTC_USDT_1m.csv', index=False)


class TestBinanceManager(unittest.TestCase):
    """Test cases for the BinanceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory and all its contents
        shutil.rmtree(self.test_dir)
    
    @patch('data_manager.BinanceManager._format_prices')
    @patch('binance_historical_data.BinanceDataDumper')
    def test_download_prices(self, mock_dumper_class, mock_format_prices):
        """Test download_prices method."""
        # Setup mock
        mock_dumper = MagicMock()
        mock_dumper_class.return_value = mock_dumper
        
        # Test download_prices
        BinanceManager.download_prices(
            download_folder=self.test_dir,
            base_currency='USDT'
        )
        
        # Check that BinanceDataDumper was initialized correctly
        mock_dumper_class.assert_called_once_with(
            path_dir_where_to_dump=str(self.test_dir),
            asset_class="spot",
            data_type="klines",
            data_frequency="1m",
        )
        
        # Check that dump_data was called
        mock_dumper.dump_data.assert_called_once()
        
        # Check that _format_prices was called
        mock_format_prices.assert_called_once_with(
            self.test_dir,
            self.test_dir / 'processed'
        )


if __name__ == '__main__':
    pytest.main()
