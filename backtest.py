import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from backtester import Backtester
import strategies

def load_data(filename, start=None, end=None):
    data = pd.read_csv(filename)
    
    if start is not None and end is not None:
        data = data.iloc[start:end]
    elif start is not None:
        data = data.iloc[start:]
    elif end is not None:
        data = data.iloc[:end]
    
    return data



def load_random_data(filename, duration=1000, variation=0.0, tolerancia=0.01):
    data = pd.read_csv(filename)
    n = len(data)
    
    while True:
        # Seleccionar un índice de inicio aleatorio
        start = np.random.randint(0, n - duration)
        end = start + duration
        
        # Extraer el tramo de datos
        segment = data.iloc[start:end]
        
        # Calcular la variación porcentual
        start_price = segment.iloc[0]['Close']  # Asumiendo que 'Close' es la columna de precios
        end_price = segment.iloc[-1]['Close']
        actual_variation = (end_price - start_price) / start_price
        
        # Si la variación porcentual es igual a la variación deseada, devolver el segmento
        if np.isclose(actual_variation, variation, atol=tolerancia):  # Tolerancia de 1%
            return segment

def fix_dates(data, backtester):
    memory_df = pd.DataFrame(backtester.memory)
    memory_df['timestamp'] = pd.to_datetime(memory_df['timestamp']).dt.tz_localize(None)
    data['Datetime'] = pd.to_datetime(data['Datetime']).dt.tz_localize(None)
    return memory_df, data

def generate_visualization_df(data, memory_df, plot_modes, initial_balance_a=0):
    memory_df_executed = memory_df.drop(memory_df[memory_df['executed'] == False].index)
    visualization_df = pd.merge(data, memory_df_executed, left_on='Datetime', right_on='timestamp', how='left')

    if 'hodl_value' in plot_modes:
        visualization_df = calculate_hodl_value(visualization_df, initial_balance_a)
    if 'balance_a' in plot_modes or 'total_value' in plot_modes:
        visualization_df = calculate_balance_a(visualization_df, initial_balance_a)
    if 'balance_b' in plot_modes or 'total_value' in plot_modes:
        visualization_df = calculate_balance_b(visualization_df)
    if 'total_value' in plot_modes:
        visualization_df = calculate_total_value(visualization_df)

    return visualization_df

def calculate_total_value(visualization_df):
    # Crear una nueva columna 'total_value' en visualization_df
    visualization_df['total_value'] = 0.0

    # Calcular el valor total
    visualization_df['total_value'] = visualization_df['balance_a'] + visualization_df['balance_b'] * visualization_df['Close']

    return visualization_df

def calculate_balance_b(visualization_df, initial_balance_b = 0):

    balance_b_values = []
    strategy = strategies.MovingAverageStrategy()

    for i in range(len(visualization_df)):
        sub_df = visualization_df.iloc[:i+1]
        balance_b = strategy.get_balance_b(sub_df)
        balance_b_values.append(balance_b)

    visualization_df['balance_b'] = balance_b_values
    
    return visualization_df

def calculate_balance_a(visualization_df, initial_balance_a = 10000):

    # Crear una nueva columna 'cost' que contenga el costo de cada operación
    visualization_df['cost'] = (visualization_df['price'] * visualization_df['amount']).fillna(0)
    
    # Invertir el costo para las operaciones de venta
    visualization_df.loc[visualization_df['type'] == 'sell_market', 'cost'] *= -1

    # Crear una nueva columna 'fees' que contenga las tarifas de cada operación
    visualization_df['fees'] = visualization_df[visualization_df['order_info'].notna()].apply(lambda row: row['order_info'].get('fees'), axis=1)
    visualization_df['fees'] = visualization_df['fees'].fillna(0)
    # Calcular el balance acumulativo teniendo en cuenta las tarifas
    visualization_df['balance_a'] = initial_balance_a - visualization_df['cost'].cumsum() - visualization_df['fees'].cumsum()
    
    # Eliminar las columnas 'cost' y 'fees' ya que no son necesarias
    visualization_df.drop(columns=['cost', 'fees'], inplace=True)
    
    return visualization_df

def calculate_hodl_value(visualization_df, initial_balance_a = 10000):
    initial_balance_b = initial_balance_a / visualization_df['Close'].iloc[0]

    # Crear una nueva columna 'hodl_value' que contenga el valor de hodling
    visualization_df['hodl_value'] = initial_balance_b * visualization_df['Close']

    return visualization_df

