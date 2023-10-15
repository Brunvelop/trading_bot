import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

# Agrega el directorio padre al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ahora puedes importar tu módulo
from db import DB


def get_data_from_db():
    db = DB()
    all_orders = db.get_all_orders().data
    return all_orders

# Cargar los datos
all_orders = get_data_from_db()
df = pd.DataFrame(all_orders)
df.to_csv('all_orders.csv', index=False)
orders_df = pd.read_csv('analisys/all_orders.csv')
prices_df = pd.read_csv('data/BTC_EUR_1m.csv')

# Convertir las columnas de timestamp a objetos datetime
orders_df['buy_timestamp'] = pd.to_datetime(orders_df['buy_timestamp'], format='%Y-%m-%dT%H:%M:%S')
prices_df['Datetime'] = pd.to_datetime(prices_df['Datetime'], utc=True)

# Configurar la columna de timestamp como índice para prices_df
prices_df.set_index('Datetime', inplace=True)

# Ajustar los timestamps de las órdenes restando 2 horas
orders_df['buy_timestamp_adj'] = orders_df['buy_timestamp'] - pd.Timedelta(hours=2)

# Filtrar las órdenes para solo aquellas que están abiertas (closed=False)
open_orders_df = orders_df[orders_df['closed'] == False]

# Definir colores para diferentes posiciones
colors = ['red', 'black', 'blue', 'orange', 'purple', 'cyan', 'pink', 'brown', 'grey', 'yellow']
unique_positions = open_orders_df['position'].unique()
position_colors = {pos: colors[i] for i, pos in enumerate(unique_positions)}

# Calcular el precio medio de compra para cada posición usando solo órdenes abiertas
mean_prices_open = open_orders_df.groupby('position')['buy_price'].mean()

# Crear una nueva gráfica
fig, ax = plt.subplots(figsize=(12, 6))

# Graficar los precios de cierre
ax.plot(prices_df.index, prices_df['Close'], label='BTC/EUR', color='blue', linewidth=0.5)

# Graficar los puntos de compra con diferentes colores y líneas de precio medio
for position in unique_positions:
    position_data = open_orders_df[open_orders_df['position'] == position]
    if not position_data.empty:
        ax.plot(position_data['buy_timestamp_adj'], position_data['buy_price'], 'o', 
                color=position_colors.get(position, 'grey'), label=f'Buy Point (Position {position})')
        if position in mean_prices_open:
            ax.axhline(y=mean_prices_open[position], color=position_colors.get(position, 'grey'), linestyle='--', 
                       label=f'Mean Price (Position {position})')

# Formatear los ejes x e y para mostrar las fechas y precios claramente
ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
ax.yaxis.set_minor_locator(mticker.MaxNLocator(integer=True))

# Añadir cuadrícula, etiquetas y título
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.xlabel('Date')
plt.ylabel('Price (EUR)')
plt.title('BTC/EUR Prices with Buy Points and Mean Prices (Open Orders Only)')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.tight_layout()

# Mostrar la gráfica
plt.show()
