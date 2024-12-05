from typing import List, Tuple, Dict, Any
import pandas as pd
from definitions import IndicatorTypes

class IndicatorPlotConfig:
    DEFAULT_COLORS = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray']
    
    @staticmethod
    def get_plot_style(index: int, name: str) -> dict:
        """Get the plotting style for an indicator"""
        return {
            'color': IndicatorPlotConfig.DEFAULT_COLORS[index % len(IndicatorPlotConfig.DEFAULT_COLORS)],
            'linewidth': 2,
            'alpha': 0.5,
            'label': name,
            'type': 'plot'
        }

class BaseIndicatorDrawer:
    def can_handle(self, indicator_type: IndicatorTypes) -> bool:
        """Check if this drawer can handle the given indicator type"""
        raise NotImplementedError
    
    def create_plot_data(self, dates: pd.Series, indicator: dict, index: int) -> Tuple[Tuple, dict]:
        """Create plot data for the indicator"""
        raise NotImplementedError

class PriceIndicatorDrawer(BaseIndicatorDrawer):
    def can_handle(self, indicator_type: IndicatorTypes) -> bool:
        return indicator_type == IndicatorTypes.SIMPLE_MOVING_AVERAGE
    
    def create_plot_data(self, dates: pd.Series, indicator: dict, index: int) -> Tuple[Tuple, dict]:
        plot_data = (dates, indicator['result'])
        plot_style = IndicatorPlotConfig.get_plot_style(index, indicator['name'])
        return plot_data, plot_style

class TechnicalIndicatorDrawer(BaseIndicatorDrawer):
    SUPPORTED_TYPES = [
        IndicatorTypes.RELATIVE_STRENGTH_INDEX,
        IndicatorTypes.VELOCITY,
        IndicatorTypes.ACCELERATION
    ]
    
    def can_handle(self, indicator_type: IndicatorTypes) -> bool:
        return indicator_type in self.SUPPORTED_TYPES
    
    def create_plot_data(self, dates: pd.Series, indicator: dict, index: int) -> Tuple[Tuple, dict]:
        plot_data = (dates, indicator['result'])
        plot_style = IndicatorPlotConfig.get_plot_style(index, indicator['name'])
        return plot_data, plot_style

class IndicatorDrawerFactory:
    def __init__(self):
        self.drawers = [
            PriceIndicatorDrawer(),
            TechnicalIndicatorDrawer()
        ]
    
    def get_drawer(self, indicator_type: IndicatorTypes) -> BaseIndicatorDrawer:
        for drawer in self.drawers:
            if drawer.can_handle(indicator_type):
                return drawer
        raise ValueError(f"No drawer found for indicator type: {indicator_type}")

class IndicatorPlotManager:
    def __init__(self):
        self.factory = IndicatorDrawerFactory()
    
    def create_price_plots(self, data: pd.DataFrame, indicators: List[dict]) -> List[Tuple[Tuple, dict]]:
        """Create plots for price-related indicators"""
        plots = []
        for i, indicator in enumerate(indicators):
            if indicator['type'] == IndicatorTypes.SIMPLE_MOVING_AVERAGE:
                drawer = self.factory.get_drawer(indicator['type'])
                plot_data = drawer.create_plot_data(data['date'], indicator, i)
                plots.append(plot_data)
        return plots if plots else None
    
    def create_technical_plots(self, data: pd.DataFrame, indicators: List[dict]) -> List[Tuple[Tuple, dict]]:
        """Create plots for technical indicators"""
        plots = []
        for i, indicator in enumerate(indicators):
            if indicator['type'] in TechnicalIndicatorDrawer.SUPPORTED_TYPES:
                drawer = self.factory.get_drawer(indicator['type'])
                plot_data = drawer.create_plot_data(data['date'], indicator, i)
                plots.append(plot_data)
        return plots if plots else None
