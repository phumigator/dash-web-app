import dash
from dash import dcc, html, Input, Output
import layout_zcyc
import layout_trnscrb
import layout_reader
import layout_news

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # для gunicorn

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Верхнее меню с минимальной высотой
    html.Div([
        html.Div([
            dcc.Link("Кривая доходности", href="/zcyc", className="menu-button"),
            dcc.Link("Транскрибация", href="/trnscrb", className="menu-button"),
            dcc.Link("Распознавание", href="/reader", className="menu-button"),
            dcc.Link("Новости", href="/news", className="menu-button"),
        ], style={
            'display': 'flex',
            'gap': '20px',
            'padding': '10px 20px',
            'fontFamily': 'Franklin Gothic Book',
            'fontSize': '14pt',
            'background': '#f0f0f0',
            'borderBottom': '1px solid #ccc'
        })
    ], style={'minHeight': 'min-content'}),
    # Область для отображения выбранной страницы
    html.Div(id='page-content', style={'padding': '20px'})
])

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/zcyc':
        return layout_zcyc.layout()
    elif pathname == '/trnscrb':
        return layout_trnscrb.layout()
    elif pathname == '/reader':
        return layout_reader.layout()
    elif pathname == '/news':
        return layout_news.layout()
    else:
        # По умолчанию (включая '/') показываем страницу "Кривая доходности"
        return layout_zcyc.layout()

if __name__ == '__main__':
    app.run(debug=True)