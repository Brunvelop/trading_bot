import pandas as pd
import matplotlib.pyplot as plt

data_1m = pd.read_csv('data/BTC_USD_1m.csv', index_col=0, parse_dates=True)
data_1m

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


def plot(data, moving_averages):
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
    ax.fill_between(data.index, ax.get_ylim()[0], ax.get_ylim()[1], where=(aligned_up & above_all), color='red', alpha=0.3)

    # Pintamos de rojo el tramo aligned_down and below_all
    ax.fill_between(data.index, ax.get_ylim()[0], ax.get_ylim()[1], where=(aligned_down & below_all), color='green', alpha=0.3)

    ax.legend(loc='best')
    ax.set_title('Moving Averages')

    plt.show()

# Llamamos a las funciones
moving_averages = calculate_moving_averages(data_1m)
plot(data_1m, moving_averages)