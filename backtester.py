import pandas as pd
pd.options.mode.chained_assignment = None
from tqdm import tqdm

import strategies

class Backtester:
    def __init__(self, strategy, fee=0.0):
        self.strategy = strategy
        self.fee = fee
        self.memory = []

    def check_stop_loss(self, data, action):
        current_price = data['Close'].iloc[-1]
        memory_df = pd.DataFrame(self.memory)
        stop_loss_price = memory_df.loc[memory_df['type'] == 'stop_loss'].iloc[-1]['price']
        action_type, price, amount = action

        if action_type.value == 'sell_market':
            if current_price > stop_loss_price:
                return (action_type, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1])
        elif action_type.value == 'buy_market':
            if current_price < stop_loss_price:
                return (action_type, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1])
        else:
            return (action_type, None, None)

    def execute_strategy(self, data):
        actions = self.strategy.run(data, self.memory)
        
        for action in actions:
            action_type, price, amount = action
            if action_type is not None and price is not None:
                order_info = {}  # Aquí puedes agregar cualquier información adicional que necesites
                status = None
                executed = action_type.value in ['sell_market', 'buy_market']  # Asumiendo que todas las acciones se ejecutan
                cost = price * amount
                order_info['fees'] = cost * self.fee
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
                    'status': status,
                    'price': price,
                    'amount': amount,
                    'cost': cost,
                    'executed': executed,
                    'order_info': order_info
                })
        return actions
    
    def simulate_real_time_execution(self, data, window_size):
        data['Datetime'] = pd.to_datetime(data['Datetime'])
        data = data.drop_duplicates('Datetime', keep='first')
        # Simular la ejecución en tiempo real
        for i in tqdm(range(window_size, len(data))):
            window_data = data.iloc[i-window_size+1:i+1]
            actions = self.execute_strategy(window_data)
        return actions