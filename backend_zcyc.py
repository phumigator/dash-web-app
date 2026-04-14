import requests
import pandas as pd
import numpy as np
from datetime import datetime

# -------------------------------------------------------------------
# 1. Получение параметров G‑Curve и доступных дат
# -------------------------------------------------------------------
def fetch_gcurve_parameters():
    url = "https://iss.moex.com/iss/engines/stock/zcyc/securities.json"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        raise ConnectionError(f"Ошибка загрузки параметров G‑Curve: {e}")

    columns = data['params']['columns']
    rows = data['params']['data']
    df = pd.DataFrame(rows, columns=columns)
    df['tradedate'] = pd.to_datetime(df['tradedate'])
    for col in ['B1','B2','B3','T1','G1','G2','G3','G4','G5','G6','G7','G8','G9']:
        df[col] = pd.to_numeric(df[col])
    return df

def get_curve_params_by_date(df, target_date):
    # Приводим колонку к datetime, если ещё не
    if not pd.api.types.is_datetime64_any_dtype(df['tradedate']):
        df['tradedate'] = pd.to_datetime(df['tradedate'])
    target = pd.to_datetime(target_date)
    exact = df[df['tradedate'] == target]
    if not exact.empty:
        row = exact.iloc[0]
    else:
        prev = df[df['tradedate'] <= target]
        if prev.empty:
            raise ValueError(f"Нет данных кривой для даты {target_date}")
        row = prev.iloc[-1]
    params = {
        'tradedate': row['tradedate'],
        'beta0': float(row['B1']),
        'beta1': float(row['B2']),
        'beta2': float(row['B3']),
        'tau': float(row['T1']),
        'g': [float(row[f'G{i}']) for i in range(1,10)]
    }
    return params

# -------------------------------------------------------------------
# 2. Расчёт доходности по формуле G‑Curve
# -------------------------------------------------------------------
def GT(t, beta0, beta1, beta2, tau, g_values):
    term1 = beta0 + beta1 * tau * (1 - np.exp(-t / tau)) / t
    term2 = beta2 * ((1 - np.exp(-t / tau)) * tau / t - np.exp(-t / tau))
    
    a = np.zeros(9)
    b = np.zeros(9)
    a[0] = 0
    a[1] = 0.6
    b[0] = a[1]
    k = 1.6
    for i in range(2, 9):
        a[i] = a[i-1] + k**(i-1)
        b[i-1] = b[i-2] * k
    term3 = 0.0
    for i in range(9):
        if b[i] != 0:
            term3 += g_values[i] * np.exp(-((t - a[i])**2) / (b[i]**2))
    GT_val = term1 + term2 + term3
    return GT_val / 10000

def KBD(t, beta0, beta1, beta2, tau, g_values):
    gt = GT(t, beta0, beta1, beta2, tau, g_values)
    return 100 * (np.exp(gt) - 1)

def get_yield_curve(params, maturities):
    beta0 = params['beta0']
    beta1 = params['beta1']
    beta2 = params['beta2']
    tau = params['tau']
    g = params['g']
    yields = [KBD(t, beta0, beta1, beta2, tau, g) for t in maturities]
    return yields

# -------------------------------------------------------------------
# 3. Получение облигаций эмитента по ИНН
# -------------------------------------------------------------------
def fetch_bonds_by_inn(inn):
    url_issuer = f"https://iss.moex.com/iss/securities.json?q={inn}&type=issuer"
    try:
        r = requests.get(url_issuer, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        raise ValueError(f"Ошибка поиска эмитента с ИНН {inn}: {e}")

    if not data.get('securities', {}).get('data'):
        raise ValueError(f"Эмитент с ИНН {inn} не найден")
    issuer_id = data['securities']['data'][0][0]

    url_bonds = f"https://iss.moex.com/iss/securities.json?issuer_id={issuer_id}&type=bond"
    try:
        r = requests.get(url_bonds, timeout=30)
        r.raise_for_status()
        bonds_data = r.json()
    except Exception as e:
        raise ValueError(f"Ошибка загрузки облигаций: {e}")

    bonds = []
    today = datetime.now().date()
    for bond in bonds_data.get('securities', {}).get('data', []):
        secid = bond[0]
        shortname = bond[2]
        try:
            detail_url = f"https://iss.moex.com/iss/securities/{secid}.json"
            rd = requests.get(detail_url, timeout=30)
            rd.raise_for_status()
            detail = rd.json()
            sec_cols = detail['securities']['columns']
            sec_row = detail['securities']['data'][0]
            sec_dict = dict(zip(sec_cols, sec_row))
            maturity_date = sec_dict.get('MATDATE', None)
            facevalue = float(sec_dict.get('FACEVALUE', 0))
            coupon = float(sec_dict.get('COUPONPERCENT', 0))

            ytm = 0.0
            price = 0.0
            if 'marketdata' in detail and detail['marketdata']['data']:
                md_cols = detail['marketdata']['columns']
                md_row = detail['marketdata']['data'][0]
                md_dict = dict(zip(md_cols, md_row))
                ytm = float(md_dict.get('YIELD', 0.0))
                price = float(md_dict.get('LAST', 0.0))

            if maturity_date:
                mat_date = pd.to_datetime(maturity_date).date()
                days = (mat_date - today).days
                maturity_years = max(0, round(days / 365.25, 2))
            else:
                maturity_years = 0.0
        except Exception:
            continue

        bonds.append({
            'secid': secid,
            'shortname': shortname,
            'ytm': ytm,
            'maturity_years': maturity_years,
            'facevalue': facevalue,
            'price': price,
            'coupon': coupon,
            'maturity_date': maturity_date
        })
    return pd.DataFrame(bonds)