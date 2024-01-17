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

    def get_balance_a(self, memory, initial_balance_a=0):
        df = pd.DataFrame(memory)

        if df.empty:
            return initial_balance_a

        df['cost'] = df['price'] * df['amount']
        df.loc[df['type'] == 'sell_market', 'cost'] *= -1

        df['fees'] = df[df['order_info'].notna()].apply(lambda row: row['order_info'].get('fees'), axis=1)
        df['fees'] = df['fees'].fillna(0)

        total_cost = df['cost'].sum()
        total_fees = df['fees'].sum()

        total_balance = initial_balance_a - total_cost - total_fees

        return total_balance
    
    def get_balance_b(self, memory, initial_balance_b=0):
        df = pd.DataFrame(memory)

        if df.empty:
            return initial_balance_b

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
    def __init__(self, windows=[10, 50, 100, 200], cost=10, fee=0.004):
        self.windows = windows
        self.cost = cost
        self.fee = fee

    def can_sell(self, current_price, memory):
        # Calculamos el precio que es el porcentaje menor que el precio actual
        sell_threshold = current_price * (1 - self.fee)

        # Convertimos la memoria en un DataFrame
        memory_df = pd.DataFrame(memory)

        # Obtenemos los trades de compra y venta
        buy_trades = memory_df[memory_df['type'] == 'buy_market'].to_dict('records')
        sell_trades = memory_df[memory_df['type'] == 'sell_market'].to_dict('records')

        # Asociamos cada sell_trade con el primer buy_trade que tenga al menos un porcentaje de diferencia positiva
        for sell_trade in sell_trades:
            for buy_trade in buy_trades:
                if sell_trade['price'] > buy_trade['price'] * (1 + self.fee):
                    buy_trades.remove(buy_trade)
                    break

        # Verificamos si hay alguna compra en la memoria cuyo precio es menor que el umbral de venta
        return any(trade['price'] < sell_threshold for trade in buy_trades)
    
    def calculate_moving_averages(self, data):
        return [data['Close'].rolling(window=window).mean().iloc[-1] for window in self.windows]
    
    def run(self, data, memory):
        actions = []
        balance_b = self.get_balance_b(memory)

        # Calculamos las medias móviles para cada ventana
        moving_averages = self.calculate_moving_averages(data)


        # Comprobamos si las medias móviles están alineadas
        aligned_up = moving_averages[0] > moving_averages[1] > moving_averages[2] >  moving_averages[3]
        aligned_down = moving_averages[0] < moving_averages[1] < moving_averages[2] <  moving_averages[3]

        # Comprobamos si el precio de cierre está por encima o por debajo de todas las medias móviles
        above_all = all(data['Close'].iloc[-1] > ma for ma in moving_averages)
        below_all = all(data['Close'].iloc[-1] < ma for ma in moving_averages)

        if above_all and aligned_up and balance_b > self.cost / data['Close'].iloc[-1] and self.can_sell(data['Close'].iloc[-1], memory):
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        elif below_all and aligned_down:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        else:
            actions.append((Action.WAIT, None, None))

        return actions
    
class MultiMovingAverageStrategyFutures(Strategy):
    def __init__(self, windows=[10, 50, 100, 200], cost=10, fee=0.004):
        self.windows = windows
        self.cost = cost
        self.fee = fee

    def can_sell(self, current_price, memory):
        # Calculamos el precio que es el porcentaje menor que el precio actual
        sell_threshold = current_price * (1 - self.fee)

        # Convertimos la memoria en un DataFrame
        memory_df = pd.DataFrame(memory)

        # Obtenemos los trades de compra y venta
        buy_trades = memory_df[memory_df['type'] == 'buy_market'].to_dict('records')
        sell_trades = memory_df[memory_df['type'] == 'sell_market'].to_dict('records')

        # Asociamos cada sell_trade con el primer buy_trade que tenga al menos un porcentaje de diferencia positiva
        for sell_trade in sell_trades:
            for buy_trade in buy_trades:
                if sell_trade['price'] > buy_trade['price'] * (1 + self.fee):
                    buy_trades.remove(buy_trade)
                    break

        # Verificamos si hay alguna compra en la memoria cuyo precio es menor que el umbral de venta
        return any(trade['price'] < sell_threshold for trade in buy_trades)
    
    def calculate_moving_averages(self, data):
        return [data['Close'].rolling(window=window).mean().iloc[-1] for window in self.windows]
    
    def run(self, data, memory):
        actions = []
        balance_b = self.get_balance_b(memory)

        # Calculamos las medias móviles para cada ventana
        moving_averages = self.calculate_moving_averages(data)

        # Comprobamos si las medias móviles están alineadas
        aligned_up = moving_averages[0] > moving_averages[1] > moving_averages[2] >  moving_averages[3]
        aligned_down = moving_averages[0] < moving_averages[1] < moving_averages[2] <  moving_averages[3]

        # Comprobamos si el precio de cierre está por encima o por debajo de todas las medias móviles
        above_all = all(data['Close'].iloc[-1] > ma for ma in moving_averages)
        below_all = all(data['Close'].iloc[-1] < ma for ma in moving_averages)

        if above_all and aligned_up and balance_b > self.cost / data['Close'].iloc[-1] and self.can_sell(data['Close'].iloc[-1], memory):
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        elif below_all and aligned_down:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        else:
            actions.append((Action.WAIT, None, None))

        return actions

