import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
from collections import deque

from exchange_apis import OKXAPI
from strategies import SuperStrategyFutures 

# Configuración inicial
exchange_api = OKXAPI()
bars_memory = deque(maxlen=1000)
strategy = SuperStrategyFutures()

# Inicializar la aplicación Dash
app = dash.Dash(__name__)

# Diseño de la aplicación Dash
app.layout = html.Div([
    dcc.Graph(
        id='live-graph',
        animate=True,
        style={'width': '100%', 'height': '100vh'}  # Establece el ancho al 100% y la altura a 100vh
    ),
    dcc.Interval(
        id='graph-update',
        interval=60*1000,  # en milisegundos
        n_intervals=0
    ),
], style={'width': '100%', 'height': '100%', 'margin': '0px'})  # Establece el ancho y la altura al 100% y elimina los márgenes

@app.callback(Output('live-graph', 'figure'),
              [Input('graph-update', 'n_intervals')])
def update_graph_scatter(n):
    global bars_memory
    bars = exchange_api.get_bars(pair='BTC/USDT', timeframe='1m', limit=300)
    bars = bars[::-1]  # Invierte el orden de los elementos en la lista

    # Actualizar bars_memory
    bars_memory_set = set(tuple(bar) for bar in bars_memory)
    for bar in bars:
        bar_tuple = tuple(bar)
        if bar_tuple not in bars_memory_set:
            bars_memory.append(bar)
            bars_memory_set.add(bar_tuple)

    # Convertir bars_memory en DataFrame para usar con la estrategia
    bars_df = pd.DataFrame(list(bars_memory), columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    bars_df['Time'] = pd.to_datetime(bars_df['Time'], unit='ms', utc=True)
    bars_df['Time'] = bars_df['Time'].dt.tz_convert('Europe/Madrid')

    # Calcular los máximos y mínimos con la estrategia
    max_300, min_300 = strategy.calculate_max_min_300(bars_df)

    # Crear la figura con los máximos y mínimos
    fig = go.Figure(data=[go.Candlestick(x=bars_df['Time'],
                                         open=bars_df['Open'],
                                         high=bars_df['High'],
                                         low=bars_df['Low'],
                                         close=bars_df['Close'])])

    # Agregar líneas horizontales de máximo y mínimo
    fig.add_hline(y=max_300, line=dict(color='Green', width=1, dash='dash'), annotation_text="Max 300")
    fig.add_hline(y=min_300, line=dict(color='Red', width=1, dash='dash'), annotation_text="Min 300")

    # Actualizar los rangos de los ejes para que se ajusten a los nuevos datos
    fig.update_xaxes(range=[bars_df['Time'].iloc[0], bars_df['Time'].iloc[-1] + pd.Timedelta(minutes=15)])
    fig.update_yaxes(range=[min(bars_df['Low']), max(bars_df['High'])])

    fig.update_layout(xaxis_rangeslider_visible=False)

    return fig

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)