def draw_graphs(visualization_df, plot_modes, extra_plots_price=None, extra_plot=None):
    # Establecer el estilo del gráfico
    plt.style.use('ggplot')

    if extra_plot is None:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
    else:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 18), sharex=True)


    # Dibujar los precios de cierre con un color azul oscuro
    ax1.plot(visualization_df['Datetime'], visualization_df['Close'], label='Close Price', color='darkblue', linewidth=2)

    if extra_plots_price is not None:
        for plot_data, plot_kwargs in extra_plots_price:
            plot_type = plot_kwargs.pop('type', 'plot')
            if plot_type == 'scatter':
                ax1.scatter(*plot_data, **plot_kwargs)
            else:
                ax1.plot(*plot_data, **plot_kwargs)

    # Dibujar los puntos de compra y venta con un tamaño personalizado
    buy_points = visualization_df[visualization_df['type'] == 'buy_market']
    sell_points = visualization_df[visualization_df['type'] == 'sell_market']
    ax1.scatter(buy_points['timestamp'], buy_points['price'], color='green', label='Buy', s=50)
    ax1.scatter(sell_points['timestamp'], sell_points['price'], color='red', label='Sell', s=50)

    # Formatear el eje x para mostrar las fechas correctamente
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    # Añadir una leyenda con una fuente personalizada
    ax1.legend(fontsize='large')

    # Añadir títulos a los ejes y al gráfico
    ax1.set_title('Buy and Sell Points Over Time', fontsize=16)
    ax1.set_xlabel('Time', fontsize=14)
    ax1.set_ylabel('Price', fontsize=14)

    # Mostrar la gráfica
    if 'balance_b' in plot_modes:
        ax2.plot(visualization_df['Datetime'], visualization_df['balance_b'], label='BTC Balance', color='purple', linewidth=2)
        ax2.set_ylabel('BTC Balance', fontsize=14)
        ax2.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['balance_b'].iloc[-1], color='purple', s=10)
        ax2.text(visualization_df['Datetime'].iloc[-1], visualization_df['balance_b'].iloc[-1], f"{visualization_df['balance_b'].iloc[-1]:.2f}", color='purple')
        ax2.yaxis.grid(False)


    # Crear un segundo eje y para 'EUR Balance'
    ax2_extra = ax2.twinx()
    if 'balance_a' in plot_modes:
        ax2_extra.plot(visualization_df['Datetime'], visualization_df['balance_a'], label='EUR Balance', color='orange', linewidth=2)
        ax2_extra.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['balance_a'].iloc[-1], color='orange', s=10)
        ax2_extra.text(visualization_df['Datetime'].iloc[-1], visualization_df['balance_a'].iloc[-1], f"{visualization_df['balance_a'].iloc[-1]:.2f}", color='orange')
    if 'total_value' in plot_modes:
        ax2_extra.plot(visualization_df['Datetime'], visualization_df['total_value'], label='Total Balance', color='blue', linewidth=2)
        ax2_extra.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['total_value'].iloc[-1], color='blue', s=10)
        ax2_extra.text(visualization_df['Datetime'].iloc[-1], visualization_df['total_value'].iloc[-1], f"{visualization_df['total_value'].iloc[-1]:.2f}", color='blue')

    if 'hodl_value' in plot_modes:
        ax2_extra.plot(visualization_df['Datetime'], visualization_df['hodl_value'], label='HODL Value', color='cyan', linewidth=2)
        ax2_extra.scatter(visualization_df['Datetime'].iloc[-1], visualization_df['hodl_value'].iloc[-1], color='cyan', s=10)
        ax2_extra.text(visualization_df['Datetime'].iloc[-1], visualization_df['hodl_value'].iloc[-1], f"{visualization_df['hodl_value'].iloc[-1]:.2f}", color='cyan')

    ax2_extra.set_ylabel('EUR', fontsize=14)

    # Formatear el eje x para mostrar las fechas correctamente
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    # Añadir una leyenda con una fuente personalizada
    ax2.legend(loc='center left', bbox_to_anchor=(0, 0.5), fontsize='small')
    ax2_extra.legend(loc='center left', bbox_to_anchor=(0, 0.6), fontsize='small')

    # Añadir títulos a los ejes y al gráfico
    ax2.set_title('Strategy', fontsize=16)
    ax2.set_xlabel('Time', fontsize=14)
    ax2.set_ylabel('BTC balance', fontsize=14)
    ax2_extra.set_ylabel('Total Spend / Total Value', fontsize=14)  # Update label

    # Añadir la tercera gráfica
    if extra_plot is not None:
        for plot_data, plot_kwargs in extra_plot:
            plot_type = plot_kwargs.pop('type', 'plot')
            if plot_type == 'scatter':
                ax3.scatter(*plot_data, **plot_kwargs)
            else:
                ax3.plot(*plot_data, **plot_kwargs)

        # Formatear el eje x para mostrar las fechas correctamente
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

        # Añadir una leyenda con una fuente personalizada
        ax3.legend(fontsize='large')

        # Añadir títulos a los ejes y al gráfico
        ax3.set_title('Extra Plot', fontsize=16)
        ax3.set_xlabel('Time', fontsize=14)
        ax3.set_ylabel('Value', fontsize=14)

    plt.show()



