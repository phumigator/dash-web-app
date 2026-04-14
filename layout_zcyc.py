from dash import html, dcc, dash_table

COLORS = [
    {'label': '🔴 Красный', 'value': '#FF4136'},
    {'label': '🔵 Синий', 'value': '#0074D9'},
    {'label': '🟢 Зелёный', 'value': '#2ECC40'},
    {'label': '🟠 Оранжевый', 'value': '#FF851B'},
    {'label': '🟣 Фиолетовый', 'value': '#B10DC9'},
    {'label': '🟡 Жёлтый', 'value': '#FFDC00'},
    {'label': '💙 Бирюзовый', 'value': '#7FDBFF'},
    {'label': '💗 Розовый', 'value': '#F012BE'},
    {'label': '⬜ Серый', 'value': '#AAAAAA'},
    {'label': '🟤 Коричневый', 'value': '#8B4513'},
    {'label': '⬛ Тёмно-синий', 'value': '#001F3F'},
    {'label': '🌲 Тёмно-зелёный', 'value': '#006400'},
    {'label': '🟣 Индиго', 'value': '#4B0082'},
    {'label': '⭐ Золотой', 'value': '#FFD700'},
    {'label': '⚪ Серебряный', 'value': '#C0C0C0'},
    {'label': '◽ Белый', 'value': '#FFFFFF'}
]

def layout():
    return html.Div([
        dcc.Store(id='gcurve-params-store'),
        dcc.Store(id='gcurve-dates-store'),
        dcc.Store(id='user-points-store', data=[]),
        dcc.Store(id='issuer-points-store', data=[]),
        dcc.Store(id='visible-points-store', data={'user': [], 'issuer': []}),

        html.Div([
            # Левая панель
            html.Div([
                html.H3("Управление графиком", style={'marginBottom': '20px'}),
                html.Label("Дата кривой:"),
                dcc.Dropdown(id='curve-date-dropdown', placeholder="Выберите дату", style={'marginBottom': '20px'}),
                html.Label("Цвет линии кривой:"),
                dcc.Dropdown(id='line-color', options=COLORS, value=COLORS[0]['value'], clearable=False, style={'marginBottom': '20px'}),
                html.Div([
                    html.Label("Убрать название графика:"),
                    dcc.RadioItems(id='hide-title', options=[{'label': 'Да', 'value': 'hide'}, {'label': 'Нет', 'value': 'show'}], value='show', inline=True, style={'marginBottom': '10px'}),
                    html.Label("Убрать подписи точек:"),
                    dcc.RadioItems(id='hide-labels', options=[{'label': 'Да', 'value': 'hide'}, {'label': 'Нет', 'value': 'show'}], value='show', inline=True, style={'marginBottom': '10px'}),
                    html.Label("Убрать легенду:"),
                    dcc.RadioItems(id='hide-legend', options=[{'label': 'Да', 'value': 'hide'}, {'label': 'Нет', 'value': 'show'}], value='show', inline=True, style={'marginBottom': '20px'}),
                ]),
                html.Label("Срок до погашения (лет):"),
                dcc.RangeSlider(id='maturity-slider', min=0, max=30, step=0.5, value=[0, 5], marks={i: str(i) for i in range(0, 31, 5)}, tooltip={"placement": "bottom", "always_visible": True}),
                html.Label("Доходность (% годовых):", style={'marginTop': '20px'}),
                dcc.RangeSlider(id='yield-slider', min=-10, max=40, step=1, value=[10, 18], marks={i: str(i) for i in range(-10, 41, 10)}, tooltip={"placement": "bottom", "always_visible": True}),
                html.Hr(),
                html.H4("Добавить пользовательскую точку", style={'marginTop': '20px'}),
                html.Label("Цвет точки:"),
                dcc.Dropdown(id='user-point-color', options=COLORS, value=COLORS[0]['value'], clearable=False),
                html.Label("Срок (лет):"),
                dcc.Input(id='user-maturity', type='number', value=1, step=0.5, style={'width': '100%', 'marginBottom': '10px'}),
                html.Label("Доходность (%):"),
                dcc.Input(id='user-yield', type='number', value=10, step=0.5, style={'width': '100%', 'marginBottom': '10px'}),
                html.Button("Добавить точку", id='add-user-point', n_clicks=0, style={'width': '100%', 'marginBottom': '10px'}),
                html.Button("Удалить последнюю точку", id='remove-user-point', n_clicks=0, style={'width': '100%'}),
            ], className="left-panel"),

            # Правая панель
            html.Div([
                dcc.Graph(id='yield-curve-graph', style={'height': '55vh'}),

                html.Div([
                    html.H4("Точки на графике", style={'marginTop': '15px'}),
                    dash_table.DataTable(
                        id='visible-points-table',
                        columns=[
                            {"name": "Тип", "id": "type", "editable": False},
                            {"name": "Название", "id": "name", "editable": True},
                            {"name": "Срок (лет)", "id": "maturity", "editable": False},
                            {"name": "Доходность (%)", "id": "yield", "editable": False},
                        ],
                        data=[],
                        page_size=10,
                        page_action='native',
                        sort_action='native',
                        row_selectable='multi',
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}]
                    ),
                    html.Button("Удалить выбранные точки", id='remove-selected-points', n_clicks=0, style={'marginTop': '10px'})
                ], style={'marginTop': '20px'}),

                html.Div([
                    html.H4("Облигации эмитента", style={'marginTop': '20px'}),
                    html.Div([
                        dcc.Input(id='issuer-inn', type='text', placeholder="Введите ИНН", style={'width': '60%', 'marginRight': '10px'}),
                        html.Button("Загрузить облигации", id='load-issuer-bonds', n_clicks=0),
                    ], style={'marginBottom': '15px'}),
                    dash_table.DataTable(
                        id='issuer-bonds-table',
                        columns=[
                            {"name": "Тикер", "id": "secid"},
                            {"name": "Название", "id": "shortname"},
                            {"name": "Доходность YTM (%)", "id": "ytm"},
                            {"name": "Срок до погашения (лет)", "id": "maturity_years"},
                            {"name": "Номинал", "id": "facevalue"},
                            {"name": "Цена (%)", "id": "price"},
                        ],
                        data=[],
                        page_size=10,
                        page_action='native',
                        sort_action='native',
                        row_selectable='multi',
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'}
                    ),
                    html.Div([
                        html.Button("Добавить выбранные точки", id='add-selected-bonds', n_clicks=0, style={'marginRight': '10px'}),
                        html.Button("Добавить все точки", id='add-all-bonds', n_clicks=0)
                    ], style={'marginTop': '10px'})
                ], style={'marginTop': '20px'})
            ], className="right-panel")
        ], className="flex-container")
    ])