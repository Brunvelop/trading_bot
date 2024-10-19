import io
import csv
import random
import requests
import zipfile
from tqdm import tqdm
from pathlib import Path
from enum import Enum, auto
from typing import List, Union
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from definitions import MarketData
from binance_historical_data import BinanceDataDumper

class DataSource(Enum):
    COINEX = auto()
    BINANCE = auto()

class DataManager:
    @staticmethod
    def download_prices(
        source: DataSource = DataSource.COINEX, 
        download_folder: Path = Path('data/prices'),
        base_currency: str = 'USDT',
        pairs_to_download: Union[List[str], int, None] = None
    ) -> None:
        download_folder.mkdir(parents=True, exist_ok=True)
        if source == DataSource.COINEX:
            CoinexManager.download_prices(download_folder, base_currency, pairs_to_download)
        elif source == DataSource.BINANCE:
            BinanceManager.download_prices(download_folder, base_currency, pairs_to_download)

    @staticmethod
    def get_marketdata_sample(
        data_path: Path = Path('data/coinex_prices_raw'),
        start: int = None,
        end: int = None,
        duration: int = None,
        variation: float = None,
        tolerance: float = 0.01,
        normalize: bool = False
    ) -> tuple[MarketData, dict]:
        metadata = {}
        if data_path.is_dir():
            sample_data_path = DataManager._chose_random_data_path(data_path)
        data = pd.read_csv(sample_data_path)
        
        if duration and variation is not None:
            data = DataManager._select_variation_segment(duration, variation, tolerance, data)
        
        if start or end:
            data = DataManager._select_time_segment(start, end, data)
        
        if normalize:
            DataManager._nomralize_data(data)

        metadata = {
            'data_path': str(sample_data_path),
            'start': start if start is not None else data.index[0],
            'end': end if end is not None else data.index[-1],
            'duration': duration,
            'variation': variation,
            'tolerance': tolerance,
            'normalize': normalize
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}

        return data, metadata

    @staticmethod
    def _chose_random_data_path(data_path: Path = Path('data/coinex_prices_raw')) -> Path:
        if data_path.is_dir():
            csv_files = [f for f in data_path.glob('*.csv')]
            if not csv_files:
                raise ValueError(f"No CSV files found in directory: {data_path}")
            data_path = random.choice(csv_files)
        return data_path
    
    @staticmethod
    def _nomralize_data(data: MarketData):
        max_close = data['close'].max()
        data['close'] = data['close'] / max_close
        for col in ['open', 'high', 'low']:
            if col in data.columns:
                data[col] = data[col] / max_close
    
    @staticmethod
    def _select_variation_segment(duration, variation, tolerance, data):
        MAX_ATTEMPS = 100000
        n = len(data)
        for _ in range(MAX_ATTEMPS):
            start_idx = np.random.randint(0, n - duration)
            end_idx = start_idx + duration
            segment = data.iloc[start_idx:end_idx]
                
            start_price = segment.iloc[0]['close']
            end_price = segment.iloc[-1]['close']
            actual_variation = (end_price - start_price) / start_price
                
            if np.isclose(actual_variation, variation, atol=tolerance):
                return segment
        
        raise ValueError(f"No data segment found with duration {duration} and variation {variation} +/- {tolerance}")

    @staticmethod
    def _select_time_segment(start, end, data):
        if start is not None and end is not None:
            data = data.iloc[start:end]
        elif start is not None:
            data = data.iloc[start:]
        elif end is not None:
            data = data.iloc[:end]
        return data

