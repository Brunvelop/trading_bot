import time
import datetime

import pandas as pd

from db import DB
from strategies import Action

class Trader:
    def __init__(self, strategy, db_name, exange_api, pair='BTC/USD'):
        self.strategy = strategy
        self.db = DB(db_name)
        self.exange_api = exange_api
        self.pair = pair

    def execute_strategy(self, data, memory):
        #old stop loss y take profit closed? limit orders? update?
        actions = self.strategy.run(data, memory)
        for action, price, quantity in actions:
            if action == Action.BUY_MARKET:
                self.buy_market(price, quantity)
            elif action == Action.SELL_MARKET:
                self.sell_market(price, quantity)
            elif action == Action.BUY_LIMIT:
                self.buy_limit(price, quantity)
            elif action == Action.SELL_LIMIT:
                self.sell_limit(price, quantity)
            elif action == Action.STOP_LOSS:
                self.set_stop_loss(price, quantity)
            elif action == Action.TAKE_PROFIT:
                self.set_take_profit(price, quantity)
            else:
                pass

    def buy_market(self, price, quantity):
        order = self.exange_api.create_order(self.pair, 'market', 'buy', quantity, price)
        order_info = self.exange_api.get_order(order['id'])
        self.db.insert_order(
            order_info['id'],
            datetime.datetime.fromtimestamp(int(order_info['timestamp']/1000)).isoformat(),
            self.pair,
            'buy',
            order_info['price'],
            order_info['amount'],
            order_info['cost'],
            True,
            order_info
        )

    def sell_market(self, price, quantity):
        order = self.exange_api.create_order(self.pair, 'market', 'sell', quantity, price)
        order_info = self.exange_api.get_order(order['id'])
        self.db.insert_order(
            order_info['id'],
            datetime.datetime.fromtimestamp(int(order_info['timestamp']/1000)).isoformat(),
            self.pair,
            'sell',
            order_info['price'],
            order_info['amount'],
            order_info['cost'],
            True,
            order_info
        )
    
    def buy_limit(price, quantity):
        pass

    def sell_limit(price, quantity):
        pass

    def set_stop_loss(self, price):
        self.kraken_api.update_stop_loss('BTC/USD', 'sell', price, 1)

    def set_take_profit(price, quantity):
        pass
    
if __name__ == "__main__":
    from kraken_api import KrakenAPI
    from strategies import MovingAverageStrategy 

    trader = Trader(
        strategy= MovingAverageStrategy(window_size=10),
        db_name = 'trades',
        exange_api = KrakenAPI(),
        pair = 'BTC/EUR',
    )
    price = trader.exange_api.get_latest_price(trader.pair)
    trader.sell_market(price=price, quantity=0.0002)

    # data = {}
    # memory = trader.db.get_all_orders()
    # trader.execute_strategy(data, memory)

# ##############

    # import time
    # import schedule

    # from strategies import MovingAverageStrategy  # Asegúrate de importar tu estrategia

    # trader = Trader(MovingAverageStrategy(window_size=10))  # Inicializa Trader con tu estrategia

    # def job():
    #     start_time = time.time()  # Inicio del tiempo de ejecución
    #     print("----------- RUN -----------")
    #     data = {}  # Aquí debes obtener tus datos para la estrategia
    #     memory = trader.db.get_all_orders()
    #     trader.execute_strategy(data, memory)
    #     end_time = time.time()  # Fin del tiempo de ejecución
    #     print("Tiempo de ejecución: {} segundos".format(end_time - start_time))

    # schedule.every().minute.at(":06").do(job)

    # while True:
    #     # print("Esperando el próximo trabajo...")
    #     schedule.run_pending()
    #     time.sleep(1)