import dash
from dash import dcc, html, Input, Output
import layout_zcyc
import layout_trnscrb
import layout_reader
import layout_news
import callback_zcyc

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    html.Div([
        html.Div([
            html.A("Кривая доходности", href="/zcyc", className="custom-menu-button"),
            html.A("Транскрибация", href="/trnscrb", className="custom-menu-button"),
            html.A("Распознавание", href="/reader", className="custom-menu-button"),
            html.A("Новости", href="/news", className="custom-menu-button"),
        ], className="custom-menu-container")
    ], className="custom-menu-wrapper"),
    
    html.Div(id='page-content', className="custom-page-content"),
    
    html.Script('''
        function setActiveButton() {
            const currentPath = window.location.pathname;
            const buttons = document.querySelectorAll('.custom-menu-button');
            buttons.forEach(button => {
                button.classList.remove('custom-menu-button-active');
                const href = button.getAttribute('href');
                if (href === currentPath || (currentPath === '/' && href === '/zcyc')) {
                    button.classList.add('custom-menu-button-active');
                }
            });
        }
        setTimeout(setActiveButton, 100);
        let lastUrl = window.location.href;
        setInterval(function() {
            if (window.location.href !== lastUrl) {
                lastUrl = window.location.href;
                setTimeout(setActiveButton, 100);
            }
        }, 100);
    ''')
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
        return layout_zcyc.layout()

if __name__ == '__main__':
    app.run(debug=True)