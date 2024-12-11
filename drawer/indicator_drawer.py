from typing import List, Tuple, Dict
import pandas as pd
from indicators import IndicatorTypes, Indicator

class IndicatorPlotConfig:
    DEFAULT_COLORS = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray']
    
    # Configuración base por tipo de indicador
    BASE_CONFIGS = {
        IndicatorTypes.Price.SIMPLE_MOVING_AVERAGE: {
            'linewidth': 2,
            'alpha': 0.7,
            'linestyle': '-'
        },
        IndicatorTypes.Extra.RELATIVE_STRENGTH_INDEX: {
            'linewidth': 2,
            'alpha': 0.7,
            'linestyle': '-'
        },
        IndicatorTypes.Extra.VELOCITY: {
            'linewidth': 1.5,
            'alpha': 0.2,
            'linestyle': '-'
        },
        IndicatorTypes.Extra.ACCELERATION: {
            'linewidth': 1.5,
            'alpha': 1,
            'linestyle': '-'
        }
    }
    
    # Contador para mantener registro de cuántas instancias de cada tipo se han creado
    _type_counters: Dict = {}
    
    @classmethod
    def get_plot_style(cls, indicator: Indicator) -> dict:
        """Get the plotting style for an indicator"""
        # Inicializar contador si no existe
        if indicator.type not in cls._type_counters:
            cls._type_counters[indicator.type] = 0
            
        # Obtener color de la paleta
        color_index = cls._type_counters[indicator.type] % len(cls.DEFAULT_COLORS)
        color = cls.DEFAULT_COLORS[color_index]
        
        # Incrementar contador
        cls._type_counters[indicator.type] += 1
        
        # Obtener configuración base
        base_config = cls.BASE_CONFIGS.get(
            indicator.type,
            {
                'linewidth': 1,
                'alpha': 0.5,
                'linestyle': '-'
            }
        )
        
        return {
            **base_config,
            'color': color,
            'label': indicator.name,
            'type': 'plot'
        }
    
    @classmethod
    def reset_counters(cls):
        """Resetear los contadores de tipos"""
        cls._type_counters = {}

class IndicatorPlotManager:
    def create_price_plots(self, data: pd.DataFrame, indicators: List[Indicator]) -> List[Tuple[Tuple, dict]]:
        """Create plots for price-related indicators"""
        IndicatorPlotConfig.reset_counters()  # Reset counters before creating plots
        plots = []
        for indicator in indicators:
            if isinstance(indicator.type, IndicatorTypes.Price):
                plot_data = (data['date'], indicator.result)
                plot_style = IndicatorPlotConfig.get_plot_style(indicator)
                plots.append((plot_data, plot_style))

        return plots if plots else None
    
    def create_technical_plots(self, data: pd.DataFrame, indicators: List[Indicator]) -> List[Tuple[Tuple, dict]]:
        """Create plots for technical indicators"""
        IndicatorPlotConfig.reset_counters()  # Reset counters before creating plots
        plots = []
        for indicator in indicators:
            if isinstance(indicator.type, IndicatorTypes.Extra):
                plot_data = (data['date'], indicator.result)
                plot_style = IndicatorPlotConfig.get_plot_style(indicator)
                plots.append((plot_data, plot_style))

        return plots if plots else None