# Cargar los datos
# data = load_data('data/BTC_EUR_1m.csv', start=None, end=None)
# data = load_data('data/BTC_USDT_15m.csv', start=None, end=10000)
data = load_random_data('data/BTC_USDT_1m.csv', duration=432000, variation=-0.30, tolerancia=0.01)

#Variables
fee = 0.003
initial_balance_a = 0
plot_modes = ['balance_a', 'total_value', 'balance_b'] # plot_modes = ['balance_a', 'total_value', 'hodl_value', 'balance_b']

#Run strategy
strategy = strategies.MultiMovingAverageStrategy(cost=5, fee=fee)
backtester = Backtester(strategy, fee=fee)
actions = backtester.simulate_real_time_execution(data, window_size = 350)

#Fix dates
memory_df, data = fix_dates(data, backtester)

#Generate Visualization df
visualization_df = generate_visualization_df(data, memory_df, plot_modes, initial_balance_a=initial_balance_a)

# # Agregar extra_plots_price
ma_10 = data['Close'].rolling(window=10).mean()
ma_50 = data['Close'].rolling(window=50).mean()
ma_100 = data['Close'].rolling(window=100).mean()
ma_200 = data['Close'].rolling(window=200).mean()

extra_plots_price = [
    ((visualization_df['Datetime'], ma_10), {'color': 'blue', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 10', 'type': 'plot'}),
    ((visualization_df['Datetime'], ma_50), {'color': 'orange', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 50', 'type': 'plot'}),
    ((visualization_df['Datetime'], ma_100), {'color': 'green', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 100', 'type': 'plot'}),
    ((visualization_df['Datetime'], ma_200), {'color': 'red', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 200', 'type': 'plot'})
]

# plot_3 = [
#     ((visualization_df['Datetime'], 3*std_dev_values), {'color': 'green', 'linewidth': 2, 'alpha':0.5, 'label': 'tandard Deviation', 'type': 'plot'}),
#     ((visualization_df['Datetime'], avg_range_values), {'color': 'red', 'linewidth': 2, 'alpha':0.5, 'label': 'Average RangeS', 'type': 'plot'}),
# ]

draw_graphs(visualization_df, plot_modes, extra_plots_price)








# #Calculate and add Visualization extras
# visualization_df['Moving_Avg'] = visualization_df['Close'].rolling(window=10).mean()
# stop_loss_df = memory_df[memory_df['type'] == 'stop_loss']
# extra_plots_price = [
#     ((stop_loss_df['timestamp'], stop_loss_df['price']), {'color': 'cyan', 's': 3, 'label': 'Stop Loss', 'type': 'scatter'}),
#     ((visualization_df['Datetime'], visualization_df['Moving_Avg']), {'color': 'orange', 'linewidth': 2, 'alpha':0.5, 'type': 'plot'}),
# ]

# bar_range = (data['High'] - data['Low']).abs() / data['Low'] * 100
# avg_range = bar_range.ewm(span=50).mean()
# std_dev = avg_range.rolling(window=200).std()
# plot_3 = [
#     (
#         (data['Datetime'], avg_range), 
#         {'color': 'green', 'linewidth': 2, 'alpha':0.5, 'label': 'Average Range', 'type': 'plot'}
#     ),
#     (
#         (data['Datetime'], std_dev), 
#         {'color': 'red', 'linewidth': 2, 'alpha':0.5, 'label': 'Standard Deviation', 'type': 'plot'}
#     ),
# ]
# draw_graphs(visualization_df, ['total_value', 'balance_b'], extra_plots_price, plot_3)

# Calcular sma_200 y std_dev

