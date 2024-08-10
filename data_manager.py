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

class DataSource(Enum):
    COINEX = auto()

class DataManager:

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
        max_close = data['Close'].max()
        data['Close'] = data['Close'] / max_close
        for col in ['Open', 'High', 'Low']:
            if col in data.columns:
                data[col] = data[col] / max_close
    
    @staticmethod
    def _select_variation_segment(duration, variation, tolerance, data):
        MAX_ATTEMPS = 10000
        n = len(data)
        for _ in range(MAX_ATTEMPS):
            start_idx = np.random.randint(0, n - duration)
            end_idx = start_idx + duration
            segment = data.iloc[start_idx:end_idx]
                
            start_price = segment.iloc[0]['Close']
            end_price = segment.iloc[-1]['Close']
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
        pass

    @staticmethod
    def get_data_sample(
        data_path: Path = Path('data/coinex_prices_raw'),
        start: int = None,
        end: int = None,
        duration: int = None,
        variation: float = None,
        tolerance: float = 0.01,
        normalize: bool = False
    ) -> pd.DataFrame:
        metadata = {}
        if data_path.is_dir():
            data_path = DataManager._chose_random_data_path(data_path)
        data = pd.read_csv(data_path)
        metadata['data_path'] = str(data_path)
        
        if duration and variation:
            data = DataManager._select_variation_segment(duration, variation, tolerance, data)
        
        if start or end:
            data = DataManager._select_time_segment(start, end, data)
        
        if normalize:
            DataManager._nomralize_data(data)

        metadata = {
            'data_path': str(data_path),
            'start': start,
            'end': end,
            'duration': duration,
            'variation': variation,
            'tolerance': tolerance,
            'normalize': normalize
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}

        return data, metadata


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
                        processed_content = "Date,Open,High,Low,Close,Volume\n" + \
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
        

if __name__ == "__main__":
    # DataManager.download_prices(
    #     source = DataSource.COINEX,
    #     download_folder = Path('data/coinex_prices_raw2'),
    #     base_currency = 'USDT',
    #     pairs_to_download = 2
    # )
    data_config={
            'data_path': Path('data/coinex_prices_raw'),
            'duration': 4320,
            'variation': 50.05,
            'tolerance': 0.01,
            'normalize': True
    }
    data, metadata = DataManager.get_data_sample(**data_config)
    print(data)
