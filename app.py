import os, io
import pandas as pd, numpy as np, plotly.express as px
from datetime import datetime, timedelta
from flask import Flask, send_file, request
import dash, dash_core_components as dcc, dash_html_components as html
from dash.dependencies import Input, Output

# ── Flask + Dash setup ──
server = Flask(__name__)
app = dash.Dash(__name__, server=server, url_base_pathname='/')

# ── Data generator (remplace par tes vraies sources) ──
def get_data(symbol, start, end):
    dates = pd.date_range(start, end, freq='H')
    vals = np.sin(np.linspace(0, 10, len(dates))) + np.random.randn(len(dates))*0.1
    return pd.DataFrame({'Date': dates, 'Valeur': vals})

# ── Dash layout ──
app.layout = html.Div(style={'background':'transparent','color':'white','textAlign':'center'}, children=[
    html.H2("Cycle Financier interactif"),
    dcc.Input(id='symbol', type='text', value='ES', placeholder='Symbole (ES, NQ...)'),
    dcc.DatePickerRange(
        id='daterange',
        start_date=(datetime.utcnow()-timedelta(days=7)).date(),
        end_date=datetime.utcnow().date()
    ),
    dcc.RadioItems(id='mode', options=[
        {'label':'Courbe','value':'line'},
        {'label':'Volatilité','value':'vol'},
        {'label':'Heatmap Risque','value':'risk'}
    ], value='line', inline=True),
    html.Button('Actualiser', id='go'),
    dcc.Graph(id='graph')
])

# ── Callback interactif ──
@app.callback(
    Output('graph','figure'),
    [Input('go','n_clicks')],
    [dash.dependencies.State('symbol','value'),
     dash.dependencies.State('daterange','start_date'),
     dash.dependencies.State('daterange','end_date'),
     dash.dependencies.State('mode','value')]
)
def update_graph(n, symbol, start, end, mode):
    df = get_data(symbol, start, end)
    if mode == 'line':
        fig = px.line(df, x='Date', y='Valeur', title=f'Cycle {symbol}')
    elif mode == 'vol':
        # calcule volatilité rolling
        df['Vol'] = df['Valeur'].rolling(24).std()
        fig = px.line(df, x='Date', y='Vol', title=f'Volatilité {symbol}')
    else:  # risk heatmap
        # bin et heatmap
        df['Risk'] = np.abs(df['Valeur'])
        fig = px.density_heatmap(df, x='Date', y='Valeur', z='Risk',
                                 title=f'Risque {symbol}')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

# ── Endpoint PNG (à la volée) ──
@server.route('/api/png')
def get_png():
    symbol = request.args.get('symbol','ES').upper()
    start = request.args.get('start')
    end   = request.args.get('end')
    mode  = request.args.get('mode','line')
    df = get_data(symbol, start, end)
    # crée figure Plotly
    fig = update_graph(None, symbol, start, end, mode)
    img_bytes = fig.to_image(format='png', width=800, height=400, scale=2)
    return send_file(io.BytesIO(img_bytes),
                     attachment_filename=f"{symbol}.png",
                     mimetype='image/png')

if __name__ == '__main__':
    # sur Render, port auto
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
