from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Tuple, Dict, Any, Optional

from definitions import PlotMode, Backtest

class BacktestDrawer:
    @classmethod
    def draw(
        cls,
        df: Backtest,
        plot_modes: List[PlotMode],
        extra_plots_price: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None,
        extra_plot: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None,
        save_path: Optional[Path] = None,
        show: bool = True
    ) -> None:
        plt.style.use('ggplot')
        
        fig, axes = cls._setup_layout(plot_modes, extra_plot)
        
        current_ax = 0
        
        if PlotMode.PRICE in plot_modes:
            cls._draw_prices(axes[current_ax], df, extra_plots_price)
            current_ax += 1
        
        if extra_plot:
            cls._draw_extra(axes[current_ax], extra_plot)
            current_ax += 1

        if any(mode in plot_modes for mode in set(PlotMode) - {PlotMode.PRICE}):
            cls._draw_balances(axes[current_ax], axes[current_ax].twinx(), df, plot_modes)
        
        plt.tight_layout()
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path)
        if show:
            plt.show()

    @staticmethod
    def _setup_layout(plot_modes, extra_plot):
        plot_modes_excluding_price = set(PlotMode) - {PlotMode.PRICE}
        num_subplots = (PlotMode.PRICE in plot_modes) + bool(extra_plot) + any(
            mode in plot_modes for mode in plot_modes_excluding_price
        )
        if num_subplots > 1:
            fig, axes = plt.subplots(num_subplots, 1, figsize=(10, 6 * num_subplots), sharex=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            axes = [ax]
        
        return fig, axes

    @classmethod
    def _draw_prices(
            cls,
            ax: plt.Axes,
            df: Backtest,
            extra_plots_price: Optional[List[Tuple[Tuple, Dict[str, Any]]]] = None
        ) -> None:
        ax.plot(df['date'], df['close'], label='close Price', color='darkblue', linewidth=2)
        
        cls._draw_extra_plots_price(ax, extra_plots_price)
        cls._draw_buy_and_sell_points(ax, df)
        cls._customice_price_axes(ax)

    @staticmethod
    def _draw_extra_plots_price(ax, extra_plots_price):
        if extra_plots_price:
            for plot_data, plot_kwargs in extra_plots_price:
                plot_type = plot_kwargs.pop('type', 'plot')
                getattr(ax, plot_type)(*plot_data, **plot_kwargs)

    @staticmethod
    def _draw_buy_and_sell_points(ax, df):
        if 'type' in df.columns:
            for trade_type, color, label in [('buy_market', 'green', 'Buy'), ('sell_market', 'red', 'Sell')]:
                points = df[df['type'] == trade_type]
                ax.scatter(points['date'], points['price'], color=color, label=label, s=50)

    @staticmethod
    def _customice_price_axes(ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.legend(fontsize='large')
        ax.set_title('Buy and Sell Points Over Time', fontsize=16)
        ax.set_ylabel('Price', fontsize=14)

    @classmethod
    def _draw_balances(
            cls,
            ax: plt.Axes,
            ax_extra: plt.Axes,
            df: Backtest, 
            plot_modes: List[PlotMode]
        ) -> None:
        plot_configs = {
            PlotMode.BALANCE_A: {'column': 'balance_a', 'label': 'DOG Balance', 'color': 'darkorange','axis': ax, 'linestyle': '-', 'linewidth': 3, 'alpha': 1.0 },
            PlotMode.BALANCE_B: {'column': 'balance_b', 'label': 'USDT Balance', 'color': 'limegreen','axis': ax_extra, 'linestyle': '-', 'linewidth': 3, 'alpha': 1.0},
            PlotMode.HOLD_VALUE: {'column': 'hold_value', 'label': 'HOLD Value', 'color': 'teal','axis': ax_extra, 'linestyle': ':', 'linewidth': 1, 'alpha': 0.5},
            PlotMode.TOTAL_VALUE_A: {'column': 'total_value_a', 'label': 'Total Value (en DOG)', 'color': 'coral','axis': ax, 'linestyle': '--', 'linewidth': 1, 'alpha': 0.5},
            PlotMode.TOTAL_VALUE_B: {'column': 'total_value_b', 'label': 'Total Value (en USDT)', 'color': 'darkgreen','axis': ax_extra, 'linestyle': '--', 'linewidth': 1, 'alpha': 0.5},
            PlotMode.ADJUSTED_A_BALANCE: {'column': 'adjusted_a_balance', 'label': 'adj_a', 'color': 'orange','axis': ax, 'linestyle': '-', 'linewidth': 1, 'alpha': 1},
            PlotMode.ADJUSTED_B_BALANCE: {'column': 'adjusted_b_balance', 'label': 'adj_b', 'color': 'yellowgreen','axis': ax_extra, 'linestyle': '-', 'linewidth': 1, 'alpha': 1},
        }

        lines, labels, used_axes = [], [], set()
        for mode in plot_modes:
            if mode in plot_configs:
                config = plot_configs[mode]
                line = cls._draw_balances_lines(df, config)
                
                lines.append(line)
                labels.append(config.get('label'))
                used_axes.add(config.get('axis'))
        
        cls._customice_balances_axes(ax, ax_extra, lines, labels, used_axes)

    @staticmethod
    def _customice_balances_axes(ax, ax_extra, lines, labels, used_axes):
        if ax in used_axes:
            ax.set_ylabel('DOG', fontsize=14)
            ax.yaxis.grid(False)
        
        if ax_extra in used_axes:
            ax_extra.set_ylabel('USDT', fontsize=14)
        
        for axis in used_axes:
            axis.xaxis.set_major_locator(mdates.AutoDateLocator())
            axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        
        if lines:
            ax.legend(lines, labels, loc='center left', fontsize='small', ncol=1)
        
        ax.set_title('Balances', fontsize=16)

        if ax not in used_axes:
            ax.axis('off')
        if ax_extra not in used_axes:
            ax_extra.axis('off')

    @staticmethod
    def _draw_balances_lines(df: Backtest, config:tuple) -> plt.Line2D:
        line, = config.get('axis').plot(df['date'], df[config.get('column')],label=config.get('label'), color=config.get('color'), 
                        linewidth=config.get('linewidth'), linestyle=config.get('linestyle'), alpha=config.get('alpha'))
        
        for i in [0, -1]:
            value, date = df[config.get('column')].iloc[i], df['date'].iloc[i]
            config.get('axis').scatter(date, value, color=config.get('color'), s=10)
            config.get('axis').text(date, value, f"{value:.0f}", color=config.get('color'), 
                    ha='right' if i == 0 else 'left', va='bottom' if i == 0 else 'top')
        
        return line

    @classmethod
    def _draw_extra(cls, ax: plt.Axes, extra_plot: List[Tuple[Tuple, Dict[str, Any]]]) -> None:
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
        
        cls._customice_extra_plot_axes(ax, plot_kwargs)

    @staticmethod
    def _customice_extra_plot_axes(ax, plot_kwargs):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        ax.legend(fontsize='large', loc='best')
        ax.set_title(plot_kwargs.get('title', 'Extra Plot'), fontsize=16)
        ax.set_ylabel(plot_kwargs.get('ylabel', 'Value'), fontsize=14)
        
        plt.tight_layout()