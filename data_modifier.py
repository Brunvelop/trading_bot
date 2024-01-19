import os
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def download_currency_data(currency_a='BTC', currency_b='USD', days_to_download=30, interval='15m'):
    end = datetime.today()
    start = end - timedelta(days=days_to_download)
    data = yf.download(f'{currency_a}-{currency_b}', start=start, end=end, interval=interval)
    if data.empty:
        print(f"Error occurred: No data was downloaded for {currency_a}")
    else:
        data = data.drop_duplicates().sort_index()
        if 'Adj Close' in data.columns:
            data = data.drop(columns=['Adj Close'])
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.rename(columns={'Date': 'Datetime'})
    
    filename = f"data/{currency_a}_{currency_b}_{interval}.csv"
    
    if os.path.exists(filename):
        existing_data = pd.read_csv(filename, index_col=0, parse_dates=True)
        data = pd.concat([existing_data, data]).drop_duplicates().sort_index()
        data = data.reset_index()
        data = data.rename(columns={'index': 'Datetime'})
        data = data.drop_duplicates('Datetime', keep='first')

    data.to_csv(filename, index=False)
    return data

download_currency_data(days_to_download=7, interval='1m')
download_currency_data(days_to_download=60, interval='15m')
download_currency_data(days_to_download=720, interval='1h')
download_currency_data(days_to_download=720, interval='1d')

# download_currency_data('BTC', 'USD', days_to_download=7, interval='1m')
# download_currency_data('BTC', 'USD', days_to_download=60, interval='15m')
# download_currency_data('BTC', 'USD', days_to_download=720, interval='1h')
# download_currency_data('BTC', 'USD', days_to_download=720, interval='1d')

data_1m = pd.read_csv('data/BTC_USD_1m.csv', index_col=0, parse_dates=True)
data_15m = pd.read_csv('data/BTC_USD_15m.csv', index_col=0, parse_dates=True)
data_1h = pd.read_csv('data/BTC_USD_1h.csv', index_col=0, parse_dates=True)
data_1d = pd.read_csv('data/BTC_USD_1d.csv', index_col=0, parse_dates=True)


# Crea una figura y un conjunto de subtramas
fig, axs = plt.subplots(4)

# Dibuja los datos en cada subtrama
axs[0].plot(data_1m.index, data_1m['Close'])
axs[0].set_title('1 minute data')

axs[1].plot(data_15m.index, data_15m['Close'])
axs[1].set_title('15 minutes data')

axs[2].plot(data_1h.index, data_1h['Close'])
axs[2].set_title('1 hour data')

axs[3].plot(data_1d.index, data_1d['Close'])
axs[3].set_title('1 day data')

# Ajusta el espacio entre las subtramas
plt.tight_layout()

# Muestra la figura
plt.show()