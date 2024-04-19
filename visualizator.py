import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        bars_df, indicators = self.job_function()
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.02, subplot_titles=('Candlestick', 'Indicators'), 
                            row_heights=[0.7, 0.3])

        # Agregar el gráfico de velas al primer subplot
        fig.add_trace(go.Candlestick(x=bars_df['Time'],
                                    open=bars_df['Open'],
                                    high=bars_df['High'],
                                    low=bars_df['Low'],
                                    close=bars_df['Close']), row=1, col=1)

        # Agregar líneas horizontales de máximo y mínimo al gráfico de velas
        fig.add_hline(y=indicators.get('max_300'), line=dict(color='Green', width=1, dash='dash'), 
                    annotation_text="Max 300", row=1, col=1)
        fig.add_hline(y=indicators.get('min_300'), line=dict(color='Red', width=1, dash='dash'), 
                    annotation_text="Min 300", row=1, col=1)
        fig.add_trace(go.Scatter(x=bars_df['Time'], y=indicators.get('ma_200'), 
                    mode='lines', name='MA 200'), row=1, col=1)

        # Agregar el gráfico de indicadores al segundo subplot
        fig.add_trace(go.Scatter(x=bars_df['Time'], y=indicators['volatility'], 
                                mode='lines', name='Volatility'), row=2, col=1)
        fig.add_trace(go.Scatter(x=bars_df['Time'], y=indicators['avg_vol_10'], 
                                mode='lines', name='Avg Vol 10'), row=2, col=1)
        fig.add_trace(go.Scatter(x=bars_df['Time'], y=indicators['avg_vol_50'], 
                                mode='lines', name='Avg Vol 50'), row=2, col=1)
        fig.add_trace(go.Scatter(x=bars_df['Time'], y=indicators['avg_vol_100'], 
                                mode='lines', name='Avg Vol 100'), row=2, col=1)
        fig.add_trace(go.Scatter(x=bars_df['Time'], y=indicators['avg_vol_200'], 
                                mode='lines', name='Avg Vol 200'), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=bars_df['Time'],
            y=indicators['volatility_up'].astype(int),
            mode='markers',
            marker=dict(color='Orange', size=10),
            name='Volatility Up'
        ), row=2, col=1)

        # Asegúrate de actualizar los rangos de ejes para ambos subplots si es necesario
        fig.update_xaxes(range=[bars_df['Time'].iloc[0], bars_df['Time'].iloc[-1] + pd.Timedelta(minutes=15)], row=1, col=1)
        fig.update_xaxes(range=[bars_df['Time'].iloc[0], bars_df['Time'].iloc[-1] + pd.Timedelta(minutes=15)], row=2, col=1)

        fig.update_yaxes(range=[min(bars_df['Low'])*0.999, max(bars_df['High'])*1.001], row=1, col=1)
        # Actualizar el rango del eje y para el subplot de indicadores si es necesario
        # fig.update_yaxes(range=[min_value, max_value], row=2, col=1)

        fig.update_layout(xaxis_rangeslider_visible=False)
        return fig

    def run(self):
        self.app.run_server(debug=True)