class CoinexManager:
    @staticmethod
    def download_prices(
            download_folder: Path,
            base_currency: str = 'USDT',
            pairs_to_download: Union[List[str], int, None] = None
        ):
        with open('data/coinex_pairs.txt', 'r') as file:
            all_pairs = [line.strip() for line in file]
        
        if base_currency:
            all_pairs = [pair for pair in all_pairs if pair.endswith(f'/{base_currency}')]

        if pairs_to_download is None:
            pairs = all_pairs
        elif isinstance(pairs_to_download, int):
            pairs = all_pairs[:pairs_to_download]
        else:
            pairs = [pair for pair in pairs_to_download if pair in all_pairs]

        existing_files = set(file.stem for file in download_folder.glob('*_1m.csv'))
        pairs_to_process = [pair for pair in pairs if f"{pair.split('/')[0].upper()}_{pair.split('/')[1]}_1m" not in existing_files]
        for pair in tqdm(pairs_to_process, desc="Processing pairs"):
            CoinexManager.download_pair(pair, download_folder)
        
    @staticmethod
    def download_pair(pair: str, download_folder: Path) -> None:
        coin, base = pair.split('/')
        last_month_end = datetime.now().replace(day=1) - timedelta(days=1)
        
        while True:
            year_month = last_month_end.strftime('%Y-%m')
            url = f"https://file.coinexstatic.com/{coin}{base}-Kline-MINUTE-Spot-{year_month}.zip"
            final_csv_path = download_folder / f"{coin.upper()}_{base}_1m.csv"
            
            print(f"Downloading data for {coin}/{base} - {year_month}")
            try:
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                        csv_content = zip_ref.read(zip_ref.namelist()[0]).decode('utf-8')
                        
                        reader = csv.reader(io.StringIO(csv_content))
                        next(reader, None)  # Skip header
                        processed_content = "date,open,high,low,close,volume\n" + \
                            ''.join(f"{datetime.fromtimestamp(int(row[0])).strftime('%Y-%m-%d %H:%M:%S')},{row[1]},{row[3]},{row[4]},{row[2]},{row[5]}\n" 
                                    for row in reader if len(row) >= 7)
                        
                        with final_csv_path.open('a') as final_file:
                            final_file.write(processed_content if not final_csv_path.stat().st_size 
                                            else processed_content.split('\n', 1)[1])

                last_month_end = last_month_end.replace(day=1) - timedelta(days=1)

            except requests.RequestException as e:
                print(f"Error downloading data for {coin}{base} in {year_month}: {e}")
                break
            except zipfile.BadZipFile:
                print(f"Invalid zip file for {coin}{base} in {year_month}. Moving to next pair.")
                break

class BinanceManager:
    @classmethod
    def download_prices(
            cls,
            download_folder: Path,
            base_currency: str = 'USDT',
            pairs_to_download: Union[List[str], int, None] = None
        ):
        download_folder.mkdir(parents=True, exist_ok=True)
        
        data_dumper = BinanceDataDumper(
            path_dir_where_to_dump=str(download_folder),
            asset_class="spot",
            data_type="klines",
            data_frequency="1m",
        )
        data_dumper.dump_data()

        cls._format_prices()
    
    @staticmethod
    def _format_prices(raw_download_folder: Path, processed_folder: Path):
        processed_folder.mkdir(parents=True, exist_ok=True)
        
        currency_pairs_path = raw_download_folder / 'spot' / 'monthly' / 'klines'
        currency_pairs = [d.name for d in currency_pairs_path.iterdir() if d.is_dir()]
        for pair in tqdm(currency_pairs, desc="Processing currency pairs"):
            pair_folder = currency_pairs_path / pair / '1m'
            csv_files = list(pair_folder.glob('*.csv'))
            
            if not csv_files:
                continue
            
            dfs = []
            for csv_file in tqdm(csv_files, desc=f"Reading CSVs for {pair}", leave=False):
                df = pd.read_csv(csv_file, header=None, names=[
                    "Open time", "Open", "High", "Low", "Close", "Volume",
                    "Close time", "Quote asset volume", "Number of trades",
                    "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
                ])
                dfs.append(df)
            
            combined_df = pd.concat(dfs, ignore_index=True)
            
            combined_df['date'] = pd.to_datetime(combined_df['Open time'], unit='ms')
            formatted_df = combined_df[['date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            formatted_df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            
            formatted_df = formatted_df.sort_values('date').drop_duplicates(subset='date', keep='first')
            
            output_file = processed_folder / f"{pair.split('USDT')[0]}_USDT_1m.csv"

            formatted_df.to_csv(output_file, index=False)
            
        print("All currency pairs processed successfully.")
        

if __name__ == "__main__":
    BinanceManager._format_prices(
        raw_download_folder=Path('E:/binance_prices_raw_dump'),
        processed_folder=Path('E:/binance_prices_processed'),
    )

