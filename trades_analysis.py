import pandas as pd
import matplotlib.pyplot as plt
from plots_utils import draw_graphs
from datetime import datetime
['Datetime', 'Open', 'Close', 'High', 'Low', 'Volume', 'timestamp',
       'pair', 'type', 'price', 'amount', 'total_value', 'fee', 'balance_a',
       'balance_b', 'hold_value']


df = pd.read_csv('data/trades/2024-06.csv', parse_dates=['Date'])

# Agrupar por fecha y moneda, y agregar los valores
df_grouped = df.groupby(['Date', 'Coin']).agg({
    'Amount': 'sum',
    'Fee': 'sum',
    'Available': 'last'
}).reset_index()

# Separar las filas de DOG y USDT
dog_df = df_grouped[df_grouped['Coin'] == 'DOG'].reset_index(drop=True)
usdt_df = df_grouped[df_grouped['Coin'] == 'USDT'].reset_index(drop=True)

# Calcular el precio de cierre
price = usdt_df['Amount'].abs() / dog_df['Amount'].abs()

# Crear DataFrame para visualización
visualization_df = pd.DataFrame({
    'Datetime': dog_df['Date'],
    'Close': price,
    'timestamp': dog_df['Date'],  # Convertir a segundos
    'pair': 'DOG/USDT',
    'type': ['sell_market' if amount < 0 else 'buy_market' for amount in dog_df['Amount']],
    'price': price,
    'amount': dog_df['Amount'].abs(),
    'total_value': (usdt_df['Available'].abs() + dog_df['Available'].abs() * price),
    'balance_a': dog_df['Available'],
    'balance_b': usdt_df['Available']
})

# Calcular hold_value (asumiendo que es el valor si hubiéramos mantenido DOG)
visualization_df['hold_value'] = visualization_df['balance_a'] * visualization_df['Close']

# Ordenar por timestamp para asegurar que los datos estén en orden cronológico
visualization_df = visualization_df.sort_values('timestamp')

# Convertir 'Datetime' a datetime si no lo es ya
visualization_df['Datetime'] = pd.to_datetime(visualization_df['Datetime'])



plot_modes = ['Close', 'balance_a', 'balance_b', 'total_value', 'hold_value', 'price']
draw_graphs(visualization_df, plot_modes)