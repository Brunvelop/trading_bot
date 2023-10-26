import pandas as pd
pd.options.mode.chained_assignment = None
from tqdm import tqdm

import strategies

class Backtester:
    def __init__(self, strategy):
        self.strategy = strategy
        self.history = []

    def execute_strategy(self, data):
        action, price, quantity = self.strategy.run(data)
        self.history.append((action, price, quantity, self.strategy.balance_a, self.strategy.balance_b))