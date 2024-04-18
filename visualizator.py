import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

class Visualizator:
    def __init__(self, job_function):
        self.job_function = job_function
        self.app = dash.Dash(__name__)
        self.setup_layout()

    def setup_layout(self):
        self.app.layout = html.Div([
            dcc.Graph(
                id='live-graph',
                animate=True,
                style={'width': '100%', 'height': '100vh'}
            ),
            dcc.Interval(
                id='graph-update',
                interval=60*1000,
                n_intervals=0
            ),
        ], style={'width': '100%', 'height': '100%', 'margin': '0px'})

        @self.app.callback(Output('live-graph', 'figure'), [Input('graph-update', 'n_intervals')])
        def update_graph_scatter(n):
            return self.update_graph()

    def update_graph(self):
        bars_df, max_300, min_300 = self.job_function()
        # Crear la figura con los máximos y mínimos
        fig = go.Figure(data=[go.Candlestick(x=bars_df['Time'],
                                            open=bars_df['Open'],
                                            high=bars_df['High'],
                                            low=bars_df['Low'],
                                            close=bars_df['Close'])])

        # Agregar líneas horizontales de máximo y mínimo
        fig.add_hline(y=max_300, line=dict(color='Green', width=1, dash='dash'), annotation_text="Max 300")
        fig.add_hline(y=min_300, line=dict(color='Red', width=1, dash='dash'), annotation_text="Min 300")

        last_cross = None
        for i in range(len(bars_df) - 1, -1, -1):  # Iterar hacia atrás
            if bars_df['Close'].iloc[i] > max_300:
                last_cross = ('above', i)
                break
            elif bars_df['Close'].iloc[i] < min_300:
                last_cross = ('below', i)
                break

        # Agregar un triángulo como señal visual para el último cruce
        if last_cross is not None:
            cross_type, cross_index = last_cross
            cross_row = bars_df.iloc[cross_index]
            if cross_type == 'above':
                fig.add_annotation(x=cross_row['Time'], y=cross_row['Low'],
                                text='▲',  # Triángulo apuntando hacia arriba
                                showarrow=False,
                                yshift=-10,  # Desplazamiento para posicionar correctamente el triángulo
                                font=dict(color='Green'))
            elif cross_type == 'below':
                fig.add_annotation(x=cross_row['Time'], y=cross_row['High'],
                                text='▼',  # Triángulo apuntando hacia abajo
                                showarrow=False,
                                yshift=10,  # Desplazamiento para posicionar correctamente el triángulo
                                font=dict(color='Red'))


        # Actualizar los rangos de los ejes para que se ajusten a los nuevos datos
        fig.update_xaxes(range=[bars_df['Time'].iloc[0], bars_df['Time'].iloc[-1] + pd.Timedelta(minutes=15)])
        fig.update_yaxes(range=[min(bars_df['Low'])*0.999, max(bars_df['High'])*1.001])

        fig.update_layout(xaxis_rangeslider_visible=False)
        return fig

    def run(self):
        self.app.run_server(debug=True)