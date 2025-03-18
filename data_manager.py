"""
Data Manager Module

This module provides functionality for downloading, processing, and managing historical price data
from various cryptocurrency exchanges. It supports data from Coinex and Binance, with capabilities
for data normalization, segment selection based on price variation, and more.
"""

import io
import csv
import random
import logging
import requests
import zipfile
from tqdm import tqdm
from pathlib import Path
from enum import Enum, auto
from typing import List, Union, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pandera.errors import SchemaError

from definitions import MarketData

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class DataSource(Enum):
    """Enum representing supported data sources for historical price data."""
    COINEX = auto()
    BINANCE = auto()

class DataManager:
    """
    Main class for managing historical price data.
    
    This class provides static methods for downloading, processing, and selecting
    historical price data from various sources for use in backtesting and analysis.
    """
    
    @staticmethod
    def download_prices(
        source: DataSource = DataSource.COINEX, 
        download_folder: Path = Path('data/prices'),
        base_currency: str = 'USDT',
        pairs_to_download: Union[List[str], int, None] = None
    ) -> None:
        """
        Download historical price data from the specified source.
        
        Args:
            source: The data source to download from (COINEX or BINANCE)
            download_folder: Directory where downloaded data will be stored
            base_currency: Base currency for trading pairs (e.g., 'USDT')
            pairs_to_download: Specific pairs to download, can be:
                - List[str]: List of specific pairs
                - int: Number of pairs to download
                - None: Download all available pairs
        
        Returns:
            None
        
        Raises:
            ValueError: If the download folder cannot be created
            Exception: If there's an error during the download process
        """
        try:
            download_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Downloading price data from {source.name} to {download_folder}")
            
            if source == DataSource.COINEX:
                CoinexManager.download_prices(download_folder, base_currency, pairs_to_download)
            elif source == DataSource.BINANCE:
                BinanceManager.download_prices(download_folder, base_currency, pairs_to_download)
            
            logger.info(f"Successfully downloaded price data from {source.name}")
        except Exception as e:
            logger.error(f"Error downloading price data: {str(e)}")
            raise

    @staticmethod
    def get_marketdata_sample(
        data_path: Path = Path('data/coinex_prices_raw'),
        start: Optional[int] = None,
        end: Optional[int] = None,
        duration: Optional[int] = None,
        variation: Optional[float] = None,
        tolerance: float = 0.01,
        normalize: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Get a sample of market data with options for selecting specific segments.
        
        Args:
            data_path: Path to the data file or directory
            start: Start index for time segment selection
            end: End index for time segment selection
            duration: Duration of the segment to select (number of data points)
            variation: Target price variation for the selected segment
            tolerance: Tolerance for the variation target
            normalize: Whether to normalize the price data
        
        Returns:
            Tuple containing:
                - MarketData: The selected market data
                - Dict: Metadata about the selection
        
        Raises:
            ValueError: If no suitable data segment is found or if the data path is invalid
            SchemaError: If the data doesn't conform to the MarketData schema
        """
        metadata = {}
        
        try:
            # Choose data path if a directory is provided
            if data_path.is_dir():
                sample_data_path = DataManager._choose_random_data_path(data_path)
                logger.info(f"Selected random data file: {sample_data_path}")
            else:
                sample_data_path = data_path
                logger.info(f"Using specified data file: {sample_data_path}")
            
            # Read the data
            try:
                df = pd.read_csv(sample_data_path, parse_dates=['date'])
                # Ensure correct data types for MarketData validation
                for col in ['open', 'high', 'low', 'close']:
                    if col in df.columns:
                        df[col] = df[col].astype(np.float64)
                        # Ensure values are positive (required by MarketData schema)
                        if col in ['open', 'high', 'low', 'close'] and (df[col] <= 0).any():
                            min_value = df[col].min()
                            if min_value <= 0:
                                # Add a small offset to make all values positive
                                df[col] = df[col] - min_value + 0.01
                
                if 'volume' in df.columns:
                    df['volume'] = df['volume'].astype(np.float64)
                
                market_data = df
                logger.info(f"Successfully loaded data with {len(market_data)} rows")
            except Exception as e:
                logger.error(f"Error reading data file {sample_data_path}: {str(e)}")
                raise ValueError(f"Failed to read data file: {str(e)}")
            
            # Select segment based on variation if specified
            if duration and variation is not None:
                logger.info(f"Selecting segment with duration={duration}, variation={variation}, tolerance={tolerance}")
                market_data = DataManager._select_variation_segment(duration, variation, tolerance, market_data)
            
            # Select time segment if specified
            if start is not None or end is not None:
                logger.info(f"Selecting time segment with start={start}, end={end}")
                market_data = DataManager._select_time_segment(start, end, market_data)
            
            # Normalize data if requested
            if normalize:
                logger.info("Normalizing data")
                market_data = DataManager._normalize_data(market_data)
            
            # Create metadata
            metadata = {
                'data_path': str(sample_data_path),
                'start': start if start is not None else market_data.index[0],
                'end': end if end is not None else market_data.index[-1],
                'duration': duration,
                'variation': variation,
                'tolerance': tolerance,
                'normalize': normalize,
                'rows': len(market_data)
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            # Validate with MarketData schema before returning
            try:
                validated_data = MarketData(market_data)
                return validated_data, metadata
            except Exception as e:
                logger.warning(f"Data validation error: {str(e)}. Returning raw DataFrame.")
                return market_data, metadata
            
        except SchemaError as e:
            logger.error(f"Data validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting market data sample: {str(e)}")
            raise

    @staticmethod
    def _choose_random_data_path(data_path: Path = Path('data/coinex_prices_raw')) -> Path:
        """
        Select a random data file from the specified directory.
        
        Args:
            data_path: Directory containing data files
        
        Returns:
            Path to the randomly selected data file
        
        Raises:
            ValueError: If no CSV files are found in the directory
        """
        if data_path.is_dir():
            csv_files = [f for f in data_path.glob('*.csv')]
            if not csv_files:
                logger.error(f"No CSV files found in directory: {data_path}")
                raise ValueError(f"No CSV files found in directory: {data_path}")
            data_path = random.choice(csv_files)
            logger.debug(f"Randomly selected data file: {data_path}")
        return data_path
    
    @staticmethod
    def _normalize_data(data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize price data by dividing by the maximum close price.
        
        Args:
            data: Market data to normalize
        
        Returns:
            Normalized market data
        """
        data = data.copy()
        max_close = data['close'].max()
        
        if max_close <= 0:
            logger.warning("Maximum close price is zero or negative, skipping normalization")
            return data
            
        data.loc[:, 'close'] = data['close'] / max_close
        
        # Normalize other price columns if they exist
        for col in ['open', 'high', 'low']:
            if col in data.columns:
                data.loc[:, col] = data[col] / max_close
                
        logger.debug(f"Data normalized by maximum close price: {max_close}")
        return data
    
    # Maximum number of attempts to find a segment with the desired variation
    MAX_ATTEMPTS = 100000
    
    @staticmethod
    def _select_variation_segment(
        duration: int, 
        variation: float, 
        tolerance: float, 
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Select a segment of data with a specific price variation.
        
        Args:
            duration: Length of the segment to select
            variation: Target price variation (as a decimal, e.g., 0.1 for 10%)
            tolerance: Acceptable deviation from the target variation
            data: Market data to select from
        
        Returns:
            Selected segment of market data
        
        Raises:
            ValueError: If no suitable segment is found after maximum attempts
        """
        n = len(data)
        
        if duration >= n:
            logger.warning(f"Requested duration {duration} exceeds data length {n}, returning full dataset")
            return data
        
        logger.info(f"Searching for segment with duration={duration}, variation={variation}, tolerance={tolerance}")
        
        # Initialize segment to None to handle case where no suitable segment is found
        segment = None
        
        for attempt in range(DataManager.MAX_ATTEMPTS):
            start_idx = np.random.randint(0, n - duration)
            end_idx = start_idx + duration
            current_segment = data.iloc[start_idx:end_idx]
                
            start_price = current_segment.iloc[0]['close']
            end_price = current_segment.iloc[-1]['close']
            
            # Avoid division by zero
            if start_price == 0:
                continue
                
            actual_variation = (end_price - start_price) / start_price
                
            if np.isclose(actual_variation, variation, atol=tolerance):
                logger.info(f"Found suitable segment after {attempt+1} attempts: start_idx={start_idx}, end_idx={end_idx}, actual_variation={actual_variation:.4f}")
                return current_segment
            
            # Log progress periodically
            if (attempt + 1) % 10000 == 0:
                logger.debug(f"Searched {attempt+1} segments, continuing...")
        
        logger.error(f"No suitable segment found after {DataManager.MAX_ATTEMPTS} attempts")
        raise ValueError(f"No data segment found with duration {duration} and variation {variation} +/- {tolerance}")

    @staticmethod
    def _select_time_segment(
        start: Optional[int], 
        end: Optional[int], 
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Select a segment of data based on start and end indices.
        
        Args:
            start: Start index (inclusive)
            end: End index (exclusive)
            data: Market data to select from
        
        Returns:
            Selected segment of market data
        """
        if start is not None and end is not None:
            if start >= end:
                logger.warning(f"Start index {start} is greater than or equal to end index {end}, returning empty dataset")
            data = data.iloc[start:end]
        elif start is not None:
            data = data.iloc[start:]
        elif end is not None:
            data = data.iloc[:end]
        
        logger.debug(f"Selected time segment with {len(data)} rows")
        return data


class CoinexManager:
    """
    Manager for downloading and processing data from Coinex exchange.
    """
    
    @staticmethod
    def download_prices(
            download_folder: Path,
            base_currency: str = 'USDT',
            pairs_to_download: Union[List[str], int, None] = None
        ) -> None:
        """
        Download historical price data for specified pairs from Coinex.
        
        Args:
            download_folder: Directory where downloaded data will be stored
            base_currency: Base currency for trading pairs (e.g., 'USDT')
            pairs_to_download: Specific pairs to download, can be:
                - List[str]: List of specific pairs
                - int: Number of pairs to download
                - None: Download all available pairs
        
        Returns:
            None
        
        Raises:
            FileNotFoundError: If the coinex_pairs.txt file is not found
            Exception: If there's an error during the download process
        """
        try:
            # Read available pairs
            pairs_file = Path('data/coinex_pairs.txt')
            if not pairs_file.exists():
                logger.error(f"Coinex pairs file not found: {pairs_file}")
                raise FileNotFoundError(f"Coinex pairs file not found: {pairs_file}")
                
            with open(pairs_file, 'r') as file:
                all_pairs = [line.strip() for line in file]
            
            logger.info(f"Found {len(all_pairs)} pairs in {pairs_file}")
            
            # Filter by base currency if specified
            if base_currency:
                all_pairs = [pair for pair in all_pairs if pair.endswith(f'/{base_currency}')]
                logger.info(f"Filtered to {len(all_pairs)} pairs with base currency {base_currency}")

            # Select pairs to download
            if pairs_to_download is None:
                pairs = all_pairs
                logger.info(f"Will download all {len(pairs)} available pairs")
            elif isinstance(pairs_to_download, int):
                pairs = all_pairs[:pairs_to_download]
                logger.info(f"Will download first {len(pairs)} pairs")
            else:
                pairs = [pair for pair in pairs_to_download if pair in all_pairs]
                logger.info(f"Will download {len(pairs)} specified pairs")

            # Check which pairs already exist
            existing_files = set(file.stem for file in download_folder.glob('*_1m.csv'))
            pairs_to_process = [pair for pair in pairs if f"{pair.split('/')[0].upper()}_{pair.split('/')[1]}_1m" not in existing_files]
            
            if len(pairs_to_process) < len(pairs):
                logger.info(f"Skipping {len(pairs) - len(pairs_to_process)} pairs that already exist")
            
            # Download each pair
            for pair in tqdm(pairs_to_process, desc="Processing pairs"):
                try:
                    CoinexManager.download_pair(pair, download_folder)
                except Exception as e:
                    logger.error(f"Error downloading pair {pair}: {str(e)}")
                    # Continue with next pair instead of stopping the entire process
                    continue
                    
            logger.info(f"Completed downloading {len(pairs_to_process)} pairs from Coinex")
            
        except Exception as e:
            logger.error(f"Error in Coinex download_prices: {str(e)}")
            raise
        
    @staticmethod
    def download_pair(pair: str, download_folder: Path) -> None:
        """
        Download historical data for a specific trading pair from Coinex.
        
        Args:
            pair: Trading pair in format 'BTC/USDT'
            download_folder: Directory where downloaded data will be stored
        
        Returns:
            None
        """
        coin, base = pair.split('/')
        last_month_end = datetime.now().replace(day=1) - timedelta(days=1)
        final_csv_path = download_folder / f"{coin.upper()}_{base}_1m.csv"
        
        # Create file if it doesn't exist
        if not final_csv_path.exists():
            final_csv_path.touch()
            
        months_processed = 0
        
        while True:
            year_month = last_month_end.strftime('%Y-%m')
            url = f"https://file.coinexstatic.com/{coin}{base}-Kline-MINUTE-Spot-{year_month}.zip"
            
            logger.info(f"Downloading data for {coin}/{base} - {year_month}")
            try:
                with requests.get(url, stream=True) as response:
                    if response.status_code != 200:
                        logger.warning(f"No more data available for {coin}/{base} (status code: {response.status_code})")
                        break
                        
                    response.raise_for_status()
                    
                    try:
                        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                            if not zip_ref.namelist():
                                logger.warning(f"Empty zip file for {coin}/{base} in {year_month}")
                                break
                                
                            csv_content = zip_ref.read(zip_ref.namelist()[0]).decode('utf-8')
                            
                            reader = csv.reader(io.StringIO(csv_content))
                            next(reader, None)  # Skip header
                            
                            processed_rows = []
                            for row in reader:
                                if len(row) >= 7:  # Ensure row has enough columns
                                    timestamp = int(row[0])
                                    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                    processed_rows.append(f"{date_str},{row[1]},{row[3]},{row[4]},{row[2]},{row[5]}")
                            
                            if not processed_rows:
                                logger.warning(f"No valid data rows in file for {coin}/{base} in {year_month}")
                                break
                                
                            processed_content = "date,open,high,low,close,volume\n" + '\n'.join(processed_rows)
                            
                            with final_csv_path.open('a') as final_file:
                                if final_csv_path.stat().st_size > 0:
                                    # Skip header if file already has content
                                    processed_content = processed_content.split('\n', 1)[1]
                                final_file.write(processed_content + '\n')
                                
                            months_processed += 1
                            logger.info(f"Processed {len(processed_rows)} rows for {coin}/{base} in {year_month}")
                            
                    except zipfile.BadZipFile:
                        logger.warning(f"Invalid zip file for {coin}{base} in {year_month}")
                        break
                        
                # Move to previous month
                last_month_end = last_month_end.replace(day=1) - timedelta(days=1)

            except requests.RequestException as e:
                logger.error(f"Error downloading data for {coin}{base} in {year_month}: {str(e)}")
                break
                
        logger.info(f"Completed downloading {months_processed} months of data for {coin}/{base}")
        
        # Sort and deduplicate the final file
        if final_csv_path.exists() and final_csv_path.stat().st_size > 0:
            try:
                df = pd.read_csv(final_csv_path, parse_dates=['date'])
                df = df.sort_values('date').drop_duplicates(subset='date', keep='first')
                df.to_csv(final_csv_path, index=False)
                logger.info(f"Sorted and deduplicated data for {coin}/{base}, final row count: {len(df)}")
            except Exception as e:
                logger.error(f"Error processing final CSV for {coin}/{base}: {str(e)}")


class BinanceManager:
    """
    Manager for downloading and processing data from Binance exchange.
    """
    
    @classmethod
    def download_prices(
            cls,
            download_folder: Path,
            base_currency: str = 'USDT',
            pairs_to_download: Union[List[str], int, None] = None
        ) -> None:
        """
        Download historical price data from Binance.
        
        Args:
            download_folder: Directory where downloaded data will be stored
            base_currency: Base currency for trading pairs (e.g., 'USDT')
            pairs_to_download: Specific pairs to download (not currently used for Binance)
        
        Returns:
            None
        
        Raises:
            ImportError: If the binance_historical_data package is not installed
            Exception: If there's an error during the download process
        """
        try:
            from binance_historical_data import BinanceDataDumper
        except ImportError:
            logger.error("binance_historical_data package not installed")
            raise ImportError("Please install binance_historical_data: pip install binance-historical-data")
            
        try:
            download_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Downloading Binance data to {download_folder}")
            
            data_dumper = BinanceDataDumper(
                path_dir_where_to_dump=str(download_folder),
                asset_class="spot",
                data_type="klines",
                data_frequency="1m",
            )
            
            # Filter by base currency and specific pairs if needed
            # Note: This would require extending the BinanceDataDumper functionality
            
            data_dumper.dump_data()
            logger.info("Binance data download completed")
            
            # Format the downloaded data
            raw_download_folder = download_folder
            processed_folder = download_folder / 'processed'
            cls._format_prices(raw_download_folder, processed_folder)
            
        except Exception as e:
            logger.error(f"Error in Binance download_prices: {str(e)}")
            raise
    
    @staticmethod
    def _format_prices(raw_download_folder: Path, processed_folder: Path) -> None:
        """
        Format downloaded Binance data to the standard format used by the system.
        
        Args:
            raw_download_folder: Directory containing raw downloaded data
            processed_folder: Directory where processed data will be stored
        
        Returns:
            None
        """
        try:
            processed_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Formatting Binance data from {raw_download_folder} to {processed_folder}")
            
            currency_pairs_path = raw_download_folder / 'spot' / 'monthly' / 'klines'
            if not currency_pairs_path.exists():
                logger.error(f"Binance data directory not found: {currency_pairs_path}")
                raise FileNotFoundError(f"Binance data directory not found: {currency_pairs_path}")
                
            currency_pairs = [d.name for d in currency_pairs_path.iterdir() if d.is_dir()]
            logger.info(f"Found {len(currency_pairs)} currency pairs to process")
            
            for pair in tqdm(currency_pairs, desc="Processing currency pairs"):
                pair_folder = currency_pairs_path / pair / '1m'
                if not pair_folder.exists():
                    logger.warning(f"No 1m data folder found for {pair}, skipping")
                    continue
                    
                csv_files = list(pair_folder.glob('*.csv'))
                if not csv_files:
                    logger.warning(f"No CSV files found for {pair}, skipping")
                    continue
                
                logger.info(f"Processing {len(csv_files)} CSV files for {pair}")
                
                dfs = []
                for csv_file in tqdm(csv_files, desc=f"Reading CSVs for {pair}", leave=False):
                    try:
                        df = pd.read_csv(csv_file, header=None, names=[
                            "Open time", "Open", "High", "Low", "Close", "Volume",
                            "Close time", "Quote asset volume", "Number of trades",
                            "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
                        ])
                        dfs.append(df)
                    except Exception as e:
                        logger.error(f"Error reading CSV file {csv_file}: {str(e)}")
                        continue
                
                if not dfs:
                    logger.warning(f"No valid data found for {pair}, skipping")
                    continue
                
                try:
                    combined_df = pd.concat(dfs, ignore_index=True)
                    
                    # Convert timestamp to datetime
                    combined_df['date'] = pd.to_datetime(combined_df['Open time'], unit='ms')
                    
                    # Select and rename columns to match our standard format
                    formatted_df = combined_df[['date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                    formatted_df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
                    
                    # Sort and deduplicate
                    formatted_df = formatted_df.sort_values('date').drop_duplicates(subset='date', keep='first')
                    
                    # Determine output filename
                    if 'USDT' in pair:
                        symbol = pair.split('USDT')[0]
                        output_file = processed_folder / f"{symbol}_USDT_1m.csv"
                    else:
                        output_file = processed_folder / f"{pair}_1m.csv"
                    
                    # Save to CSV
                    formatted_df.to_csv(output_file, index=False)
                    logger.info(f"Saved {len(formatted_df)} rows for {pair} to {output_file}")
                    
                except Exception as e:
                    logger.error(f"Error processing data for {pair}: {str(e)}")
                    continue
            
            logger.info("All currency pairs processed successfully")
            
        except Exception as e:
            logger.error(f"Error in _format_prices: {str(e)}")
            raise


if __name__ == "__main__":
    """
    Example usage when script is run directly.
    """
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Format Binance prices
    try:
        BinanceManager._format_prices(
            raw_download_folder=Path('E:/binance_prices_raw_dump'),
            processed_folder=Path('E:/binance_prices_processed'),
        )
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
