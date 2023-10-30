from enum import Enum
from typing import Tuple, List
from abc import ABC, abstractmethod

import pandas as pd

class Action(Enum):
    BUY_MARKET = "buy_market"
    SELL_MARKET = "sell_market"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    WAIT = "wait"

class Strategy(ABC):
    @abstractmethod
    def run(self, data, memory) -> List[Tuple[Action, float, float]]:
        pass # :return: [(action1, price1, quantity1), (action2, price2, quantity2), ...]
    
    def get_balance_b(self, memory):
        df = pd.DataFrame(memory)

        if df.empty:
            return 0

        total_bought = df.loc[(df['type'] == 'buy_market') & (df['executed'] == True), 'amount'].sum()
        total_sold = df.loc[(df['type'] == 'sell_market') & (df['executed'] == True), 'amount'].sum()

        total_balance = total_bought - total_sold

        return total_balance

class MovingAverageStrategy(Strategy):
    def __init__(self, window_size = 200, cost = 10):
        self.window_size = window_size
        self.cost = cost

    def run(self, data, memory):
        actions = []

        data['moving_average'] = data['Close'].rolling(window=self.window_size).mean()
        balance_b = self.get_balance_b(memory)

        if data['Close'].iloc[-1] < data['moving_average'].iloc[-1]:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))

        elif data['Close'].iloc[-1] > data['moving_average'].iloc[-1] and balance_b > self.cost / data['Close'].iloc[-1]:
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))

        else:
            actions.append((Action.WAIT, None, None))

        return actions
    
class MultiMovingAverageStrategy(Strategy):
    def __init__(self, windows=[10, 50, 100, 200], cost=10):
        self.windows = windows
        self.cost = cost

    def run(self, data, memory):
        actions = []
        balance_b = self.get_balance_b(memory).iloc[-1]

        # Calculamos las medias móviles para cada ventana
        moving_averages = [data['Close'].rolling(window=window).mean() for window in self.windows]

        # Comprobamos si las medias móviles están alineadas
        aligned_up = all(ma1.iloc[-1] > ma2.iloc[-1] for ma1, ma2 in zip(moving_averages, moving_averages[1:]))
        aligned_down = all(ma1.iloc[-1] < ma2.iloc[-1] for ma1, ma2 in zip(moving_averages, moving_averages[1:]))

        # Comprobamos si el precio de cierre está por encima o por debajo de todas las medias móviles
        above_all = all(data['Close'].iloc[-1] > ma.iloc[-1] for ma in moving_averages)
        below_all = all(data['Close'].iloc[-1] < ma.iloc[-1] for ma in moving_averages)

        if above_all and aligned_up and balance_b > self.cost / data['Close'].iloc[-1]:
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        elif below_all and aligned_down:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        else:
            actions.append((Action.WAIT, None, None))

        return actions
    
class SuperStrategyFutures(Strategy):
    def __init__(self, windows=[10, 50, 100, 200], cost=10):
        self.windows = windows
        self.cost = cost
    
    def update_stop_loss(self, data, memory):
        current_price = data['Close'].iloc[-1]
        open = self.get_open_trade(memory)
        data['moving_average'] = data['Close'].rolling(window=10).mean()

        threshold = 0.0000
        if open.get('type') == 'sell_market':
            if current_price < data['moving_average'].iloc[-1] and open.get('price') > data['moving_average'].iloc[-1]*(1+threshold):
                return (Action.STOP_LOSS, data['moving_average'].iloc[-1], self.cost / data['Close'].iloc[-1])
        elif open.get('type') == 'buy_market':
            if current_price > data['moving_average'].iloc[-1] and open.get('price') < data['moving_average'].iloc[-1]*(1-threshold):
                return (Action.STOP_LOSS, data['moving_average'].iloc[-1], self.cost / data['Close'].iloc[-1])
        return None

    def get_open_trade(self, memory):
        # Convertimos la lista de memoria en un DataFrame de pandas
        df = pd.DataFrame(memory)

        if df.empty:
            return None

        # Filtramos las órdenes que han sido ejecutadas
        executed_orders = df[df['executed'] == True]

        # Contamos las órdenes de compra y venta
        buy_count = len(executed_orders[executed_orders['type'] == 'buy_market'])
        sell_count = len(executed_orders[executed_orders['type'] == 'sell_market'])

        # Si hay más compras que ventas, entonces la operación abierta es una compra
        if buy_count > sell_count:
            return executed_orders[executed_orders['type'] == 'buy_market'].iloc[-1].to_dict()
        # Si hay más ventas que compras, entonces la operación abierta es una venta
        elif sell_count > buy_count:
            return executed_orders[executed_orders['type'] == 'sell_market'].iloc[-1].to_dict()
        # Si no hay operaciones abiertas, devolvemos None
        else:
            return None

    def run(self, data, memory):
        actions = []
        
        # Calculate the range of the bar as a percentage of the closing price
        bar_range = (data['High'] - data['Low']).abs() / data['Low'] * 100
        avg_range = bar_range.ewm(span=10).mean()
        std_dev = avg_range.rolling(window=200).std()
        volatility_up = (avg_range > std_dev).iloc[-1]

        # Calculate the exponential moving averages of BarRange
        avg_ranges = [bar_range.ewm(span=window).mean() for window in self.windows]

        # Calculate the maximum and minimum of the last 300 bars, excluding the current bar
        max_300 = data['Close'][-302:-2].max()
        min_300 = data['Close'][-302:-2].min()

        # Add conditions to break the maximum or minimum of the last 300 bars
        break_max_300 = data['Close'] > max_300
        break_min_300 = data['Close'] < min_300

        open = self.get_open_trade(memory)
        if not open:
            if break_max_300.iloc[-1] and volatility_up:
                actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
                actions.append((Action.STOP_LOSS, data['Low'].tail(10).min(), self.cost / data['Close'].iloc[-1]))
            elif break_min_300.iloc[-1] and volatility_up:
                actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
                actions.append((Action.STOP_LOSS, data['High'].tail(10).max(), self.cost / data['Close'].iloc[-1]))
            else:
                actions.append((Action.WAIT, None, None))
        elif open:
            current_price = data['Close'].iloc[-1]
            memory_df = pd.DataFrame(memory)
            stop_loss_price = memory_df.loc[memory_df['type'] == 'stop_loss'].iloc[-1]['price']
            if open.get('type') == 'sell_market':
                if current_price > stop_loss_price:
                    actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1] ))
            elif open.get('type') == 'buy_market':
                if current_price < stop_loss_price:
                    actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
            else:
                actions.append((Action.WAIT, None, None))
            
            update = self.update_stop_loss(data, memory)
            if update:
                actions.append(update)


        return actions