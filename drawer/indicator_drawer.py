from typing import List, Tuple
import pandas as pd
from indicators import IndicatorTypes

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

class IndicatorPlotManager:
    def create_price_plots(self, data: pd.DataFrame, indicators: List[dict]) -> List[Tuple[Tuple, dict]]:
        """Create plots for price-related indicators"""
        plots = []
        for i, indicator in enumerate(indicators):
            if isinstance(indicator.type, IndicatorTypes.Price):
                plot_data = (data['date'], indicator.result)
                plot_style = IndicatorPlotConfig.get_plot_style(i, indicator.name)
                plots.append((plot_data, plot_style))

        return plots if plots else None
    
    def create_technical_plots(self, data: pd.DataFrame, indicators: List[dict]) -> List[Tuple[Tuple, dict]]:
        """Create plots for technical indicators"""
        plots = []
        for i, indicator in enumerate(indicators):
            if isinstance(indicator.type, IndicatorTypes.Extra):
                plot_data = (data['date'], indicator.result)
                plot_style = IndicatorPlotConfig.get_plot_style(i, indicator.name)
                plots.append((plot_data, plot_style))

        return plots if plots else None
