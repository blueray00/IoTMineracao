import os
import time

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

ORION_URL = os.getenv('ORION_URL', 'http://localhost:1026')
QUANTUMLEAP_URL = os.getenv('QUANTUMLEAP_URL', 'http://localhost:8668')
ZONES = ['ZonaA', 'ZonaB', 'ZonaC', 'ZonaD', 'ZonaE']
LEVEL_COLOR = {
    'baixo': '#4CAF50',
    'moderado': '#FFB300',
    'alto': '#F44336',
    'crítico': '#9C27B0',
}


def fetch_current_zones():
    url = f'{ORION_URL}/v2/entities?type=MineZone&options=keyValues&limit=100'
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_history(entity_id, limit=20):
    url = f'{QUANTUMLEAP_URL}/v2/entities/{entity_id}/attrs/risco_atual?lastN={limit}&options=keyValues'
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return []
    return response.json()


def risk_card(zone, row):
    risk = row.get('risco_atual', 0)
    level = row.get('nivel_risco', 'baixo')
    color = LEVEL_COLOR.get(level, '#4CAF50')

    return st.markdown(
        f"""
        <div style='padding:18px; border-radius:12px; background:#f8f9fa; box-shadow:0 4px 12px rgba(0,0,0,0.05);'>
            <h4 style='margin:0 0 8px 0;'>Zona {zone[-1]}</h4>
            <p style='margin:0;font-size:20px;font-weight:700;color:{color};'>{level.upper()}</p>
            <p style='margin:0.5rem 0 0 0;'>Risco atual: <strong>{risk:.1f}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_dataframe(zones_data):
    rows = []
    for item in zones_data:
        rows.append(
            {
                'id': item.get('id'),
                'temperatura': item.get('temperatura', 0),
                'fumaça': item.get('fumaça', 0),
                'gás': item.get('gás', 0),
                'umidade': item.get('umidade', 0),
                'ventilação': item.get('ventilação', 0),
                'risco_atual': item.get('risco_atual', 0),
                'nivel_risco': item.get('nivel_risco', 'baixo'),
            }
        )
    return pd.DataFrame(rows)


st.set_page_config(page_title='Risco de Incêndio na Mina', layout='wide')
st.title('Dashboard de Detecção de Risco de Incêndio - Mineração')

with st.sidebar:
    st.header('Configuração')
    st.markdown(f'- Orion: `{ORION_URL}`')
    st.markdown(f'- QuantumLeap: `{QUANTUMLEAP_URL}`')
    st.markdown('- Refresh automático a cada 15 segundos')
    st.button('Atualizar agora', on_click=lambda: None)

try:
    zones_data = fetch_current_zones()
    df = build_dataframe(zones_data)
except Exception as exc:
    st.error(f'Erro ao buscar dados do Orion: {exc}')
    df = pd.DataFrame()

if df.empty:
    st.warning('Nenhum dado disponível ainda. Certifique-se de que o publisher e o Node-RED estejam rodando.')
else:
    df = df.sort_values('risco_atual', ascending=False)
    st.subheader('Visão Geral em Tempo Real')

    zone_cols = st.columns(len(df))
    for idx, row in df.iterrows():
        with zone_cols[idx]:
            risk_card(row['id'], row)

    st.markdown('---')
    st.subheader('Métricas mais recentes por zona')
    st.dataframe(df[['id', 'temperatura', 'fumaça', 'gás', 'umidade', 'ventilação', 'risco_atual', 'nivel_risco']].rename(columns={'id': 'Zona'}), use_container_width=True)

    historical_rows = []
    for zone_id in ZONES:
        history = fetch_history(zone_id, limit=15)
        if isinstance(history, dict):
            history = history.get('values', [])
        if not history:
            continue

        for sample in history:
            historical_rows.append(
                {
                    'zona': zone_id,
                    'risco_atual': sample.get('value', 0),
                    'timestamp': sample.get('recvTime', sample.get('datetime', '')),
                }
            )
        time.sleep(0.1)

    if historical_rows:
        hist_df = pd.DataFrame(historical_rows)
        hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
        hist_df = hist_df.sort_values(['zona', 'timestamp'])

        st.subheader('Histórico de risco por zona')
        fig = px.line(hist_df, x='timestamp', y='risco_atual', color='zona', markers=True)
        fig.update_layout(xaxis_title='Data / Hora', yaxis_title='Risco atual', legend_title='Zona')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader('Comparação de risco atual entre zonas')
        fig2 = px.bar(df, x='id', y='risco_atual', color='nivel_risco', color_discrete_map=LEVEL_COLOR)
        fig2.update_layout(xaxis_title='Zona', yaxis_title='Risco atual', showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info('Aguardando histórico no QuantumLeap...')
