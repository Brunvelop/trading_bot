# Data Manager Module

## Overview

The Data Manager module provides functionality for downloading, processing, and managing historical price data from various cryptocurrency exchanges. It supports data from Coinex and Binance, with capabilities for data normalization, segment selection based on price variation, and more.

## Key Components

### DataSource Enum
- `COINEX`: Represents the Coinex exchange as a data source
- `BINANCE`: Represents the Binance exchange as a data source

### DataManager Class
The main class for managing historical price data with static methods for:
- Downloading price data from different sources
- Getting market data samples with various options
- Normalizing price data
- Selecting time segments
- Selecting segments with specific price variations

### CoinexManager Class
Specialized class for downloading and processing data from Coinex exchange:
- Downloads historical price data for specified pairs
- Processes and formats the downloaded data
- Handles file management and data deduplication

### BinanceManager Class
Specialized class for downloading and processing data from Binance exchange:
- Downloads historical price data using the binance_historical_data package
- Formats the downloaded data to match the standard format used by the system

## Key Methods

### DataManager.download_prices
Downloads historical price data from the specified source:
- `source`: The data source to download from (COINEX or BINANCE)
- `download_folder`: Directory where downloaded data will be stored
- `base_currency`: Base currency for trading pairs (e.g., 'USDT')
- `pairs_to_download`: Specific pairs to download

### DataManager.get_marketdata_sample
Gets a sample of market data with options for selecting specific segments:
- `data_path`: Path to the data file or directory
- `start`: Start index for time segment selection
- `end`: End index for time segment selection
- `duration`: Duration of the segment to select (number of data points)
- `variation`: Target price variation for the selected segment
- `tolerance`: Tolerance for the variation target
- `normalize`: Whether to normalize the price data

### DataManager._normalize_data
Normalizes price data by dividing by the maximum close price:
- Normalizes open, high, low, and close prices
- Leaves volume unchanged
- Handles edge cases like zero max close

### DataManager._select_time_segment
Selects a segment of data based on start and end indices:
- `start`: Start index (inclusive)
- `end`: End index (exclusive)
- `data`: Market data to select from

### DataManager._select_variation_segment
Selects a segment of data with a specific price variation:
- `duration`: Length of the segment to select
- `variation`: Target price variation (as a decimal, e.g., 0.1 for 10%)
- `tolerance`: Acceptable deviation from the target variation
- `data`: Market data to select from

## Testing

The module includes comprehensive unit tests for all classes and methods:
- Tests for DataManager class methods
- Tests for CoinexManager class methods
- Tests for BinanceManager class methods

Tests cover various scenarios including:
- Downloading price data from different sources
- Getting market data samples with different options
- Normalizing price data
- Selecting time segments
- Selecting segments with specific price variations

## Improvements Made

1. Fixed the `_select_variation_segment` method to handle edge cases:
   - Added a class constant `MAX_ATTEMPTS` to limit the number of attempts
   - Improved error handling to avoid index out of bounds errors
   - Added better logging for debugging

2. Enhanced test cases:
   - Added tests with fixed dates to avoid test failures when month changes
   - Used actual content from coinex_pairs.txt for more realistic testing
   - Added tests for edge cases and error conditions

3. Improved error handling throughout the module:
   - Added proper exception handling
   - Added informative error messages
   - Added logging for debugging

4. Added type hints and improved documentation:
   - Added type hints for all methods
   - Improved docstrings with parameter descriptions
   - Added examples and usage information

## Usage Examples

```python
# Download price data from Coinex
DataManager.download_prices(
    source=DataSource.COINEX,
    download_folder=Path('data/prices'),
    base_currency='USDT',
    pairs_to_download=['BTC/USDT', 'ETH/USDT']
)

# Get a market data sample with normalization
market_data, metadata = DataManager.get_marketdata_sample(
    data_path=Path('data/prices'),
    normalize=True
)

# Get a market data sample with specific variation
market_data, metadata = DataManager.get_marketdata_sample(
    data_path=Path('data/prices'),
    duration=100,
    variation=0.1,
    tolerance=0.01
)
