from dash import Input, Output, State, callback, ctx
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import uuid
from backend_zcyc import (
    fetch_gcurve_parameters,
    get_curve_params_by_date,
    get_yield_curve,
    fetch_bonds_by_inn
)

# ------------------- Загрузка параметров кривой -------------------
@callback(
    [Output('gcurve-params-store', 'data'),
     Output('gcurve-dates-store', 'data'),
     Output('curve-date-dropdown', 'options'),
     Output('curve-date-dropdown', 'value')],
    Input('url', 'pathname')
)
def load_gcurve_data(_):
    try:
        df_params = fetch_gcurve_parameters()
        params_dict = df_params.to_dict('records')
        dates = df_params['tradedate'].dt.date.unique()
        date_options = [{'label': d.strftime('%Y-%m-%d'), 'value': d.strftime('%Y-%m-%d')} for d in dates]
        default_date = max(dates).strftime('%Y-%m-%d')
        return params_dict, date_options, date_options, default_date
    except Exception as e:
        print(f"Ошибка загрузки кривой: {e}")
        return None, [], [], None

# ------------------- Обновление графика -------------------
@callback(
    Output('yield-curve-graph', 'figure'),
    [Input('gcurve-params-store', 'data'),
     Input('curve-date-dropdown', 'value'),
     Input('line-color', 'value'),
     Input('hide-title', 'value'),
     Input('hide-labels', 'value'),
     Input('hide-legend', 'value'),
     Input('maturity-slider', 'value'),
     Input('yield-slider', 'value'),
     Input('visible-points-store', 'data')]
)
def update_graph(params_data, selected_date, line_color, hide_title, hide_labels,
                 hide_legend, maturity_range, yield_range, visible_points):
    if not params_data or not selected_date:
        return go.Figure()
    df_params = pd.DataFrame(params_data)
    if 'tradedate' in df_params.columns:
        df_params['tradedate'] = pd.to_datetime(df_params['tradedate'])
    try:
        curve_params = get_curve_params_by_date(df_params, selected_date)
    except Exception as e:
        print(f"Ошибка получения параметров для даты {selected_date}: {e}")
        return go.Figure()

    maturities = np.linspace(0.01, 30, 300)
    yields = get_yield_curve(curve_params, maturities)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=maturities,
        y=yields,
        mode='lines',
        name='Кривая доходности',
        line=dict(color=line_color, width=3),
        hovertemplate='Срок: %{x:.2f} лет<br>Доходность: %{y:.2f}%<extra></extra>'
    ))

    # Определяем, показывать ли текстовые метки
    text_position = 'none' if hide_labels == 'hide' else 'top center'

    if visible_points:
        for p in visible_points.get('user', []):
            fig.add_trace(go.Scatter(
                x=[p['maturity']],
                y=[p['yield']],
                mode='markers+text',
                name=p.get('name', 'Пользователь'),
                text=[p.get('name', '')],
                textposition=text_position,
                textfont=dict(size=10),
                marker=dict(color=p.get('color', '#FF851B'), size=10),
                showlegend=(hide_legend != 'hide')
            ))
        for p in visible_points.get('issuer', []):
            fig.add_trace(go.Scatter(
                x=[p['maturity']],
                y=[p['yield']],
                mode='markers+text',
                name=p.get('name', p.get('shortname', 'Эмитент')),
                text=[p.get('name', '')],
                textposition=text_position,
                textfont=dict(size=10),
                marker=dict(color='#2ECC40', size=8, symbol='square'),
                showlegend=(hide_legend != 'hide')
            ))

    fig.update_xaxes(range=maturity_range, title_text="Срок до погашения (лет)")
    fig.update_yaxes(range=yield_range, title_text="Доходность (% годовых)")

    title = "" if hide_title == 'hide' else "Кривая бескупонной доходности (G‑Curve)"
    fig.update_layout(title=title, showlegend=(hide_legend != 'hide'), hovermode='closest')
    return fig

# ------------------- Пользовательские точки с ID -------------------
@callback(
    Output('user-points-store', 'data'),
    Input('add-user-point', 'n_clicks'),
    State('user-points-store', 'data'),
    State('user-maturity', 'value'),
    State('user-yield', 'value'),
    State('user-point-color', 'value'),
    prevent_initial_call=True
)
def add_user_point(n_clicks, existing, maturity, yld, color):
    if not n_clicks or maturity is None or yld is None:
        return existing or []
    new_point = {
        'id': str(uuid.uuid4()),
        'type': 'user',
        'name': f"Пользователь ({maturity} лет)",
        'maturity': float(maturity),
        'yield': float(yld),
        'color': color
    }
    points = existing or []
    points.append(new_point)
    return points

@callback(
    Output('user-points-store', 'data', allow_duplicate=True),
    Input('remove-user-point', 'n_clicks'),
    State('user-points-store', 'data'),
    prevent_initial_call=True
)
def remove_last_user_point(n_clicks, points):
    if n_clicks and points:
        return points[:-1]
    return points or []

# ------------------- Синхронизация visible-points-store с user -------------------
@callback(
    Output('visible-points-store', 'data'),
    Input('user-points-store', 'data'),
    State('visible-points-store', 'data')
)
def sync_user_points(user_points, visible):
    if visible is None:
        visible = {'user': [], 'issuer': []}
    visible['user'] = user_points or []
    return visible

