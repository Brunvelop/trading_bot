from enum import Enum, auto
from typing import Tuple, List, NamedTuple
from dataclasses import dataclass

from definitions import Action, Memory, MarketData, TradingPhase
from indicators import Indicators
from .strategy import Strategy

class MA(NamedTuple):
    period: int
    price: float
    has_profit: bool = False
    portion_sold: bool = False

@dataclass
class Position:
    entry_price: float
    initial_amount: float  # Cantidad inicial de la posición
    remaining_amount: float  # Cantidad actual después de ventas parciales
    mas_sold: List[int] = None  # Lista de MAs que ya han vendido su porción

    def __post_init__(self):
        self.mas_sold = []
        self.remaining_amount = self.initial_amount

    def is_closed(self) -> bool:
        """Verifica si la posición está completamente cerrada"""
        return self.remaining_amount <= 0.000001  # Usar un pequeño epsilon para manejar errores de punto flotante

class MultiMovingAverageStrategyTrend(Strategy):
    class Alignment(Enum):
        UP = auto()
        DOWN = auto()
        NONE = auto()

    class Mode(Enum):
        LONG = "long"
        SHORT = "short"
        BOTH = "both"

    def __init__(self, 
            windows: List[int] = [10, 50, 100, 200],
            mode: Mode = Mode.BOTH,
            debug: bool = True
        ) -> None:
        self.windows = windows
        self.mode = mode
        self.debug = debug
        self.previous_alignment = None
        self.last_action = None
        self.current_position = None

    def _reset_position_state(self):
        """Resetea el estado de la posición para permitir nuevas entradas"""
        if self.debug and self.current_position:
            print(f"Resetting position state. Final remaining amount: {self.current_position.remaining_amount}")
        self.current_position = None
        self.last_action = None

    def _calculate_profit_percentage(self, price: float) -> float:
        if not self.current_position:
            return 0.0
        if self.last_action == Action.BUY_MARKET:
            return (price - self.current_position.entry_price) / self.current_position.entry_price * 100
        else:  # SHORT position
            return (self.current_position.entry_price - price) / self.current_position.entry_price * 100

    def _get_mas_with_profit(self, current_price: float, moving_averages: List[dict]) -> List[MA]:
        """Obtiene las MAs ordenadas y marca cuáles tienen beneficio"""
        ma_prices = [ma['result'].iloc[-1] for ma in moving_averages]
        mas = []
        
        # Crear lista ordenada de MAs con su información
        for period, price in zip(self.windows, ma_prices):
            has_profit = self._calculate_profit_percentage(price) > 0
            portion_sold = period in self.current_position.mas_sold if self.current_position else False
            mas.append(MA(period=period, price=price, has_profit=has_profit, portion_sold=portion_sold))
        
        return mas

    def _check_exit_conditions(self, data: MarketData, moving_averages: List[dict]) -> List[Tuple[Action, float, float]]:
        if not self.current_position or self.current_position.is_closed():
            self._reset_position_state()
            return []

        actions = []
        current_price = data['close'].iloc[-1]
        mas = self._get_mas_with_profit(current_price, moving_averages)

        if self.last_action == Action.BUY_MARKET:  # LONG position management
            # Stop loss: Si el precio cierra por debajo de MA200, cerrar toda la posición
            if current_price < mas[-1].price:  # MA200 es la última
                if self.debug:
                    print(f"Stop Loss triggered: Selling remaining position ({self.current_position.remaining_amount}) at {current_price}")
                if not self.current_position.is_closed():
                    actions.append((Action.SELL_MARKET, current_price, self.current_position.remaining_amount))
                    self.current_position.remaining_amount = 0
                    self._reset_position_state()
                return actions

            # Contar cuántas MAs consecutivas tienen beneficio desde MA10
            profitable_mas = []
            for ma in mas:
                if ma.has_profit:
                    profitable_mas.append(ma)
                else:
                    break

            if profitable_mas:
                portions = len(profitable_mas)
                amount_per_portion = self.current_position.initial_amount / portions

                if self.debug:
                    print(f"\nProfitable MAs: {[ma.period for ma in profitable_mas]}")
                    print(f"Already sold MAs: {self.current_position.mas_sold}")
                    print(f"Portions: {portions}, Amount per portion: {amount_per_portion}")
                    print(f"Remaining amount: {self.current_position.remaining_amount}")

                # Verificar cada MA con beneficio
                for ma in profitable_mas:
                    # Solo vender si el precio cruza la MA, no hemos vendido ya esta porción y hay suficiente cantidad
                    if (current_price < ma.price and 
                        ma.period not in self.current_position.mas_sold and 
                        self.current_position.remaining_amount >= amount_per_portion):
                        
                        if self.debug:
                            print(f"Price crossed below MA{ma.period}, selling portion")
                        actions.append((Action.SELL_MARKET, current_price, amount_per_portion))
                        self.current_position.mas_sold.append(ma.period)
                        self.current_position.remaining_amount -= amount_per_portion

                        if self.current_position.is_closed():
                            self._reset_position_state()
                            break

        else:  # SHORT position management
            # Stop loss: Si el precio cierra por encima de MA200, cerrar toda la posición
            if current_price > mas[-1].price:  # MA200 es la última
                if self.debug:
                    print(f"Stop Loss triggered: Buying remaining position ({self.current_position.remaining_amount}) at {current_price}")
                if not self.current_position.is_closed():
                    actions.append((Action.BUY_MARKET, current_price, self.current_position.remaining_amount / current_price))
                    self.current_position.remaining_amount = 0
                    self._reset_position_state()
                return actions

            # Contar cuántas MAs consecutivas tienen beneficio desde MA10
            profitable_mas = []
            for ma in mas:
                if ma.has_profit:
                    profitable_mas.append(ma)
                else:
                    break

            if profitable_mas:
                portions = len(profitable_mas)
                amount_per_portion = self.current_position.initial_amount / portions

                if self.debug:
                    print(f"\nProfitable MAs: {[ma.period for ma in profitable_mas]}")
                    print(f"Already sold MAs: {self.current_position.mas_sold}")
                    print(f"Portions: {portions}, Amount per portion: {amount_per_portion}")
                    print(f"Remaining amount: {self.current_position.remaining_amount}")

                # Verificar cada MA con beneficio
                for ma in profitable_mas:
                    # Solo comprar si el precio cruza la MA, no hemos comprado ya esta porción y hay suficiente cantidad
                    if (current_price > ma.price and 
                        ma.period not in self.current_position.mas_sold and 
                        self.current_position.remaining_amount >= amount_per_portion):
                        
                        if self.debug:
                            print(f"Price crossed above MA{ma.period}, buying portion")
                        actions.append((Action.BUY_MARKET, current_price, amount_per_portion / current_price))
                        self.current_position.mas_sold.append(ma.period)
                        self.current_position.remaining_amount -= amount_per_portion

                        if self.current_position.is_closed():
                            self._reset_position_state()
                            break

        return actions

    def run(self, data: MarketData, memory: Memory) -> List[Tuple[Action, float, float]]:
        actions = []
        balance_a, balance_b = memory.get('balance_a', 0), memory.get('balance_b', 0)
        current_price = data['close'].iloc[-1]

        # Verificar si hay una posición abierta que debería estar cerrada
        if self.current_position and self.current_position.is_closed():
            self._reset_position_state()

        current_alignment = self._determine_alignment(data)
        moving_averages = self.calculate_indicators(data)

        # Primero, verificar condiciones de salida si hay una posición abierta
        if self.current_position:
            exit_actions = self._check_exit_conditions(data, moving_averages)
            if exit_actions:
                return exit_actions

        # Solo actualizar previous_alignment cuando tenemos una tendencia significativa
        if current_alignment != self.Alignment.NONE:
            # Verificar cambio de tendencia y ejecutar entradas
            if self.previous_alignment is not None and current_alignment != self.previous_alignment:
                # Caso para vender: transición UP a DOWN
                if self.previous_alignment == self.Alignment.UP and current_alignment == self.Alignment.DOWN:
                    if self.mode in [self.Mode.SHORT, self.Mode.BOTH]:
                        if (self.last_action is None or self.last_action == Action.BUY_MARKET) and balance_a > 0:
                            amount = balance_a * 0.1
                            if amount > 0:
                                actions.append((Action.SELL_MARKET, current_price, amount))
                                self.last_action = Action.SELL_MARKET
                                self.current_position = Position(
                                    entry_price=current_price, 
                                    initial_amount=amount,
                                    remaining_amount=amount
                                )
                
                # Caso para comprar: transición DOWN a UP
                elif self.previous_alignment == self.Alignment.DOWN and current_alignment == self.Alignment.UP:
                    if self.mode in [self.Mode.LONG, self.Mode.BOTH]:
                        if (self.last_action is None or self.last_action == Action.SELL_MARKET) and balance_b > 0:
                            amount = (balance_b * 0.1) / current_price
                            if amount > 0:
                                actions.append((Action.BUY_MARKET, current_price, amount))
                                self.last_action = Action.BUY_MARKET
                                self.current_position = Position(
                                    entry_price=current_price, 
                                    initial_amount=amount,
                                    remaining_amount=amount
                                )
            
            # Actualizar previous_alignment solo para tendencias significativas
            self.previous_alignment = current_alignment

        if not actions:
            actions.append((Action.WAIT, None, None))

        if self.debug:
            print("\nStrategy State:")
            print("time:", str(data['date'].iloc[-1]))
            print(f"Previous alignment: {self.previous_alignment}")
            print(f"Current alignment: {current_alignment}")
            print(f"Mode: {self.mode.value}")
            print(f"Last action: {self.last_action}")
            if self.current_position:
                print(f"Position entry price: {self.current_position.entry_price}")
                print(f"Position initial amount: {self.current_position.initial_amount}")
                print(f"Position remaining amount: {self.current_position.remaining_amount}")
                print(f"MAs sold: {self.current_position.mas_sold}")
                print(f"Position closed: {self.current_position.is_closed()}")

        return actions
    
    def calculate_indicators(self, data: MarketData):
        return [Indicators.calculate_moving_average(data, window) for window in self.windows]

    def _determine_alignment(self, data: MarketData) -> Alignment:
        moving_averages = self.calculate_indicators(data)
        current_price = data['close'].iloc[-1]
        
        if (current_price > moving_averages[0]['result'].iloc[-1] > 
            moving_averages[1]['result'].iloc[-1] > 
            moving_averages[2]['result'].iloc[-1] > 
            moving_averages[3]['result'].iloc[-1]):
            return self.Alignment.UP
        elif (current_price < moving_averages[0]['result'].iloc[-1] < 
            moving_averages[1]['result'].iloc[-1] < 
            moving_averages[2]['result'].iloc[-1] < 
            moving_averages[3]['result'].iloc[-1]):
            return self.Alignment.DOWN
        return self.Alignment.NONE
