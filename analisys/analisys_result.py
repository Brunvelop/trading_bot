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
# df.to_csv('all_orders.csv', index=False)
orders = pd.read_csv('analisys/all_orders.csv' )
btc_eur = pd.read_csv('data/BTC_EUR_1m.csv')

# Convertir las cadenas de texto a objetos datetime y asegurar que las zonas horarias son consistentes
btc_eur['Datetime'] = pd.to_datetime(btc_eur['Datetime'], utc=True)
orders['buy_timestamp'] = pd.to_datetime(orders['buy_timestamp'], utc=True)
orders['sell_timestamp'] = pd.to_datetime(orders['sell_timestamp'], utc=True)

# Ajustar la marca de tiempo de compra restando 2 horas
orders['buy_timestamp'] = orders['buy_timestamp'] - timedelta(hours=2)

# Asegurarse de que las marcas de tiempo en btc_eur son únicas y establecerlas como índice
btc_eur = btc_eur.drop_duplicates(subset='Datetime', keep='last').set_index('Datetime')

# Establecer las marcas de tiempo como índice para las órdenes también
orders = orders.set_index('buy_timestamp').sort_index()

# Calcular la ganancia/pérdida para las posiciones cerradas
closed_orders = orders[orders['closed']].copy()
closed_orders['profit'] = closed_orders['sell_cost'] - closed_orders['buy_cost'] - closed_orders['buy_fees'] - closed_orders['sell_fees']

# Calcular la ganancia/pérdida para las posiciones abiertas
open_orders = orders[~orders['closed']].copy()
current_price = btc_eur['Close'].iloc[-1]  # Último precio en el conjunto de datos
open_orders['profit'] = (current_price * open_orders['buy_amount']) - open_orders['buy_cost'] - open_orders['buy_fees']

# Concatenar los datos de ganancia/pérdida y ordenar por marca de tiempo
all_profits = pd.concat([closed_orders, open_orders])['profit'].sort_index().cumsum()

# Crear una figura con dos subgráficas
fig, ax = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
fig.subplots_adjust(hspace=0.4)

# Subgráfica 1: Precio y órdenes de compra y venta
ax[0].plot(btc_eur.index, btc_eur['Close'], label='BTC/EUR Price', color='blue', alpha=0.8)
ax[0].set_ylabel('Price (EUR)', color='blue')
ax[0].tick_params(axis='y', labelcolor='blue')
ax2 = ax[0].twinx()
ax2.scatter(orders.index, orders['buy_price'], label='Buy Orders', color='red', marker='x')
ax2.scatter(orders['sell_timestamp'], orders['sell_price'], label='Sell Orders', color='black', marker='o')
ax2.set_ylabel('Order Price (EUR)', color='red')
ax2.tick_params(axis='y', labelcolor='red')
ax[0].set_title('BTC/EUR Price, Buy Orders, and Sell Orders Over Time')
ax[0].grid(True, which='both', linestyle='--', linewidth=0.5)
ax2.legend(loc='upper left')

# Subgráfica 2: Ganancia acumulativa
ax[1].plot(all_profits.index, all_profits, label='Cumulative Profit', color='green')
ax[1].axhline(y=0, color='black', linestyle='--', linewidth=0.8)
ax[1].set_title('Total Cumulative Profit Over Time')
ax[1].set_xlabel('Datetime')
ax[1].set_ylabel('Cumulative Profit (EUR)')
ax[1].grid(True, which='both', linestyle='--', linewidth=0.5)
ax[1].legend()

# Formatear el eje x para mejor legibilidad
for axis in ax:
    axis.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    axis.tick_params(axis='x', rotation=45)

# Ajustar el diseño para mejor legibilidad
plt.tight_layout()
plt.show()