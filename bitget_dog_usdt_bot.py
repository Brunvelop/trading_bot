import time
import schedule

import pandas as pd

from trader import Trader
from exchange_apis import BitgetAPI
from strategies import MultiMovingAverageStrategySell, MultiMovingAverageStrategy

fee = 0.002
trader = Trader(
    strategy= MultiMovingAverageStrategy(cost=5.1, fee=2*fee), #Cost es precio TOTAL USDT
    db_name = 'bitget_dog_usdt',
    exange_api = BitgetAPI(api_key="BITGET_API_KEY_DOG_USDT_BOT", api_secret="BITGET_API_SECRET_DOG_USDT_BOT"),
    pair = 'DOG/USDT',
)

def job():
    try:
        start_time = time.time()  # Inicio del tiempo de ejecución

        print("----------- RUN -----------")
        data = trader.exange_api.get_bars(pair=trader.pair, timeframe='1min', limit=200)
        data = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        data = data.iloc[::-1]

        memory = {}
        memory['orders'] = trader.db.get_all_orders()
        memory['balance'] = trader.exange_api.get_account_balance('DOG')


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