import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import strategies

from db import DB

def get_all_orders(db):
    result = []
    last_id = 0
    limit = 1000

    while True:
        response = db.supabase.table(db.table_name).select('*').order('id', ascending=True).range(last_id, last_id + limit - 1).execute()
        data = response.data
        result.extend(data)

        if len(data) < limit:
            break

        last_id = data[-1]['id']

    return result


db = DB('okx_ordi_usdt_SMASELL')
memory = db.get_all_orders()
fee = 0.0005
#Fix data
memory_df = pd.DataFrame(memory)
memory_df['timestamp'] = pd.to_datetime(memory_df['timestamp']).dt.tz_localize(None)
memory_df


# Corrigiendo el nombre de la columna 'id '
buy_trades = memory_df[memory_df['type'] == 'buy_market']
sell_trades = memory_df[memory_df['type'] == 'sell_market']

# Reajustando el proceso de asociación y cálculo de ganancias
associated_sales = []
total_profit = 0

for index, sell_trade in sell_trades.iterrows():
    for _, buy_trade in buy_trades.iterrows():
        if sell_trade['price'] > buy_trade['price'] * (1 + fee):
            profit = (sell_trade['price'] - buy_trade['price']) * sell_trade['amount']
            profit -= sell_trade['price'] * sell_trade['amount'] * fee
            profit -= buy_trade['price'] * buy_trade['amount'] * fee

            total_profit += profit

            associated_sales.append(sell_trade['id '])
            buy_trades = buy_trades.drop(buy_trade.name)
            break

open_positions = len(buy_trades)

# Asegúrate de que 'timestamp' es una columna en memory_df y es de tipo datetime
memory_df['timestamp'] = pd.to_datetime(memory_df['timestamp'])

# Calcula el tiempo total transcurrido
total_time = memory_df['timestamp'].max() - memory_df['timestamp'].min()

# Calcula el número de días
total_days = total_time.days

# Calcula la ganancia media diaria
average_daily_profit = total_profit / total_days

# Ganancia máxima y mínima en una sola operación
profits = sell_trades['price'] - buy_trades['price']
max_profit = profits.max()
min_profit = profits.min()

# Número total de operaciones de compra y venta
total_buy_trades = len(buy_trades)
total_sell_trades = len(sell_trades)

# Ganancia total por tipo de operación
total_buy_profit = (buy_trades['price'] * (1 - fee)).sum()
total_sell_profit = (sell_trades['price'] * (1 - fee)).sum()

max_profit, min_profit, total_buy_trades, total_sell_trades, total_buy_profit, total_sell_profit


# Imprime el tiempo total transcurrido
print(f"Tiempo total transcurrido: {total_time}")

# Imprime la ganancia media diaria
print(f"Ganancia media diaria: {average_daily_profit}")

# Imprime la ganancia máxima y mínima en una sola operación
print(f"Ganancia máxima en una sola operación: {max_profit}")
print(f"Ganancia mínima en una sola operación: {min_profit}")

# Imprime el número total de operaciones de compra y venta
print(f"Número total de operaciones de compra: {total_buy_trades}")
print(f"Número total de operaciones de venta: {total_sell_trades}")

# Imprime la ganancia total por tipo de operación
print(f"Ganancia total de operaciones de compra: {total_buy_profit}")
print(f"Ganancia total de operaciones de venta: {total_sell_profit}")