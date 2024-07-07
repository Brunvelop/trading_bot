from strategies import Action, Strategy
from exchange_apis import BaseExchangeAPI
from definitions import MarketData, Memory


class Trader:
    def __init__(self, strategy: Strategy, exange_api: BaseExchangeAPI, pair: str = 'BTC/USD') -> None:
        self.strategy = strategy
        self.exange_api = exange_api
        self.pair = pair

    def execute_strategy(self, data: MarketData, memory: Memory) -> None:
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

    def buy_market(self, price: float, quantity: float) -> None:
        return self.exange_api.create_order(self.pair, 'market', 'buy', quantity, price)

    def sell_market(self, price: float, quantity: float) -> None:
        return self.exange_api.create_order(self.pair, 'market', 'sell', quantity, price)
    
    def buy_limit(self, price: float, quantity: float) -> None:
        pass

    def sell_limit(self, price: float, quantity: float) -> None:
        pass

    def set_stop_loss(self, price: float) -> None:
        self.exange_api.update_stop_loss('BTC/USD', 'sell', price, 1)

    def set_take_profit(self, price: float, quantity: float) -> None:
        pass