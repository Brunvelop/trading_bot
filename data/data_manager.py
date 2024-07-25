import io
import csv
import requests
import zipfile
from tqdm import tqdm
from pathlib import Path
from enum import Enum, auto
from typing import List, Union
from datetime import datetime, timedelta

class DataSource(Enum):
    COINEX = auto()

class DataManager:
    
    @staticmethod
    def download_prices(
        source: DataSource = DataSource.COINEX, 
        download_folder: Path = Path('data/prices'),
        base_currency: str = 'USDT',
        pairs_to_download: Union[List[str], int, None] = None
    ) -> None:
        """
        Descarga los precios desde una fuente específica y los guarda en la carpeta raw.
        """
        download_folder.mkdir(parents=True, exist_ok=True)

        if source == DataSource.COINEX:
            CoinexManager.download_prices(download_folder, base_currency, pairs_to_download)
        pass

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


        for pair in tqdm(pairs, desc="Processing pairs"):
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
                            ''.join(f"{row[0]},{row[1]},{row[3]},{row[4]},{row[2]},{row[5]}\n" 
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
    DataManager.download_prices(
        source = DataSource.COINEX,
        download_folder = Path('data/coinex_prices_raw'),
        base_currency = 'USDT',
        pairs_to_download = 3
    )