class MultiMovingAverageStrategySell(Strategy):
    def __init__(self, windows=[10, 50, 100, 200], cost=10, fee=0.004):
        self.windows = windows
        self.cost = cost
        self.fee = fee
    
    def calculate_moving_averages(self, data):
        return [data['Close'].rolling(window=window).mean().iloc[-1] for window in self.windows]
    
    def can_buy(self, current_price, memory):

        # Calculamos el precio que es el porcentaje menor que el precio actual
        buy_threshold = current_price * (1 + self.fee)

        # Convertimos la memoria en un DataFrame
        memory_df = pd.DataFrame(memory)
        if memory_df.empty:
            return False

        # Obtenemos los trades de compra y venta
        
        buy_trades = memory_df[memory_df['type'] == 'buy_market'].to_dict('records')
        sell_trades = memory_df[memory_df['type'] == 'sell_market'].to_dict('records')

        # Asociamos cada sell_trade con el primer buy_trade que tenga al menos un porcentaje de diferencia positiva
        for buy_trade in buy_trades:
            for sell_trade in sell_trades:
                if sell_trade['price'] > buy_trade['price'] * (1 + self.fee):
                    sell_trades.remove(sell_trade)
                    break

        # Verificamos si hay alguna venta en la memoria cuyo precio es mayor que el umbral de compra
        return any(trade['price'] > buy_threshold for trade in sell_trades)
    
    def run(self, data, memory):
        actions = []
        balance_a = memory['balance']

        # Calculamos las medias móviles para cada ventana
        moving_averages = self.calculate_moving_averages(data)

        # Comprobamos si las medias móviles están alineadas
        aligned_up = moving_averages[0] > moving_averages[1] > moving_averages[2] >  moving_averages[3]
        aligned_down = moving_averages[0] < moving_averages[1] < moving_averages[2] <  moving_averages[3]

        # Comprobamos si el precio de cierre está por encima o por debajo de todas las medias móviles
        above_all = all(data['Close'].iloc[-1] > ma for ma in moving_averages)
        below_all = all(data['Close'].iloc[-1] < ma for ma in moving_averages)

        if above_all and aligned_up and balance_a > self.cost:
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost))
        elif below_all and aligned_down and self.can_buy(data['Close'].iloc[-1], memory['orders']):
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost))
        else:
            actions.append((Action.WAIT, None, None))

        return actions

class MultiMovingAverageStrategy2(Strategy):
    def __init__(self, windows=[10, 50, 100, 200], cost=10, fee=0.004):
        self.windows = windows
        self.cost = cost
        self.fee = fee

    def can_sell(self, current_price, memory):
        # Calculamos el precio que es el porcentaje menor que el precio actual
        sell_threshold = current_price * (1 - self.fee)

        # Convertimos la memoria en un DataFrame
        memory_df = pd.DataFrame(memory)

        # Obtenemos los trades de compra y venta
        buy_trades = memory_df[memory_df['type'] == 'buy_market'].to_dict('records')
        sell_trades = memory_df[memory_df['type'] == 'sell_market'].to_dict('records')

        # Asociamos cada sell_trade con el primer buy_trade que tenga al menos un porcentaje de diferencia positiva
        for sell_trade in sell_trades:
            for buy_trade in buy_trades:
                if sell_trade['price'] > buy_trade['price'] * (1 + self.fee):
                    buy_trades.remove(buy_trade)
                    break

        # Verificamos si hay alguna compra en la memoria cuyo precio es menor que el umbral de venta
        return any(trade['price'] < sell_threshold for trade in buy_trades)
    
    def calculate_moving_averages(self, data):
        return [data['Close'].rolling(window=window).mean().iloc[-1] for window in self.windows]
    
    def run(self, data, memory):
        actions = []
        balance_b = self.get_balance_b(memory)

        # Calculamos las medias móviles para cada ventana
        moving_averages = self.calculate_moving_averages(data)


        # Comprobamos si las medias móviles están alineadas
        aligned_up = moving_averages[0] > moving_averages[1] > moving_averages[2] >  moving_averages[3]
        aligned_down = moving_averages[0] < moving_averages[1] < moving_averages[2] <  moving_averages[3]

        # Comprobamos si el precio de cierre está por encima o por debajo de todas las medias móviles
        above_all = all(data['Close'].iloc[-1] > ma for ma in moving_averages)
        below_all = all(data['Close'].iloc[-1] < ma for ma in moving_averages)

        if above_all and aligned_up and balance_b > self.cost / data['Close'].iloc[-1] and self.can_sell(data['Close'].iloc[-1], memory):
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], balance_b*0.01))
        elif below_all and aligned_down:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        else:
            actions.append((Action.WAIT, None, None))

        return actions
    
