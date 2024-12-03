from strategies.strategy import Strategy
from exchange_apis import BaseExchangeAPI
from definitions import MarketData, Memory, Action


class Trader:
    def __init__(self, strategy: Strategy, exchange_api: BaseExchangeAPI, pair: str = 'BTC/USD') -> None:
        self.strategy = strategy
        self.exchange_api = exchange_api
        self.pair = pair

    def execute_strategy(self, data: MarketData, memory: Memory) -> None:
        actions = self.strategy.run(data, memory)
        for action, price, quantity in actions:
            match action:
                case Action.BUY_MARKET: self.buy_market(price, quantity)
                case Action.SELL_MARKET: self.sell_market(price, quantity)
                case Action.BUY_LIMIT: self.buy_limit(price, quantity)
                case Action.SELL_LIMIT: self.sell_limit(price, quantity)
                case Action.STOP_LOSS: self.set_stop_loss(price, quantity)
                case Action.TAKE_PROFIT: self.set_take_profit(price, quantity)
                case _: raise ValueError(f"Unrecognized action: {action}")

    def buy_market(self, price: float, quantity: float) -> None:
        return self.exchange_api.create_order(self.pair, 'market', 'buy', quantity, price)

    def sell_market(self, price: float, quantity: float) -> None:
        return self.exchange_api.create_order(self.pair, 'market', 'sell', quantity, price)
    
    def buy_limit(self, price: float, quantity: float) -> None:
        pass

    def sell_limit(self, price: float, quantity: float) -> None:
        pass

    def set_stop_loss(self, price: float) -> None:
        pass

    def set_take_profit(self, price: float, quantity: float) -> None:
        pass