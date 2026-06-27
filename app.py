import streamlit as st
import requests
import pandas as pd

st.title("Monitoramento da Mina")

# Função para buscar entidade no Orion
def get_entity(entity_id):
    url = f"http://localhost:1026/v2/entities/{entity_id}"
    headers = {
        "Fiware-Service": "iotmineracao",
        "Fiware-ServicePath": "/"
    }
    resp = requests.get(url, headers=headers)
    if resp.ok:
        return resp.json()
    return None

# Exemplo: pegar dados da ZonaE
entity = get_entity("ZonaE")

if entity:
    temperatura = entity.get("temperatura", {}).get("value", None)
    risco = entity.get("risco_atual", {}).get("value", None)
    nivel = entity.get("nivel_risco", {}).get("value", None)

    st.metric("Temperatura Atual", f"{temperatura} °C")
    st.metric("Risco Atual", risco)
    st.metric("Nível de Risco", nivel)

    # Gráfico simples
    df = pd.DataFrame({
        "Temperatura": [temperatura],
        "Risco": [risco]
    })
    st.line_chart(df)
else:
    st.warning("Não foi possível obter dados da entidade ZonaE.")
