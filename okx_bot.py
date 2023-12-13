import time
import schedule

import pandas as pd

from trader import Trader
from exchange_apis import OKXAPI
from strategies import StandardDeviationStrategy 

fee = 0.0005
trader = Trader(
    strategy= StandardDeviationStrategy(cost=100, fee=2*fee),
    db_name = 'okx_btc_usdt',
    exange_api = OKXAPI(),
    pair = 'SOL/USDT:USDT',
)

def job():
    try:
        start_time = time.time()  # Inicio del tiempo de ejecución
        print("----------- RUN -----------")
        data = trader.exange_api.get_bars(pair=trader.pair, timeframe='1m', limit=200)
        data = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        data = data.iloc[::-1] #Kraken manda invertidos los datos
        memory = trader.db.get_all_orders()
        trader.execute_strategy(data, memory)
        end_time = time.time()  # Fin del tiempo de ejecución
        print("Tiempo de ejecución: {} segundos".format(end_time - start_time))
    except Exception as e:
        print("Se produjo un error: ", e)

schedule.every().minute.at(":06").do(job)

while True:
    # print("Esperando el próximo trabajo...")
    schedule.run_pending()
    time.sleep(1)