class StandardDeviationStrategy(Strategy):
    def __init__(self, cost=10, fee=0.004):
        self.cost = cost
        self.fee = fee

    def can_sell(self, current_price, memory):
        if not memory:
            return False

        # Calculamos el precio que es el porcentaje menor que el precio actual
        sell_threshold = current_price * (1 - self.fee)

        # Convertimos la memoria en un DataFrame
        memory_df = pd.DataFrame(memory)

        # Obtenemos los trades de compra y venta
        buy_trades = memory_df[memory_df['type'] == 'buy_market'].to_dict('records')
        sell_trades = memory_df[memory_df['type'] == 'sell_market'].to_dict('records')

        # Asociamos cada sell_trade con el primer buy_trade que tenga al menos un porcentaje de diferencia positiva
        for sell_trade in sell_trades:
            for buy_trade in buy_trades:
                if sell_trade['price'] > buy_trade['price'] * (1 + self.fee):
                    buy_trades.remove(buy_trade)
                    break

        # Verificamos si hay alguna compra en la memoria cuyo precio es menor que el umbral de venta
        return any(trade['price'] < sell_threshold for trade in buy_trades)
    
    def calculate_standard_deviations(self, data, n=3):
        price = data['Close']
        sma_200 = price.rolling(window=200).mean()
        std_dev = price.rolling(window=200).std()

        upper_std_dev = sma_200 + n*std_dev
        lower_std_dev = sma_200 - n*std_dev

        return upper_std_dev, lower_std_dev
    
    def run(self, data, memory):
        actions = []
        balance_b = self.get_balance_b(memory)

        upper_std_dev, lower_std_dev = self.calculate_standard_deviations(data)

        sell_condition = data['Close'] > upper_std_dev
        buy_condition = data['Close'] < lower_std_dev

        if sell_condition.iloc[-1] and self.can_sell(data['Close'].iloc[-1], memory) and balance_b > self.cost / data['Close'].iloc[-1]:
            actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        elif buy_condition.iloc[-1]:
            actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
        else:
            actions.append((Action.WAIT, None, None))

        return actions
    
class SuperStrategyFutures(Strategy):
    def __init__(self, cost=100, fee = 0):
        self.cost = cost
        self.fee = fee
    
    def update_stop_loss(self, data, memory, threshold = 0):
        current_price = data['Close'].iloc[-1]
        open = self.get_open_trade(memory)
        data['moving_average'] = data['Close'].rolling(window=10).mean()

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
    
    def calculate_std_dev_and_avg_range(self, data):
        bar_range = (data['High'] - data['Low']).abs() / data['Low'] * 100
        avg_range = bar_range.ewm(span=10).mean()
        std_dev = avg_range.rolling(window=200).std()
        return std_dev, avg_range

    def calculate_max_min_300(self, data):
        max_300 = data['Close'][-302:-3].max()
        min_300 = data['Close'][-302:-3].min()
        return max_300, min_300

    def run(self, data, memory):
        actions = []
        
        # Calculate the range of the bar as a percentage of the closing price
        std_dev, avg_range = self.calculate_std_dev_and_avg_range(data)
        max_300, min_300 = self.calculate_max_min_300(data)

        # Add conditions to break the maximum or minimum of the last 300 bars
        volatility_up = (avg_range > 3*std_dev).iloc[-1]
        break_max_300 = data['Close'] > max_300
        break_min_300 = data['Close'] < min_300

        balance_b = self.get_balance_b(memory)
        balance_a = self.get_balance_a(memory)

        open = self.get_open_trade(memory)
        if True: #not open:
            if break_min_300.iloc[-1] and volatility_up:
                actions.append((Action.BUY_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
                # actions.append((Action.STOP_LOSS, data['Close'].iloc[-1]*(1-0.01), self.cost / data['Close'].iloc[-1]))
            elif break_max_300.iloc[-1] and volatility_up:
                actions.append((Action.SELL_MARKET, data['Close'].iloc[-1], self.cost / data['Close'].iloc[-1]))
                # actions.append((Action.STOP_LOSS, data['Close'].iloc[-1]*(1+0.01), self.cost / data['Close'].iloc[-1]))
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
            
            # update = self.update_stop_loss(data, memory)
            # if update:
            #     actions.append(update)


        return actions