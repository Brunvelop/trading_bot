from strategies import Strategy
from strategies import ActionType
from exchange_apis import BaseExchangeAPI
from definitions import MarketData, Memory

class Trader:
    def __init__(self, strategy: Strategy, exchange_api: BaseExchangeAPI, pair: str = 'BTC/USD') -> None:
        self.strategy = strategy
        self.exchange_api = exchange_api
        self.pair = pair

    def execute_strategy(self, data: MarketData, memory: Memory) -> None:
        actions = self.strategy.run(data, memory)
        for action in actions:
            match action.action_type:
                case ActionType.BUY_MARKET: self.buy_market(action.price, action.amount)
                case ActionType.SELL_MARKET: self.sell_market(action.price, action.amount)
                case ActionType.BUY_LIMIT: self.buy_limit(action.price, action.amount)
                case ActionType.SELL_LIMIT: self.sell_limit(action.price, action.amount)
                case ActionType.STOP_LOSS: self.set_stop_loss(action.price, action.amount)
                case ActionType.TAKE_PROFIT: self.set_take_profit(action.price, action.amount)
                case _: raise ValueError(f"Unrecognized action: {action}")

    def buy_market(self, price: float, amount: float) -> None:
        return self.exchange_api.create_order(self.pair, 'market', 'buy', amount, price)

    def sell_market(self, price: float, amount: float) -> None:
        return self.exchange_api.create_order(self.pair, 'market', 'sell', amount, price)
    
    def buy_limit(self, price: float, amount: float) -> None:
        pass

    def sell_limit(self, price: float, amount: float) -> None:
        pass

    def set_stop_loss(self, price: float) -> None:
        pass

    def set_take_profit(self, price: float, amount: float) -> None:
        pass