from abc import ABC, abstractmethod
from typing import List
from definitions import Memory, MarketData
from indicators import Indicator
from enum import Enum
from pydantic import BaseModel, Field
import numpy as np

class ActionType(Enum):
    BUY_MARKET = "buy_market"
    SELL_MARKET = "sell_market"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    WAIT = "wait"

class Action(BaseModel):
    action_type: ActionType
    price: np.float64 = Field(gt=0, description="Price must be greater than 0")
    amount: np.float64 = Field(ge=0, description="Quantity must be greater or equal to 0")

    class Config:
        arbitrary_types_allowed = True

class Strategy(ABC):
    @abstractmethod
    def run(self, data: MarketData, memory: Memory) -> List[Action]:
        pass
    
    @abstractmethod
    def calculate_indicators(data: MarketData) -> List[Indicator]:
        pass
