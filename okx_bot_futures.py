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

    ma_200 = indicators.calculate_ma(bars_df, 200)

    max_300 = indicators.calculate_max(bars_df, 300)
    min_300 = indicators.calculate_min(bars_df, 300)

    volatility = indicators.calculate_volatility(bars_df)
    avg_vol_10 = indicators.calculate_avg_volatility(volatility, 10)
    avg_vol_50 = indicators.calculate_avg_volatility(volatility, 50)
    avg_vol_100 = indicators.calculate_avg_volatility(volatility, 100)
    avg_vol_200 = indicators.calculate_avg_volatility(volatility, 200)

    last_price = bars_df['Close'].iloc[-1] 
    break_max_300 = last_price > max_300
    break_min_300 = last_price < min_300
    volatility_up = (avg_vol_10 > avg_vol_50) & (avg_vol_50 > avg_vol_100) & (avg_vol_100 > avg_vol_200)

    indicators_data = {
        'ma_200': ma_200,
        'volatility': volatility,
        'max_300': max_300, 
        'min_300': min_300,
        'avg_vol_10': avg_vol_10,
        'avg_vol_50': avg_vol_50,
        'avg_vol_100': avg_vol_100,
        'avg_vol_200': avg_vol_200,
        'volatility_up': volatility_up,
        'break_max_300': break_max_300,
        'break_min_300': break_min_300,
    }

    position = exchange_api.fetchPosition(PAIR)
    if position.get('contracts'):
        return bars_df, indicators_data
        
    if break_max_300 and volatility_up:
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

    elif break_min_300 and volatility_up:
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
                    
    return bars_df, indicators_data


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