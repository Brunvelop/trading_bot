import pandas as pd
import matplotlib.pyplot as plt

data_1m = pd.read_csv('data/BTC_USD_1m.csv', index_col=0, parse_dates=True)
data_1m = pd.read_csv('data/old/BTC_USDT_1m.csv', index_col=0, parse_dates=True)
data_1m = data_1m.tail(1000000)


def calculate_moving_averages(data):
    windows = [10, 50, 100, 200]
    return [(window, data['Close'].rolling(window=window).mean()) for window in windows]

def calculate_conditions(data, moving_averages):
    # Desempaquetamos las medias móviles
    ma_10, ma_50, ma_100, ma_200 = [ma for _, ma in moving_averages]

    # Comprobamos si las medias móviles están alineadas hacia arriba o hacia abajo
    aligned_up = (ma_10 > ma_50) & (ma_50 > ma_100) & (ma_100 > ma_200)
    aligned_down = (ma_10 < ma_50) & (ma_50 < ma_100) & (ma_100 < ma_200)

    # Comprobamos si el precio está por encima o por debajo de todas las medias móviles
    above_all = (data['Close'] > ma_10) & (data['Close'] > ma_50) & (data['Close'] > ma_100) & (data['Close'] > ma_200)
    below_all = (data['Close'] < ma_10) & (data['Close'] < ma_50) & (data['Close'] < ma_100) & (data['Close'] < ma_200)

    # Como las medias móviles de mayor ventana tienen menos datos, rellenamos los valores faltantes con False
    aligned_up = aligned_up.reindex_like(data, method='pad').fillna(False)
    aligned_down = aligned_down.reindex_like(data, method='pad').fillna(False)
    above_all = above_all.reindex_like(data, method='pad').fillna(False)
    below_all = below_all.reindex_like(data, method='pad').fillna(False)

    return aligned_up, aligned_down, above_all, below_all

def calculate_segments_and_means(data, conditions):
    segments = []
    current_condition = None
    start_index = None

    for i, condition in enumerate(conditions):
        if condition != 0 and condition != current_condition:
            if current_condition is not None:
                segment_data = data[start_index:i][conditions[start_index:i] == current_condition]  # Filter data based on condition
                duration_color = len(segment_data)
                duration_total = i - start_index
                amplitude = ((segment_data.max() - segment_data.min()) / segment_data[0] * 100) if len(segment_data) > 0 else 0  # Amplitude calculation changed here
                segments.append((current_condition, segment_data.mean(), start_index, i, duration_color, duration_total, amplitude))
            start_index = i
            current_condition = condition

    # Añadimos el último segmento
    if current_condition is not None:
        segment_data = data[start_index:][conditions[start_index:] == current_condition]  # Filter data based on condition
        duration_color = len(segment_data)
        duration_total = len(data) - start_index
        amplitude = ((segment_data.max() - segment_data.min()) / segment_data[0] * 100) if len(segment_data) > 0 else 0  # Amplitude calculation changed here
        segments.append((current_condition, segment_data.mean(), start_index, len(data), duration_color, duration_total, amplitude))

    return segments

def plot_histogram(df, column, ax, color):
    df[column].hist(ax=ax, bins=300, color=color, alpha=0.5)
    ax.set_title(f'Distribution of {column}')

def plot_histograms(segments_df, buy_segments_df, sell_segments_df, columns):
    fig, axs = plt.subplots(len(columns), figsize=(14,7*len(columns)))

    for ax, column in zip(axs, columns):
        plot_histogram(segments_df, column, ax, 'blue')
        plot_histogram(buy_segments_df, column, ax, 'green')
        plot_histogram(sell_segments_df, column, ax, 'red')

    plt.tight_layout()
    plt.show()

def plot(data, moving_averages, segments):
    fig, ax = plt.subplots(figsize=(14,7))
    
    colors = ['yellow', 'red', 'cyan', 'blue']
    linewidths = [2, 3, 4, 5]
    titles = ["SMA 10", "SMA 50", "SMA 100", "SMA 200"]

    for (window, ma), color, linewidth, title in zip(moving_averages, colors, linewidths, titles):
        ax.plot(ma, label=title, color=color, linewidth=linewidth)
    
    ax.plot(data['Close'], label='Close Price', color='black')

    # Calculamos las condiciones
    aligned_up, aligned_down, above_all, below_all = calculate_conditions(data, moving_averages)

    # Pintamos de verde el tramo aligned_up and above_all
    buy = aligned_up & above_all
    ax.fill_between(data.index, ax.get_ylim()[0], ax.get_ylim()[1], where=buy, color='red', alpha=0.3)

    # Pintamos de rojo el tramo aligned_down and below_all
    sell = aligned_down & below_all
    ax.fill_between(data.index, ax.get_ylim()[0], ax.get_ylim()[1], where=sell, color='green', alpha=0.3)

    # Dibujamos las líneas horizontales para los precios medios de cada segmento
    for condition, mean_price, start, end, duration_color, duration_total, amplitude in segments:
        if condition == 1:  # Compra
            color = 'red'
        elif condition == -1:  # Venta
            color = 'green'
        else:  # Sin operación
            continue
        ax.hlines(mean_price, data.index[start], data.index[end-1], color=color, linestyle='--')

    ax.legend(loc='best')
    ax.set_title('Moving Averages')

    plt.show()

