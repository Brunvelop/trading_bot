import time
import schedule
import pandas as pd
from collections import deque
from exchange_apis import OKXAPI
from indicators import Indicators

# Configuración inicial
VISUALIZATION = True 
exchange_api = OKXAPI()
bars_memory = deque(maxlen=1000)
indicators = Indicators()
PAIR = 'ORDI/USDT:USDT'

def get_bars():
    global bars_memory
    bars = exchange_api.get_bars(pair='ORDI/USDT:USDT', timeframe='1m', limit=300)
    bars = bars[::-1]  # Invierte el orden de los elementos en la lista

    # Actualizar bars_memory
    bars_memory_set = set(tuple(bar) for bar in bars_memory)
    for bar in bars:
        bar_tuple = tuple(bar)
        if bar_tuple not in bars_memory_set:
            bars_memory.append(bar)
            bars_memory_set.add(bar_tuple)

    # Convertir bars_memory en DataFrame para usar con la estrategia
    bars_df = pd.DataFrame(list(bars_memory), columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    bars_df['Time'] = pd.to_datetime(bars_df['Time'], unit='ms', utc=True)
    bars_df['Time'] = bars_df['Time'].dt.tz_convert('Europe/Madrid')

    return bars_df


def job():
    bars_df = get_bars()
    max_300, min_300 = indicators.calculate_max_min(bars_df, 10)

    last_price = bars_df['Close'].iloc[-1]  # Precio de cierre de la última vela

#######################################################
    if last_price > max_300:
        exchange_api.create_order_with_tp_and_sl(
            pair=PAIR,
            side='buy',
            amount=1,
            price=last_price,
            sl_price=last_price*0.985,
            tp_price = last_price*1.015,
            leverage=50,
            order_type='market'
        )

    elif last_price < min_300:
        exchange_api.create_order_with_tp_and_sl(
            pair=PAIR,
            side='sell',
            amount=1,
            price=last_price,
            sl_price=last_price*0.985,
            tp_price = last_price*1.015,
            leverage=50,
            order_type='market'
        )
                    
    return bars_df, max_300, min_300


if __name__ == '__main__':
    if VISUALIZATION:
        from visualizator import Visualizator

        visualizator = Visualizator(job)
        visualizator.run()
    else:
        schedule.every().minute.at(":05").do(job)
        while True:
            schedule.run_pending()
            time.sleep(1)