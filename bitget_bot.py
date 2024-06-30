import time
import schedule

import pandas as pd

from trader import Trader
from definitions import Memory, MarketData
from exchange_apis import BitgetAPI
from strategies import MultiMovingAverageStrategy


trader = Trader(
    strategy=MultiMovingAverageStrategy(
        ab_ratio=0.5, 
        max_duration=341, 
        min_purchase=5.1,
        safety_margin=2
    ),
    exange_api=BitgetAPI(
        api_key="BITGET_API_KEY_DOG_USDT_BOT", 
        api_secret="BITGET_API_SECRET_DOG_USDT_BOT"
    ),
    pair='DOG/USDT'
)

def job():
    try:
        start_time = time.time()  # Inicio del tiempo de ejecución

        print("----------- RUN -----------")

        data = trader.exange_api.get_bars(pair=trader.pair, timeframe='1min', limit=200)
        data = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        data = data.iloc[::-1]
        data = MarketData(data)

        memory: Memory = { 'orders': [], 'balance_a': 0.0,'balance_b': 0.0}
        memory['balance_a'] = trader.exange_api.get_account_balance('DOG')
        memory['balance_b'] = trader.exange_api.get_account_balance('USDT')

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