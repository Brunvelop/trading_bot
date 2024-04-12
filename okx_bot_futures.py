import time
import schedule
import pandas as pd
import plotly.graph_objects as go
from collections import deque

from trader import Trader
from exchange_apis import OKXAPI
from strategies import SuperStrategyFutures 

exchange_api = OKXAPI()
bars_memory = deque(maxlen=1000)
strategy = SuperStrategyFutures()

def update_bars():
    global bars_memory
    bars = exchange_api.get_bars(pair='BTC/USDT', timeframe='1m', limit=300)
    bars = bars[::-1]  # Invierte el orden de los elementos en la lista

    # Convertir bars_memory en un conjunto para la comprobación de pertenencia
    bars_memory_set = set(tuple(bar) for bar in bars_memory)

    # Agregar solo los elementos que no están en bars_memory
    for bar in bars:
        bar_tuple = tuple(bar)
        if bar_tuple not in bars_memory_set:
            bars_memory.append(bar)
            bars_memory_set.add(bar_tuple)

    # Convertir bars_memory en DataFrame para usar con la estrategia
    bars_df = pd.DataFrame(list(bars_memory), columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    
    # Convertir el timestamp a un formato legible para humanos y ajustar a la zona horaria local UTC+2
    bars_df['Time'] = pd.to_datetime(bars_df['Time'], unit='ms', utc=True)
    bars_df['Time'] = bars_df['Time'].dt.tz_convert('Europe/Madrid')  # Asumiendo que 'Europe/Madrid' es UTC+2


    # Calcular los máximos y mínimos con la estrategia
    max_300, min_300 = strategy.calculate_max_min_300(bars_df)

    # Dibujar la gráfica con los máximos y mínimos
    fig = go.Figure(data=[go.Candlestick(x=bars_df['Time'],
                                         open=bars_df['Open'],
                                         high=bars_df['High'],
                                         low=bars_df['Low'],
                                         close=bars_df['Close'])])

    # Agregar líneas horizontales de máximo y mínimo
    fig.add_hline(y=max_300, line=dict(color='Green', width=1, dash='dash'), annotation_text="Max 300")
    fig.add_hline(y=min_300, line=dict(color='Red', width=1, dash='dash'), annotation_text="Min 300")

    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.show()

# Actualizar bars cada minuto
while True:
    print('updating...')
    update_bars()
    time.sleep(60)