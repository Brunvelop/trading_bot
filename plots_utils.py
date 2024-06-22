import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_prices(ax, visualization_df, extra_plots_price):
    ax.plot(visualization_df['Datetime'], visualization_df['Close'], label='Close Price', color='darkblue', linewidth=2)
    if extra_plots_price is not None:
        for plot_data, plot_kwargs in extra_plots_price:
            plot_type = plot_kwargs.pop('type', 'plot')
            if plot_type == 'scatter':
                ax.scatter(*plot_data, **plot_kwargs)
            else:
                ax.plot(*plot_data, **plot_kwargs)
    buy_points = visualization_df[visualization_df['type'] == 'buy_market']
    sell_points = visualization_df[visualization_df['type'] == 'sell_market']
    ax.scatter(buy_points['timestamp'], buy_points['price'], color='green', label='Buy', s=50)
    ax.scatter(sell_points['timestamp'], sell_points['price'], color='red', label='Sell', s=50)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax.legend(fontsize='large')
    ax.set_title('Buy and Sell Points Over Time', fontsize=16)
    ax.set_xlabel('Time', fontsize=14)
    ax.set_ylabel('Price', fontsize=14)

def plot_balance(ax, ax_extra, visualization_df, plot_modes):
    if 'balance_a' in plot_modes:
        ax.plot(visualization_df['Datetime'], visualization_df['balance_a'], label='DOG Balance', color='purple', linewidth=2)
        ax.set_ylabel('BTC Balance', fontsize=14)
        ax.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['balance_a'].iloc[-1], color='purple', s=10)
        ax.text(visualization_df['Datetime'].iloc[-1], visualization_df['balance_a'].iloc[-1], f"{visualization_df['balance_a'].iloc[-1]:.2f}", color='purple')
        ax.yaxis.grid(False)
    if 'balance_b' in plot_modes:
        ax_extra.plot(visualization_df['Datetime'], visualization_df['balance_b'], label='USDT Balance', color='orange', linewidth=2)
        ax_extra.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['balance_b'].iloc[-1], color='orange', s=10)
        ax_extra.text(visualization_df['Datetime'].iloc[-1], visualization_df['balance_b'].iloc[-1], f"{visualization_df['balance_b'].iloc[-1]:.2f}", color='orange')
    if 'total_value' in plot_modes:
        ax_extra.plot(visualization_df['Datetime'], visualization_df['total_value'], label='Total Balance', color='blue', linewidth=2)
        ax_extra.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['total_value'].iloc[-1], color='blue', s=10)
        ax_extra.text(visualization_df['Datetime'].iloc[-1], visualization_df['total_value'].iloc[-1], f"{visualization_df['total_value'].iloc[-1]:.2f}", color='blue')
    if 'hold_value' in plot_modes:
        ax_extra.plot(visualization_df['Datetime'], visualization_df['hold_value'], label='HOLD Value', color='cyan', linewidth=2)
        ax_extra.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['hold_value'].iloc[-1], color='cyan', s=10)
        ax_extra.text(visualization_df['Datetime'].iloc[-1], visualization_df['hold_value'].iloc[-1], f"{visualization_df['hold_value'].iloc[-1]:.2f}", color='cyan')
    
    # Ajustar la frecuencia de los ticks en el eje x
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    
    ax.legend(loc='center left', bbox_to_anchor=(0, 0.5), fontsize='small')
    ax_extra.legend(loc='center left', bbox_to_anchor=(0, 0.6), fontsize='small')
    ax.set_title('Strategy', fontsize=16)
    ax.set_xlabel('Time', fontsize=14)
    ax.set_ylabel('BTC balance', fontsize=14)
    ax_extra.set_ylabel('Total Spend / Total Value', fontsize=14)

def plot_extra(ax, extra_plot):
    for plot_data, plot_kwargs in extra_plot:
        plot_type = plot_kwargs.pop('type', 'plot')
        if plot_type == 'scatter':
            ax.scatter(*plot_data, **plot_kwargs)
        else:
            ax.plot(*plot_data, **plot_kwargs)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax.legend(fontsize='large')
    ax.set_title('Extra Plot', fontsize=16)
    ax.set_xlabel('Time', fontsize=14)
    ax.set_ylabel('Value', fontsize=14)

def draw_graphs(visualization_df, plot_modes, extra_plots_price=None, extra_plot=None, save_path=None):
    plt.style.use('ggplot')
    if 'price' in plot_modes:
        if extra_plot is None:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 18), sharex=True)
        else:
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 18), sharex=True)
        plot_prices(ax1, visualization_df, extra_plots_price)
        plot_balance(ax2, ax2.twinx(), visualization_df, plot_modes)
        if extra_plot is not None:
            plot_extra(ax3, extra_plot)
    else:
        if extra_plot is None:
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 6))
        else:
            fig, (ax2, ax3) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
        plot_balance(ax2, ax2.twinx(), visualization_df, plot_modes)
        if extra_plot is not None:
            plot_extra(ax3, extra_plot)
    
    if save_path:
        fig.savefig(save_path)
    else:
        plt.show()