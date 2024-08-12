from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Tuple, Dict, Any, Optional

from definitions import PlotMode, StrategyExecResult

class StrategyExecResultDrawer:
    @staticmethod
    def _add_prices(
            ax: plt.Axes,
            df: StrategyExecResult,
            extra_plots_price: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None
        ) -> None:
        ax.plot(df['Date'], df['Close'], label='Close Price', color='darkblue', linewidth=2)
        
        if extra_plots_price:
            for plot_data, plot_kwargs in extra_plots_price:
                plot_type = plot_kwargs.pop('type', 'plot')
                getattr(ax, plot_type)(*plot_data, **plot_kwargs)
        
        # Plot buy and sell points
        if 'type' in df.columns:
            for trade_type, color, label in [('buy_market', 'green', 'Buy'), ('sell_market', 'red', 'Sell')]:
                points = df[df['type'] == trade_type]
                ax.scatter(points['Date'], points['price'], color=color, label=label, s=50)
        
        # Set up axes and labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.legend(fontsize='large')
        ax.set_title('Buy and Sell Points Over Time', fontsize=16)
        ax.set_xlabel('Time', fontsize=14)
        ax.set_ylabel('Price', fontsize=14)

    def _plot_balances(
            ax: plt.Axes,
            ax_extra: plt.Axes,
            df: StrategyExecResult, 
            plot_modes: List[PlotMode]
        ) -> None:
        plot_configs = {
            PlotMode.BALANCE_A: ('balance_a', 'DOG Balance', 'darkorange', ax, '-', 3, 1.0),
            PlotMode.BALANCE_B: ('balance_b', 'USDT Balance', 'limegreen', ax_extra, '-', 3, 1.0),
            PlotMode.HOLD_VALUE: ('hold_value', 'HOLD Value', 'teal', ax_extra, ':', 1, 0.5),
            PlotMode.TOTAL_VALUE_A: ('total_value_a', 'Total Value (en DOG)', 'coral', ax, '--', 1, 0.5),
            PlotMode.TOTAL_VALUE_B: ('total_value_b', 'Total Value (en USDT)', 'darkgreen', ax_extra, '--', 1, 0.5),
            PlotMode.ADJUSTED_A_BALANCE: ('adjusted_a_balance', 'adj_a', 'orange', ax, '-', 1, 1),
            PlotMode.ADJUSTED_B_BALANCE: ('adjusted_b_balance', 'adj_b', 'yellowgreen', ax_extra, '-', 1, 1),
        }
        
        lines = []
        labels = []
        used_axes = set()
        
        for mode, (column, label, color, axis, linestyle, linewidth, alpha) in plot_configs.items():
            if mode in plot_modes:
                line, = axis.plot(df['Date'], df[column], 
                                label=label, color=color, linewidth=linewidth, linestyle=linestyle, alpha=alpha)
                            
                # Valor inicial
                first_value = df[column].iloc[0]
                first_Date = df['Date'].iloc[0]
                axis.scatter(first_Date, first_value, color=color, s=10)
                axis.text(first_Date, first_value, f"{first_value:.0f}", color=color, ha='right', va='bottom')
                
                # Valor final
                last_value = df[column].iloc[-1]
                last_Date = df['Date'].iloc[-1]
                axis.scatter(last_Date, last_value, color=color, s=10)
                axis.text(last_Date, last_value, f"{last_value:.0f}", color=color, ha='left', va='top')
                
                lines.append(line)
                labels.append(label)
                used_axes.add(axis)
        
        # Configuración de ejes solo si se usan
        if ax in used_axes:
            ax.set_ylabel('DOG', fontsize=14)
            ax.yaxis.grid(False)
        
        if ax_extra in used_axes:
            ax_extra.set_ylabel('USDT', fontsize=14)
        
        # Configuración común
        for axis in used_axes:
            axis.xaxis.set_major_locator(mdates.AutoDateLocator())
            axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        
        # Leyenda dentro del gráfico con una sola columna
        if lines:
            ax.legend(lines, labels, loc='center left', fontsize='small', ncol=1)
        
        ax.set_title('Balances', fontsize=16)
        ax.set_xlabel('Time', fontsize=14)

        # Ocultar ejes no utilizados
        if ax not in used_axes:
            ax.axis('off')
        if ax_extra not in used_axes:
            ax_extra.axis('off')

    def _plot_extra(ax: plt.Axes, extra_plot: List[Tuple[Tuple, Dict[str, Any]]]) -> None:
        # Diccionario para mapear tipos de gráficos a métodos de matplotlib
        plot_methods = {
            'scatter': ax.scatter,
            'plot': ax.plot,
            'bar': ax.bar,
            'hist': ax.hist
        }
        
        for plot_data, plot_kwargs in extra_plot:
            plot_type = plot_kwargs.pop('type', 'plot')
            plot_method = plot_methods.get(plot_type, ax.plot)
            plot_method(*plot_data, **plot_kwargs)
        
        # Configuración del eje x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Configuración de la leyenda y etiquetas
        ax.legend(fontsize='large', loc='best')
        ax.set_title(plot_kwargs.get('title', 'Extra Plot'), fontsize=16)
        ax.set_xlabel(plot_kwargs.get('xlabel', 'Time'), fontsize=14)
        ax.set_ylabel(plot_kwargs.get('ylabel', 'Value'), fontsize=14)
        
        # Ajustar diseño
        plt.tight_layout()

    @staticmethod
    def draw_result(
        df: StrategyExecResult,
        plot_modes: List[PlotMode],
        extra_plots_price: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None,
        extra_plot: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None,
        save_path: Optional[Path] = None,
        show: bool = True
    ) -> None:
        plt.style.use('ggplot')

        num_subplots = (PlotMode.PRICE in plot_modes) + bool(extra_plot) + any(
            mode in plot_modes for mode in [
                PlotMode.BALANCE_A,
                PlotMode.BALANCE_B,
                PlotMode.HOLD_VALUE,
                PlotMode.TOTAL_VALUE_A,
                PlotMode.TOTAL_VALUE_B,
                PlotMode.ADJUSTED_A_BALANCE,
                PlotMode.ADJUSTED_B_BALANCE
            ]
        )
        if num_subplots > 1:
            fig, axes = plt.subplots(num_subplots, 1, figsize=(10, 6 * num_subplots), sharex=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            axes = [ax]
        
        current_ax = 0
        
        if PlotMode.PRICE in plot_modes:
            StrategyExecResultDrawer._add_prices(axes[current_ax], df, extra_plots_price)
            current_ax += 1
        
        if (PlotMode.BALANCE_A in plot_modes
            or PlotMode.BALANCE_B in plot_modes
            or PlotMode.HOLD_VALUE in plot_modes
            or PlotMode.TOTAL_VALUE_A in plot_modes
            or PlotMode.TOTAL_VALUE_B in plot_modes
            or PlotMode.ADJUSTED_A_BALANCE in plot_modes
            or PlotMode.ADJUSTED_B_BALANCE in plot_modes
        ):
            StrategyExecResultDrawer._plot_balances(axes[current_ax], axes[current_ax].twinx(), df, plot_modes)
            current_ax += 1
        
        if extra_plot:
            StrategyExecResultDrawer._plot_extra(axes[current_ax], extra_plot)
        
        plt.tight_layout()
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path)
        if show:
            plt.show()


    def calculate_moving_averages_extra_plot(data) -> list:
        ma_10 = data['Close'].rolling(window=10).mean()
        ma_50 = data['Close'].rolling(window=50).mean()
        ma_100 = data['Close'].rolling(window=100).mean()
        ma_200 = data['Close'].rolling(window=200).mean()

        extra_plots_price = [
            ((data['Date'], ma_10), {'color': 'blue', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 10', 'type': 'plot'}),
            ((data['Date'], ma_50), {'color': 'orange', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 50', 'type': 'plot'}),
            ((data['Date'], ma_100), {'color': 'green', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 100', 'type': 'plot'}),
            ((data['Date'], ma_200), {'color': 'red', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 200', 'type': 'plot'})
        ]
        return extra_plots_price