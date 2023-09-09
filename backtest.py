from tqdm import tqdm
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from tqdm import tqdm
import yfinance as yf

def download_currency_data(currency='BTC', days_to_download=30, interval='1h'):
    end = datetime.today()
    start = end - timedelta(days=days_to_download)
    data = yf.download(f'{currency}-USD', start=start, end=end, interval=interval)
    if data.empty:
        print(f"Error occurred: No data was downloaded for {currency}")
    else:
        data = data.drop_duplicates().sort_index()
    return data


def calculate_strategy_1(data):
    # Calculate the 200 hour moving average
    data['MA200'] = data['Close'].rolling(window=200).mean()

    # Define the strategy
    data['Buy_Signal'] = (data['Close'] < data['MA200'])
    data['Sell_Signal'] = (data['Close'] > data['MA200'])
    return data

def calculate_strategy_2(data):
    # Calculate the moving averages
    data['MA10'] = data['Close'].rolling(window=10).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA100'] = data['Close'].rolling(window=100).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()

    # Define the strategy
    data['Buy_Signal'] = (data['Close'] < data[['MA10', 'MA50', 'MA100', 'MA200']].min(axis=1)) & (data['MA10'] < data['MA50']) & (data['MA50'] < data['MA100']) & (data['MA100'] < data['MA200'])
    data['Sell_Signal'] = (data['Close'] > data[['MA10', 'MA50', 'MA100', 'MA200']].max(axis=1)) & (data['MA10'] > data['MA50']) & (data['MA50'] > data['MA100']) & (data['MA100'] > data['MA200'])
    
    return data

def calculate_strategy_3(data):
    # Calculate the moving averages
    data['MA10'] = data['Close'].rolling(window=10).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA100'] = data['Close'].rolling(window=100).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()

    # Calculate the bar range as a percentage of the close price
    data['BarRange'] = abs(data['High'] - data['Low']) / data['Low'] * 100

    # Calculate the exponential moving averages of the BarRange
    data['avgRange10'] = data['BarRange'].ewm(span=10).mean()
    data['avgRange50'] = data['BarRange'].ewm(span=50).mean()
    data['avgRange100'] = data['BarRange'].ewm(span=100).mean()
    data['avgRange200'] = data['BarRange'].ewm(span=200).mean()

    # Define the strategy
    data['Buy_Signal'] = (data['Close'] < data[['MA10', 'MA50', 'MA100', 'MA200']].min(axis=1)) & (data['MA10'] < data['MA50']) & (data['MA50'] < data['MA100']) & (data['MA100'] < data['MA200']) & (data['avgRange10'] < data['avgRange50']) & (data['avgRange50'] < data['avgRange100']) & (data['avgRange100'] < data['avgRange200'])
    data['Sell_Signal'] = (data['Close'] > data[['MA10', 'MA50', 'MA100', 'MA200']].max(axis=1)) & (data['MA10'] > data['MA50']) & (data['MA50'] > data['MA100']) & (data['MA100'] > data['MA200'])

    return data

