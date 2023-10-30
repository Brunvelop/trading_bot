import pandas as pd
pd.options.mode.chained_assignment = None
from tqdm import tqdm

import strategies

class Backtester:
    def __init__(self, strategy):
        self.strategy = strategy
        self.memory = []

    def execute_strategy(self, data):
        actions = self.strategy.run(data, self.memory)
        
        for action in actions:
            action_type, price, amount = action
            if action_type is not None and price is not None:
                order_info = {}  # Aquí puedes agregar cualquier información adicional que necesites
                executed = action_type.value in ['sell_market', 'buy_market']  # Asumiendo que todas las acciones se ejecutan
                cost = price * amount
                order_id = 'fake_OEU45D-6THBX-3VLOJP'  # Aquí puedes generar un ID de orden único
                timestamp = data['Datetime'].iloc[-1]  # Aquí puedes generar un timestamp actual
                pair = 'fake_BTC/EUR'  # Aquí puedes usar el par de divisas que estás utilizando
                id = 277  # Aquí puedes generar un ID único

                self.memory.append({
                    'id': id,
                    'order_id': order_id,
                    'timestamp': timestamp,
                    'pair': pair,
                    'type': action_type.value,
                    'price': price,
                    'amount': amount,
                    'cost': cost,
                    'executed': executed,
                    'order_info': order_info
                })
        return actions