# ------------------- Загрузка облигаций эмитента -------------------
@callback(
    Output('issuer-bonds-table', 'data'),
    Input('load-issuer-bonds', 'n_clicks'),
    State('issuer-inn', 'value'),
    prevent_initial_call=True
)
def load_issuer_bonds(n_clicks, inn):
    if not inn:
        return []
    try:
        df = fetch_bonds_by_inn(inn)
        if df.empty:
            return []
        return df.to_dict('records')
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return []

# ------------------- Добавление точек эмитента с ID -------------------
@callback(
    Output('issuer-points-store', 'data'),
    [Input('add-selected-bonds', 'n_clicks'),
     Input('add-all-bonds', 'n_clicks')],
    [State('issuer-bonds-table', 'data'),
     State('issuer-bonds-table', 'selected_rows'),
     State('issuer-points-store', 'data')],
    prevent_initial_call=True
)
def add_issuer_points(sel_clicks, all_clicks, table_data, selected_rows, existing_points):
    if not table_data:
        return existing_points or []
    triggered = ctx.triggered_id
    points_to_add = []
    if triggered == 'add-all-bonds':
        points_to_add = table_data
    elif triggered == 'add-selected-bonds' and selected_rows:
        points_to_add = [table_data[i] for i in selected_rows]
    if not points_to_add:
        return existing_points or []
    new_points = []
    for row in points_to_add:
        ytm = row.get('ytm', 0)
        if ytm == 0 or ytm is None:
            continue
        new_points.append({
            'id': str(uuid.uuid4()),
            'type': 'issuer',
            'name': row['shortname'],
            'maturity': row.get('maturity_years', 0),
            'yield': ytm,
            'secid': row.get('secid', ''),
            'color': '#2ECC40'
        })
    existing = existing_points or []
    existing.extend(new_points)
    return existing

# ------------------- Синхронизация visible-points-store с issuer -------------------
@callback(
    Output('visible-points-store', 'data', allow_duplicate=True),
    Input('issuer-points-store', 'data'),
    State('visible-points-store', 'data'),
    prevent_initial_call=True
)
def sync_issuer_points(issuer_points, visible):
    if visible is None:
        visible = {'user': [], 'issuer': []}
    visible['issuer'] = issuer_points or []
    return visible

# ------------------- Таблица "Точки на графике" (с ID) -------------------
@callback(
    Output('visible-points-table', 'data'),
    Input('visible-points-store', 'data')
)
def update_visible_table(visible_points):
    if not visible_points:
        return []
    rows = []
    for p in visible_points.get('user', []):
        rows.append({
            'id': p.get('id', ''),
            'type': 'Пользовательская',
            'name': p.get('name', ''),
            'maturity': p.get('maturity', 0),
            'yield': p.get('yield', 0),
        })
    for p in visible_points.get('issuer', []):
        rows.append({
            'id': p.get('id', ''),
            'type': 'Эмитент',
            'name': p.get('name', ''),
            'maturity': p.get('maturity', 0),
            'yield': p.get('yield', 0),
        })
    return rows

# ------------------- Редактирование названия точки (пользовательской и эмитента) -------------------
@callback(
    [Output('user-points-store', 'data', allow_duplicate=True),
     Output('issuer-points-store', 'data', allow_duplicate=True)],
    Input('visible-points-table', 'data_previous'),
    State('visible-points-table', 'data'),
    State('user-points-store', 'data'),
    State('issuer-points-store', 'data'),
    prevent_initial_call=True
)
def edit_point_name(prev_data, current_data, user_pts, issuer_pts):
    if not prev_data or not current_data:
        return (user_pts or []), (issuer_pts or [])
    # Находим изменённую строку
    changed_idx = None
    for i, (prev, curr) in enumerate(zip(prev_data, current_data)):
        if prev != curr:
            changed_idx = i
            break
    if changed_idx is None:
        return (user_pts or []), (issuer_pts or [])
    changed = current_data[changed_idx]
    point_id = changed.get('id')
    new_name = changed.get('name')
    if not point_id or not new_name:
        return (user_pts or []), (issuer_pts or [])
    # Обновляем пользовательские точки
    updated_user = []
    for p in (user_pts or []):
        if p.get('id') == point_id and p.get('type') == 'user':
            p = p.copy()
            p['name'] = new_name
        updated_user.append(p)
    # Обновляем точки эмитента
    updated_issuer = []
    for p in (issuer_pts or []):
        if p.get('id') == point_id and p.get('type') == 'issuer':
            p = p.copy()
            p['name'] = new_name
        updated_issuer.append(p)
    return updated_user, updated_issuer

# ------------------- Удаление выбранных точек по ID -------------------
@callback(
    [Output('user-points-store', 'data', allow_duplicate=True),
     Output('issuer-points-store', 'data', allow_duplicate=True)],
    Input('remove-selected-points', 'n_clicks'),
    State('visible-points-table', 'derived_virtual_selected_rows'),
    State('visible-points-table', 'data'),
    State('user-points-store', 'data'),
    State('issuer-points-store', 'data'),
    prevent_initial_call=True
)
def remove_selected_points(n_clicks, selected_rows, table_data, user_pts, issuer_pts):
    if not n_clicks or not selected_rows:
        return (user_pts or []), (issuer_pts or [])
    
    selected_ids = [table_data[i]['id'] for i in selected_rows if i < len(table_data)]
    
    new_user = [p for p in (user_pts or []) if p.get('id') not in selected_ids]
    new_issuer = [p for p in (issuer_pts or []) if p.get('id') not in selected_ids]
    
    return new_user, new_issuer