def backtest(data, usd_balance=10000.0, coin_balance=0.0, buy_amount=10):
    purchases = pd.DataFrame(columns=['Timestamp', 'Buy_Amount_USD', 'Quantity_BTC', 'Balance_USD', 'Balance_BTC', 'Total_Value_USD', 'Is_Sold', 'Sell_Amount_USD', 'Sell_Quantity_BTC', 'Sell_Timestamp'])
    balances = pd.DataFrame(columns=['Timestamp', 'Balance_USD', 'Balance_BTC', 'Total_Value_USD'])
    total_value = usd_balance
    
    for i, row in tqdm(data.iterrows(), total=data.shape[0]):
        # Comprar
        if row['Buy_Signal'] and usd_balance >= buy_amount:
            quantity = buy_amount / row['Close']
            coin_balance += quantity
            usd_balance -= buy_amount
            total_value = usd_balance + coin_balance * row['Close']
            new_purchase = pd.DataFrame(
                {
                    'Timestamp': [i], 
                    'Buy_Amount_USD': [buy_amount],
                    'Quantity_BTC': [quantity], 
                    'Balance_USD': [usd_balance],
                    'Balance_BTC': [coin_balance],
                    'Total_Value_USD': [total_value],
                    'Is_Sold': 0,
                    'Sell_Amount_USD': [None],
                    'Sell_Quantity_BTC': [None],
                    'Sell_Timestamp': [None]
                }
            )
            purchases = pd.concat([purchases, new_purchase], ignore_index=True)
        # Vender
        elif row['Sell_Signal'] and coin_balance > 0:
            # Buscar la compra más antigua con al menos un 2% de rentabilidad
            for j, purchase in purchases.iterrows():
                if (row['Close'] - purchase['Buy_Amount_USD']) / purchase['Buy_Amount_USD'] >= 0.02 and not purchase['Is_Sold']:
                    # Vender
                    sell_amount = purchase['Quantity_BTC'] * row['Close']
                    sell_quantity = purchase['Quantity_BTC']
                    usd_balance += sell_amount
                    coin_balance -= sell_quantity
                    total_value = usd_balance + coin_balance * row['Close']
                    # Actualizar el DataFrame de compras
                    purchases.at[j, 'Is_Sold'] = 1
                    purchases.at[j, 'Sell_Amount_USD'] = sell_amount
                    purchases.at[j, 'Sell_Quantity_BTC'] = sell_quantity
                    purchases.at[j, 'Sell_Timestamp'] = i
                    break

        # Almacenar balances
        new_balance = pd.DataFrame(
            {
                'Timestamp': [i],
                'Balance_USD': [usd_balance],
                'Balance_BTC': [coin_balance],
                'Total_Value_USD': [total_value]
            }
        )
        balances = pd.concat([balances, new_balance], ignore_index=True)

    return purchases, balances

def plot_data(data, purchases, balances):
    fig, ax = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

    # Plot strategy on the first graph
    ax[0].plot(data.index, data['Close'], label='Close Price', color='blue')
    ax[0].plot(data.index, data['MA200'], label='200 Hour MA', color='red')
    ax[0].plot(data.index, data['MA10'], label='10 Hour MA', color='cyan')
    ax[0].plot(data.index, data['MA50'], label='50 Hour MA', color='magenta')
    ax[0].plot(data.index, data['MA100'], label='100 Hour MA', color='yellow')
    ax[0].plot(data[data['Buy_Signal']].index, data['Close'][data['Buy_Signal']], '^', markersize=3, color='g', label='buy')
    ax[0].plot(data[data['Sell_Signal']].index, data['Close'][data['Sell_Signal']], 'v', markersize=3, color='r', label='sell')
    ax[0].set(xlabel='Date', ylabel='Close Price')
    ax[0].grid(True)
    ax[0].legend()

    # Convert Timestamp to datetime
    purchases['Timestamp'] = pd.to_datetime(purchases['Timestamp']).dt.to_pydatetime()

    # Plot balances and total value on the second graph
    ax[1].plot(balances['Timestamp'], balances['Balance_USD'], label='USD Balance', color='green')

    # Create a second y-axis for the BTC balance
    ax2 = ax[1].twinx()
    ax2.plot(balances['Timestamp'], balances['Balance_BTC'], label='BTC Balance', color='orange')

    ax[1].plot(balances['Timestamp'], balances['Total_Value_USD'], label='Total Value in USD', color='blue')
    ax[1].set(ylabel='Amount (USD)')
    ax2.set_ylabel('Amount (BTC)')
    ax[1].grid(True)

    # Add legends for both y-axes
    ax[1].legend(bbox_to_anchor=(0.88, 1), loc='upper left')
    ax2.legend(bbox_to_anchor=(0.88, 0.9), loc='upper left')

    plt.tight_layout()
    plt.show()


coin = 'BTC'
coin_data_1h = download_currency_data(coin, days_to_download=730, interval='1h')
coin_data_1h_signals = calculate_strategy_3(coin_data_1h)
purchases, balances = backtest(coin_data_1h_signals, buy_amount=100)
print()
plot_data(coin_data_1h_signals, purchases, balances)


