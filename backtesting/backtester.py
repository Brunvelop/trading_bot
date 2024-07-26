import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import pandas as pd
import numpy as np
from tqdm import tqdm
from typing import List
from pathlib import Path

from strategies import Strategy, MultiMovingAverageStrategy
from definitions import Memory, MarketData, Action, VisualizationDataframe, PlotMode
from plots_utils import draw_graphs, calculate_moving_averages_extra_plot


class Backtester:
    def __init__(self, strategy: Strategy, initial_balance_a: float, initial_balance_b: float, fee: float = 0.001):
        self.strategy = strategy
        self.fee = fee
        self.memory: Memory = {'orders': [], 'balance_a': initial_balance_a, 'balance_b': initial_balance_b}
        self.data = None

    def simulate_real_time_execution(self, window_size: int = 200) -> List[Action]:
        for i in tqdm(range(window_size, len(self.data))):
            window_data = self.data.iloc[i-window_size+1:i+1]
            self._execute_strategy(window_data)
        return self.memory

    def load_data(
        self,
        data_path: Path = Path('data/coinex_prices_raw'),
        start: int = None,
        end: int = None,
        duration: int = None,
        variation: float = None,
        tolerance: float = 0.01,
        normalize: bool = False
    ) -> pd.DataFrame:
        if data_path.is_dir():
            csv_files = [f for f in data_path.glob('*.csv')]
            if not csv_files:
                raise ValueError(f"No CSV files found in directory: {data_path}")
            data_path = random.choice(csv_files)
        
        data = pd.read_csv(data_path)
        
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
                if np.isclose(actual_variation, variation, atol=tolerance):
                    data = segment
                    break
        else:
            if start is not None and end is not None:
                data = data.iloc[start:end]
            elif start is not None:
                data = data.iloc[start:]
            elif end is not None:
                data = data.iloc[:end]
        
        if normalize:
            max_close = data['Close'].max()
            data['Close'] = data['Close'] / max_close
            for col in ['Open', 'High', 'Low']:
                if col in data.columns:
                    data[col] = data[col] / max_close

        self.data = data
        return data

    def generate_visualization_df(self) -> VisualizationDataframe:
        memory_df = pd.DataFrame(self.memory.get('orders'))
        visualization_df = pd.merge(self.data, memory_df, left_on='Date', right_on='timestamp', how='left')

        visualization_df = self._fill_nan_with_bfill_ffill(visualization_df, 'balance_a')
        visualization_df = self._fill_nan_with_bfill_ffill(visualization_df, 'balance_b')
        visualization_df['hold_value'] = visualization_df['balance_a'] * visualization_df['Close']
        visualization_df['total_value_a'] = visualization_df['balance_a'] + visualization_df['balance_b'] / visualization_df['Close'] 
        visualization_df['total_value_b'] = visualization_df['balance_b'] + visualization_df['hold_value']
        visualization_df['adjusted_b_balance'] = visualization_df['balance_b'] - (visualization_df['balance_a'].iloc[0] - visualization_df['balance_a']) * visualization_df['Close']

        return visualization_df
    
    def run_backtest(
            self,
            data_config: dict = None,
            plot_config: dict = {
                'plot_modes': list(PlotMode),
                'save_path': None,
                'show': False
            }
    ) -> VisualizationDataframe:
        self.load_data(**data_config)
        self.simulate_real_time_execution()

        visualization_df = self.generate_visualization_df()
        extra_plots_price = None
        if plot_config.get('show', None):
            if isinstance(self.strategy, MultiMovingAverageStrategy):
                extra_plots_price = calculate_moving_averages_extra_plot(self.data)
            draw_graphs(
                visualization_df=visualization_df,  
                extra_plots_price=extra_plots_price,
                **plot_config
            )
        
        return visualization_df
    
    def _execute_strategy(self, data: MarketData):
        actions = self.strategy.run(data, self.memory)
        
        for action_type, price, amount in actions:
            if action_type is not None and price is not None:
                total_value = price * amount
                fee = amount * self.fee if action_type == Action.BUY_MARKET else total_value * self.fee if action_type == Action.SELL_MARKET else 0
                timestamp = data['Date'].iloc[-1]
                pair = 'DOG/USDT'  

                if action_type == Action.BUY_MARKET:
                    self.memory['balance_a'] += amount * (1-self.fee)
                    self.memory['balance_b'] -= total_value
                elif action_type == Action.SELL_MARKET:
                    self.memory['balance_a'] -= amount
                    self.memory['balance_b'] += total_value * (1-self.fee)

                self.memory.get('orders').append({
                    'timestamp': timestamp,
                    'pair': pair,
                    'type': action_type.value,
                    'price': price,
                    'amount': amount,
                    'fee': fee,
                    'total_value': total_value,
                    'balance_a': self.memory['balance_a'],
                    'balance_b': self.memory['balance_b']
                })
    
    def _fill_nan_with_bfill_ffill(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        # Rellenar los valores NaN hacia adelante
        df[column_name] = df[column_name].ffill()
        # Rellenar los valores NaN restantes (al principio) con el primer valor no NaN
        first_valid_index = df[column_name].first_valid_index()
        if first_valid_index is not None:
            df[column_name] = df[column_name].fillna(df[column_name].iloc[first_valid_index])

        return df
    
if __name__ == "__main__":
    import strategies
    from definitions import TradingPhase

    backtester = Backtester(
        strategy=strategies.MultiMovingAverageStrategy(
            max_duration = 200,
            min_purchase = 5.1,
            safety_margin = 1,
            trading_phase = TradingPhase.DISTRIBUTION,
            debug = False
        ),
        initial_balance_a=5000.0,
        initial_balance_b=0000.0,
        fee=0.001
    )
    backtester.run_backtest(
        data_config={
            'data_path': Path('data/coinex_prices_raw'),
            'duration': 4320,
            'variation': 0,
            'tolerance': 0.01,
            'normalize': True
        },
        plot_config= {
            'plot_modes': list(PlotMode),
            'save_path': None, #Path('data/prueba.png'),
            'show': True
        }
    )