import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd

from definitions import PlotMode


def plot_prices(ax: plt.Axes, visualization_df: pd.DataFrame,
                extra_plots_price: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None) -> None:
    # Plot close price
    ax.plot(visualization_df['Datetime'], visualization_df['Close'], label='Close Price', color='darkblue', linewidth=2)
    
    # Plot extra plots
    if extra_plots_price:
        for plot_data, plot_kwargs in extra_plots_price:
            plot_type = plot_kwargs.pop('type', 'plot')
            getattr(ax, plot_type)(*plot_data, **plot_kwargs)
    
    # Plot buy and sell points
    if 'type' in visualization_df.columns:
        for trade_type, color, label in [('buy_market', 'green', 'Buy'), ('sell_market', 'red', 'Sell')]:
            points = visualization_df[visualization_df['type'] == trade_type]
            ax.scatter(points['Datetime'], points['price'], color=color, label=label, s=50)
    
    # Set up axes and labels
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax.legend(fontsize='large')
    ax.set_title('Buy and Sell Points Over Time', fontsize=16)
    ax.set_xlabel('Time', fontsize=14)
    ax.set_ylabel('Price', fontsize=14)

def plot_balances(ax: plt.Axes, ax_extra: plt.Axes, visualization_df: pd.DataFrame, 
                  plot_modes: List[PlotMode]) -> None:
    first_datetime = visualization_df['Datetime'].iloc[0]
    last_datetime = visualization_df['Datetime'].iloc[-1]

    plot_configs = {
        PlotMode.BALANCE_A: ('balance_a', 'DOG Balance', 'darkorange', ax, '-', 3, 1.0),
        PlotMode.BALANCE_B: ('balance_b', 'USDT Balance', 'limegreen', ax_extra, '-', 3, 1.0),
        PlotMode.HOLD_VALUE: ('hold_value', 'HOLD Value', 'teal', ax_extra, ':', 1, 0.5),
        PlotMode.TOTAL_VALUE_A: ('total_value_a', 'Total Value (en DOG)', 'coral', ax, '--', 1, 0.5),
        PlotMode.TOTAL_VALUE_B: ('total_value_b', 'Total Value (en USDT)', 'darkgreen', ax_extra, '--', 1, 0.5),
        PlotMode.ADJUSTED_B_BALANCE: ('adjusted_b_balance', 'Profit', 'yellowgreen', ax_extra, '-', 1, 1),
    }
    
    lines = []
    labels = []
    used_axes = set()
    
    for mode, (column, label, color, axis, linestyle, linewidth, alpha) in plot_configs.items():
        if mode in plot_modes:
            line, = axis.plot(visualization_df['Datetime'], visualization_df[column], 
                              label=label, color=color, linewidth=linewidth, linestyle=linestyle, alpha=alpha)
                        
            # Valor inicial
            first_value = visualization_df[column].iloc[0]
            axis.scatter(first_datetime, first_value, color=color, s=10)
            axis.text(first_datetime, first_value, f"{first_value:.0f}", color=color, ha='right', va='bottom')
            
            # Valor final
            last_value = visualization_df[column].iloc[-1]
            axis.scatter(last_datetime, last_value, color=color, s=10)
            axis.text(last_datetime, last_value, f"{last_value:.0f}", color=color, ha='left', va='top')
            
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

def plot_extra(ax: plt.Axes, extra_plot: List[Tuple[Tuple, Dict[str, Any]]]) -> None:
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

def draw_graphs(
    visualization_df: pd.DataFrame,
    plot_modes: List[PlotMode],
    extra_plots_price: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None,
    extra_plot: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None,
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    plt.style.use('ggplot')
    
    # Determinar el número de subplots necesarios
    num_subplots = 1 + (PlotMode.PRICE in plot_modes) + (extra_plot is not None)
    
    # Crear la figura y los ejes
    fig, axes = plt.subplots(num_subplots, 1, figsize=(10, 6 * num_subplots), sharex=True)
    
    # Asegurarse de que axes sea siempre una lista
    if num_subplots == 1:
        axes = [axes]
    
    # Índice para llevar un seguimiento del subplot actual
    current_ax = 0
    
    # Dibujar el gráfico de precios si es necesario
    if PlotMode.PRICE in plot_modes:
        plot_prices(axes[current_ax], visualization_df, extra_plots_price)
        current_ax += 1
    
    # Dibujar el gráfico de balances
    plot_balances(axes[current_ax], axes[current_ax].twinx(), visualization_df, plot_modes)
    current_ax += 1
    
    # Dibujar el gráfico extra si es necesario
    if extra_plot is not None:
        plot_extra(axes[current_ax], extra_plot)
    
    # Ajustar el diseño
    plt.tight_layout()
    
    # Guardar y/o mostrar el gráfico
    if save_path:
        fig.savefig(save_path)
    if show:
        plt.show()