def calculate_statistics(df, columns):
    statistics = ['mean', 'median', 'std', 'max']
    results = {column: [getattr(df[column], stat)() for stat in statistics] for column in columns}
    
    # Calculamos la moda de manera separada para manejar múltiples modas
    mode_results = {column: [df[column].mode()[0] if len(df[column].mode()) > 0 else None] for column in columns}
    
    # Unimos los resultados en un solo DataFrame
    results_df = pd.DataFrame(results, index=statistics)
    mode_df = pd.DataFrame(mode_results, index=['mode'])
    final_df = pd.concat([results_df, mode_df])
    
    # Reindexamos el DataFrame para cambiar el orden de las filas a 'mean', 'median', 'mode'
    final_df = final_df.reindex(['mean', 'median', 'mode', 'std', 'max'])
    
    return final_df

def calculate_stop_loss(amplitude_df, percentile):
    # Calcula el percentil del DataFrame de amplitud
    stop_loss_percentile = amplitude_df.quantile(percentile)
    print(f"Stop loss based on percentile {percentile}: {stop_loss_percentile}")
    return stop_loss_percentile

def calculate_stop_loss_std(df, column, num_std):
    mean = df[column].mean()
    std = df[column].std()
    stop_loss_std = mean - num_std * std
    print(f"Stop loss based on {num_std} standard deviations below mean of {column}: {stop_loss_std}")
    return stop_loss_std


# Llamamos a las funciones
moving_averages = calculate_moving_averages(data_1m)

aligned_up, aligned_down, above_all, below_all = calculate_conditions(data_1m, moving_averages)
conditions = (aligned_up & above_all).astype(int) - (aligned_down & below_all).astype(int)
segments = calculate_segments_and_means(data_1m['Close'], conditions)

# Convertimos los segmentos a un DataFrame de pandas para facilitar el cálculo de las estadísticas
segments_df = pd.DataFrame(segments, columns=['Condition', 'Mean Price', 'Start', 'End', 'Duration Color', 'Duration Total', 'Amplitude'])


# Definimos las columnas para las que queremos calcular las estadísticas
columns = ['Duration Color', 'Duration Total', 'Amplitude']


# Dividimos los segmentos en compra y venta
buy_segments = [segment for segment in segments if segment[0] == -1]
sell_segments = [segment for segment in segments if segment[0] == 1]

# Convertimos los segmentos a DataFrames de pandas para facilitar el cálculo de las estadísticas
buy_segments_df = pd.DataFrame(buy_segments, columns=['Condition', 'Mean Price', 'Start', 'End', 'Duration Color', 'Duration Total', 'Amplitude'])
sell_segments_df = pd.DataFrame(sell_segments, columns=['Condition', 'Mean Price', 'Start', 'End', 'Duration Color', 'Duration Total', 'Amplitude'])

# Definimos las columnas para las que queremos calcular las estadísticas
columns = ['Duration Color', 'Duration Total', 'Amplitude']

# Calculamos las estadísticas y las imprimimos
results = calculate_statistics(segments_df, columns)
buy_results = calculate_statistics(buy_segments_df, columns)
sell_results = calculate_statistics(sell_segments_df, columns)

print("full statistics:")
print(results)
print("\nBuy segments statistics:")
print(buy_results)
print("\nSell segments statistics:")
print(sell_results)
# Calcula el stop loss basado en el percentil 95 de la amplitud
stop_loss_percentile = calculate_stop_loss(segments_df['Amplitude'], 0.88)
# Calcula el stop loss basado en 2 desviaciones estándar por debajo de la media de la amplitud
stop_loss_std = calculate_stop_loss_std(segments_df, 'Amplitude', 2)


# Llamamos a la función para crear los histogramas
plot_histograms(segments_df, buy_segments_df, sell_segments_df, columns)

plot(data_1m, moving_averages, segments)