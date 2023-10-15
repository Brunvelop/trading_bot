import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import DB

def get_data_from_db():
    db = DB()
    all_orders = db.get_all_orders().data
    return all_orders

# Cargar los datos
all_orders = get_data_from_db()
df = pd.DataFrame(all_orders)
df.to_csv('analisys/all_orders.csv', index=False)

# --- Load Data ---
orders_df = pd.read_csv('analisys/all_orders.csv')
btc_price_df = pd.read_csv('data/BTC_EUR_1m.csv')

# --- Data Preprocessing ---
# Convert timestamps and adjust time zones
orders_df['buy_timestamp'] = pd.to_datetime(orders_df['buy_timestamp'])
orders_df['sell_timestamp'] = pd.to_datetime(orders_df['sell_timestamp'])
btc_price_df['Datetime'] = pd.to_datetime(btc_price_df['Datetime'], utc=True)
btc_price_df['AdjustedDatetime'] = btc_price_df['Datetime'] + timedelta(hours=2)

# --- Profit Calculations ---
# Last BTC price for open orders profitability calculation
last_btc_price = btc_price_df['Close'].iloc[-1]

# Calculating profitability for closed orders
closed_orders = orders_df[orders_df['closed']].copy()
closed_orders['profit'] = (
    (closed_orders['sell_price'] * closed_orders['sell_amount'] - closed_orders['sell_fees']) -
    (closed_orders['buy_price'] * closed_orders['buy_amount'] + closed_orders['buy_fees'])
)

# Calculating profitability for open orders using the last BTC price
open_orders = orders_df[~orders_df['closed']].copy()
open_orders['sell_price'] = last_btc_price  # Assuming the sell price as the last known price
open_orders['sell_amount'] = open_orders['buy_amount']  # Assuming the sell amount as the buy amount
open_orders['profit'] = (
    (open_orders['sell_price'] * open_orders['sell_amount']) -  # No sell fees for open orders
    (open_orders['buy_price'] * open_orders['buy_amount'] + open_orders['buy_fees'])
)

# Concatenating closed and open orders and sorting by buy_timestamp
all_orders_with_profit = pd.concat([closed_orders, open_orders]).sort_values(by='buy_timestamp').reset_index(drop=True)

# Calculating cumulative profit
all_orders_with_profit['cumulative_profit'] = all_orders_with_profit['profit'].cumsum()

# --- Visualization ---
plt.style.use('seaborn-darkgrid')
palette = plt.get_cmap('Set1')
fig, ax = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# Plot 1: Cumulative Profit Over Time
ax[0].plot(all_orders_with_profit['buy_timestamp'], all_orders_with_profit['cumulative_profit'], marker='', color='blue', linewidth=2.5, alpha=0.9, label='Rentabilidad acumulada')
ax[0].set_title('Rentabilidad Acumulada y Puntos de Compra/Venta en el Tiempo', loc='left', fontsize=12, fontweight=0, color='orange')
ax[0].set_ylabel('Rentabilidad Acumulada (EUR)')

# Plot 2: Buy/Sell Points Over BTC Price
ax[1].plot(btc_price_df['AdjustedDatetime'], btc_price_df['Close'], color='skyblue', label='Precio de BTC')
ax[1].scatter(closed_orders['buy_timestamp'], closed_orders['buy_price'], color='green', s=50, label='Compra')
ax[1].scatter(closed_orders['sell_timestamp'], closed_orders['sell_price'], color='red', s=50, label='Venta')
ax[1].scatter(open_orders['buy_timestamp'], open_orders['buy_price'], color='green', s=50)
ax[1].set_ylabel('Precio de BTC (EUR)')
ax[1].xaxis.set_major_locator(mdates.DayLocator(interval=1))
ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax[1].legend(loc=2, ncol=2)

plt.tight_layout()
plt.show()
