import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from backtester import Backtester
import strategies


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
    
    # Calcular el balance acumulativo
    visualization_df['balance_a'] = initial_balance_a - visualization_df['cost'].cumsum()
    
    # Eliminar la columna 'cost' ya que no es necesaria
    visualization_df.drop(columns=['cost'], inplace=True)
    
    return visualization_df

def calculate_hodl_value(visualization_df, initial_balance_a = 10000):
    initial_balance_b = initial_balance_a / visualization_df['Close'].iloc[0]

    # Crear una nueva columna 'hodl_value' que contenga el valor de hodling
    visualization_df['hodl_value'] = initial_balance_b * visualization_df['Close']

    return visualization_df

def draw_graphs(memory_df):
    # Establecer el estilo del gráfico
    plt.style.use('ggplot')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

    # Dibujar los precios de cierre con un color azul oscuro
    ax1.plot(memory_df['Datetime'], memory_df['Close'], label='Close Price', color='darkblue', linewidth=2)

    # # Dibujar la media móvil de 200 períodos
    # memory_df['Moving_Avg'] = memory_df['Close'].rolling(window=200).mean()
    # ax1.plot(memory_df['Datetime'], memory_df['Moving_Avg'], label='200 Period Moving Average', color='orange', linewidth=2)

    # Dibujar los puntos de compra y venta con un tamaño personalizado
    buy_points = memory_df[memory_df['type'] == 'buy_market']
    sell_points = memory_df[memory_df['type'] == 'sell_market']
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
    ax2.plot(memory_df['Datetime'], memory_df['balance_b'], label='BTC Balance', color='purple', linewidth=2)
    ax2.set_ylabel('BTC Balance', fontsize=14)
    ax2.scatter(memory_df['Datetime'].iloc[-1], memory_df['balance_b'].iloc[-1], color='purple', s=10)
    ax2.text(memory_df['Datetime'].iloc[-1], memory_df['balance_b'].iloc[-1], f"{memory_df['balance_b'].iloc[-1]:.2f}", color='purple')
    ax2.yaxis.grid(False)


    # Crear un segundo eje y para 'EUR Balance'
    ax3 = ax2.twinx()
    ax3.plot(memory_df['Datetime'], memory_df['balance_a'], label='EUR Balance', color='orange', linewidth=2)
    ax3.plot(memory_df['Datetime'], memory_df['total_value'], label='Total Balance', color='blue', linewidth=2)
    ax3.plot(memory_df['Datetime'], memory_df['hodl_value'], label='HODL Value', color='cyan', linewidth=2)

    ax3.scatter(memory_df['Datetime'].iloc[-1], memory_df['balance_a'].iloc[-1], color='orange', s=10)
    ax3.text(memory_df['Datetime'].iloc[-1], memory_df['balance_a'].iloc[-1], f"{memory_df['balance_a'].iloc[-1]:.2f}", color='orange')
    ax3.scatter(memory_df['Datetime'].iloc[-1], memory_df['total_value'].iloc[-1], color='blue', s=10)
    ax3.text(memory_df['Datetime'].iloc[-1], memory_df['total_value'].iloc[-1], f"{memory_df['total_value'].iloc[-1]:.2f}", color='blue')
    ax3.scatter(memory_df['Datetime'].iloc[-1], memory_df['hodl_value'].iloc[-1], color='cyan', s=10)
    ax3.text(memory_df['Datetime'].iloc[-1], memory_df['hodl_value'].iloc[-1], f"{memory_df['hodl_value'].iloc[-1]:.2f}", color='cyan')

    ax3.set_ylabel('EUR', fontsize=14)

    # Formatear el eje x para mostrar las fechas correctamente
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    # Añadir una leyenda con una fuente personalizada
    ax2.legend(loc='center left', bbox_to_anchor=(0, 0.5), fontsize='small')
    ax3.legend(loc='center left', bbox_to_anchor=(0, 0.6), fontsize='small')

    # Añadir títulos a los ejes y al gráfico
    ax2.set_title('Strategy', fontsize=16)
    ax2.set_xlabel('Time', fontsize=14)
    ax2.set_ylabel('BTC balance', fontsize=14)
    ax3.set_ylabel('Total Spend / Total Value', fontsize=14)  # Update label


    # Mostrar la gráfica
    plt.show()



# Cargar los datos
data = pd.read_csv('data/BTC_EUR_1m.csv')
data = data.tail(1000)
# data = data.iloc[-350:-250]

window_size = 350
strategy = strategies.SuperStrategyFutures(cost=10)
backtester = Backtester(strategy)

data['Datetime'] = pd.to_datetime(data['Datetime'])
data = data.drop_duplicates('Datetime', keep='first')
# Simular la ejecución en tiempo real
for i in tqdm(range(window_size, len(data))):
    window_data = data.iloc[i-window_size+1:i+1]
    actions = backtester.execute_strategy(window_data)

#Fix data
memory_df = pd.DataFrame(backtester.memory)
memory_df['timestamp'] = pd.to_datetime(memory_df['timestamp']).dt.tz_localize(None)
memory_df['timestamp'] = pd.to_datetime(memory_df['timestamp']).dt.tz_localize(None)
data['Datetime'] = pd.to_datetime(data['Datetime']).dt.tz_localize(None)

#Calculate extra
visualization_df = pd.merge(data, memory_df, left_on='Datetime', right_on='timestamp', how='left')

initial_balance_a = 2000
visualization_df = calculate_balance_a(visualization_df, initial_balance_a)
visualization_df = calculate_hodl_value(visualization_df, initial_balance_a)
visualization_df = calculate_balance_b(visualization_df)
visualization_df = calculate_total_value(visualization_df)

#Draw
draw_graphs(visualization_df)