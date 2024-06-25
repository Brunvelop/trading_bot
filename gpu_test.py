import pandas as pd
import torch
import numpy as np

from definitions import PlotMode
from plots_utils import draw_graphs


def moving_average(tensor, window):
    n, m = tensor.shape
    weights = torch.ones(1, 1, window, dtype=tensor.dtype) / window
    # Aplicar conv1d a cada fila del tensor
    ma = torch.nn.functional.conv1d(
        tensor.view(n, 1, m), 
        weights, 
        padding=0
    ).squeeze(1)
    # Rellenar los primeros (window-1) elementos con NaN para cada fila
    padding = torch.full((n, window-1), float('nan'), dtype=tensor.dtype)
    return torch.cat([padding, ma], dim=1)


def check_ma_conditions(close_tensor, ma_10, ma_50, ma_100, ma_200):
    # Asegurar que todos los tensores estén en la GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    close_tensor = close_tensor.to(device)
    ma_10 = ma_10.to(device)
    ma_50 = ma_50.to(device)
    ma_100 = ma_100.to(device)
    ma_200 = ma_200.to(device)

    # Comprobar las condiciones
    condition_up = (close_tensor > ma_10) & (ma_10 > ma_50) & (ma_50 > ma_100) & (ma_100 > ma_200)
    condition_down = (close_tensor < ma_10) & (ma_10 < ma_50) & (ma_50 < ma_100) & (ma_100 < ma_200)

    # Crear el tensor de resultados
    result = torch.zeros_like(close_tensor, device=device)
    result[condition_up] = 1
    result[condition_down] = -1

    return result

def calculate_balances(aligned_up, aligned_down, close_tensor, initial_balance_a, ab_ratio):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Mover tensores a GPU si está disponible
    aligned_up = aligned_up.to(device)
    aligned_down = aligned_down.to(device)
    close_tensor = close_tensor.to(device)
    
    # Inicializar balances
    balance_a = torch.full_like(close_tensor, initial_balance_a, device=device)
    balance_b = torch.zeros_like(close_tensor, device=device)
    
    # Calcular cambios en los balances
    sell_amount = torch.where(aligned_up, balance_a / 130, torch.zeros_like(balance_a))
    buy_amount = torch.where(aligned_down, balance_a / 130, torch.zeros_like(balance_a))
    
    # Actualizar balances
    balance_a_change = torch.where(aligned_up, -sell_amount, buy_amount)
    balance_b_change = torch.where(aligned_up, sell_amount * close_tensor, -buy_amount * close_tensor)
    
    balance_a = torch.cumsum(balance_a_change, dim=1) + initial_balance_a
    balance_b = torch.cumsum(balance_b_change, dim=1)
    
    return balance_a, balance_b

ab_ratio = 0.5
initial_balance_a = 889000

# Cargar el archivo CSV usando pandas
df = pd.read_csv('data/old/DOG_USDT_1m.csv')
close_prices = df['Close'].values
close_tensor = torch.tensor([close_prices] * 100, dtype=torch.float32)


# Calcular las medias móviles
ma_10, ma_50, ma_100, ma_200 = torch.stack([moving_average(close_tensor, window) for window in [10, 50, 100, 200]])


aligned_up = (close_tensor > ma_10) & (ma_10 > ma_50) & (ma_50 > ma_100) & (ma_100 > ma_200)
aligned_down = (close_tensor < ma_10) & (ma_10 < ma_50) & (ma_50 < ma_100) & (ma_100 < ma_200)

balance_a, balance_b = calculate_balances(aligned_up, aligned_down, close_tensor, initial_balance_a, ab_ratio)

type_tensor = torch.where(aligned_up, torch.tensor(1), torch.where(aligned_down, torch.tensor(-1), torch.tensor(0)))




datetime_col = pd.date_range(start='1/1/2022', periods=len(close_tensor[0]), freq='T')
visualization_df = pd.DataFrame({
    'Datetime': datetime_col,
    'Close': close_tensor[0].numpy(),
    'pair': 'DOG/USDT',
    'type': np.select([type_tensor[0].cpu().numpy() == 1, type_tensor[0].cpu().numpy() == -1], ['sell_market', 'buy_market'], default=''),
    'price': close_tensor[0].numpy(),
    'amount': '',
    'balance_a': balance_a[0].cpu().numpy(),
    'balance_b': balance_b[0].cpu().numpy()
})
# Crear la lista de extra_plots_price
extra_plots_price = [
    ((datetime_col, ma_10[0].numpy()), {'color': 'blue', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 10', 'type': 'plot'}),
    ((datetime_col, ma_50[0].numpy()), {'color': 'orange', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 50', 'type': 'plot'}),
    ((datetime_col, ma_100[0].numpy()), {'color': 'green', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 100', 'type': 'plot'}),
    ((datetime_col, ma_200[0].numpy()), {'color': 'red', 'linewidth': 2, 'alpha':0.5, 'label': 'MA 200', 'type': 'plot'})
]
plot_modes = [
    PlotMode.PRICE,
    PlotMode.BALANCE_A,
    PlotMode.BALANCE_B
]

draw_graphs(visualization_df, plot_modes, extra_plots_price)