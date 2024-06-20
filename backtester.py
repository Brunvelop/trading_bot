import pandas as pd
import numpy as np
from tqdm import tqdm
from typing import List, Dict, Any

from strategies import Strategy
from definitions import Memory, MarketData, Action

class Backtester:
    def __init__(self, strategy: Strategy, initial_balance_a: float,initial_balance_b:float, fee: float = 0.001):
        self.strategy = strategy
        self.fee = fee
        self.memory = {'orders': [], 'balance_a': initial_balance_a, 'balance_b': initial_balance_b}
        self.data = None

    def execute_strategy(self, data: MarketData):
        actions = self.strategy.run(data, self.memory)
        
        for action_type, price, amount in actions:
            if action_type is not None and price is not None:
                total_value = price * amount
                fee = total_value * self.fee if action_type == Action.BUY_MARKET else amount * self.fee if action_type == Action.SELL_MARKET else 0
                timestamp = data['Datetime'].iloc[-1]
                pair = 'DOG/USDT'  

                if action_type == Action.BUY_MARKET:
                    self.memory['balance_a'] += amount
                    self.memory['balance_b'] -= (total_value + fee)
                elif action_type == Action.SELL_MARKET:
                    self.memory['balance_a'] -= (amount + fee)
                    self.memory['balance_b'] += total_value

                self.memory.get('orders').append({
                    'timestamp': timestamp,
                    'pair': pair,
                    'type': action_type.value,
                    'price': price,
                    'amount': amount,
                    'total_value': total_value,
                    'fee': fee,
                    'balance_a': self.memory['balance_a'],
                    'balance_b': self.memory['balance_b']
                })

    def simulate_real_time_execution(self, window_size: int = 350) -> List[Action]:
        # Simular la ejecución en tiempo real
        for i in tqdm(range(window_size, len(self.data))):
            window_data = self.data.iloc[i-window_size+1:i+1]
            self.execute_strategy(window_data)
        return self.memory

    def load_data(self, filename: str, start: int = None, end: int = None, 
                  duration: int = None, variation: float = None, 
                  tolerancia: float = 0.01) -> pd.DataFrame:
        """
        Ejemplos:
            # Cargar datos desde el inicio hasta el índice 200
            data = load_data('data.csv', end=200)

            # Cargar un segmento aleatorio de 1000 filas con una variación del -5%
            data = load_data('data.csv', duration=1000, variation=-0.05)
        """
        data = pd.read_csv(filename)
        
        if duration is not None and variation is not None:
            n = len(data)
            while True:
                # Seleccionar un índice de inicio aleatorio
                start_idx = np.random.randint(0, n - duration)
                end_idx = start_idx + duration
                
                # Extraer el tramo de datos
                segment = data.iloc[start_idx:end_idx]
                
                # Calcular la variación porcentual
                start_price = segment.iloc[0]['Close']  # Asumiendo que 'Close' es la columna de precios
                end_price = segment.iloc[-1]['Close']
                actual_variation = (end_price - start_price) / start_price
                
                # Si la variación porcentual es igual a la variación deseada, devolver el segmento
                if np.isclose(actual_variation, variation, atol=tolerancia):
                    return segment
        else:
            if start is not None and end is not None:
                data = data.iloc[start:end]
            elif start is not None:
                data = data.iloc[start:]
            elif end is not None:
                data = data.iloc[:end]

        self.data = data
        return data

    def fill_nan_with_bfill_ffill(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        # Rellenar los valores NaN en la columna con el siguiente valor no NaN
        df[column_name] = df[column_name].bfill()
        # Rellenar los valores NaN restantes (al final) con el último valor no NaN
        df[column_name] = df[column_name].ffill()

        return df

    def generate_visualization_df(self) -> pd.DataFrame:
        memory_df = pd.DataFrame(self.memory.get('orders'))
        visualization_df = pd.merge(self.data, memory_df, left_on='Datetime', right_on='timestamp', how='left')

        visualization_df = self.fill_nan_with_bfill_ffill(visualization_df, 'balance_a')
        visualization_df = self.fill_nan_with_bfill_ffill(visualization_df, 'balance_b')
        visualization_df['hold_value'] = visualization_df['balance_a'] * visualization_df['Close']
        visualization_df['total_value'] = visualization_df['balance_b'] + visualization_df['hold_value']

        return visualization_df
    
    def moving_averages_extra_plot(self) -> list:
        ma_10 = self.data['Close'].rolling(window=10).mean()
        ma_50 = self.data['Close'].rolling(window=50).mean()
        ma_100 = self.data['Close'].rolling(window=100).mean()
        ma_200 = self.data['Close'].rolling(window=200).mean()

        extra_plots_price = [
            ((self.data['Datetime'], ma_10), {'color': 'blue', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 10', 'type': 'plot'}),
            ((self.data['Datetime'], ma_50), {'color': 'orange', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 50', 'type': 'plot'}),
            ((self.data['Datetime'], ma_100), {'color': 'green', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 100', 'type': 'plot'}),
            ((self.data['Datetime'], ma_200), {'color': 'red', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 200', 'type': 'plot'})
        ]
        return extra_plots_price