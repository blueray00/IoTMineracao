import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(
    page_title="Gêmeo Digital da Mina",
    layout="wide"
)

ORION = "http://localhost:1026/v2/entities"

HEADERS = {
    "Fiware-Service": "iotmineracao",
    "Fiware-ServicePath": "/"
}

CORES = {
    "baixo": "#4CAF50",
    "moderado": "#FFC107",
    "alto": "#FF5722",
    "critico": "#9C27B0"
}


def buscar_zona(zona):

    resposta = requests.get(
        f"{ORION}/Zona{zona}",
        headers=HEADERS
    )

    if resposta.ok:
        return resposta.json()

    return None


st.title("Gêmeo Digital da Operação de Mineração")
st.caption("Monitoramento em tempo real das zonas da mina")

st.write(f"**Última atualização:** {time.strftime('%H:%M:%S')}")

zonas = ["A", "B", "C", "D", "E"]

dados = []

for zona in zonas:

    entidade = buscar_zona(zona)

    if entidade:

        dados.append({

            "Zona": zona,
            "Temperatura": entidade["temperatura"]["value"],
            "Fumaça": entidade["fumaca"]["value"],
            "Gás": entidade["gas"]["value"],
            "Umidade": entidade["umidade"]["value"],
            "Ventilação": entidade["ventilacao"]["value"],
            "Risco": entidade["risco_atual"]["value"],
            "Nível": entidade["nivel_risco"]["value"],
            "Timestamp": entidade["timestamp"]["value"]

        })

df = pd.DataFrame(dados)

# ==========================
# CARDS DAS ZONAS
# ==========================

st.subheader("Situação Atual das Zonas")

colunas = st.columns(5)

for i, linha in enumerate(dados):

    cor = CORES.get(linha["Nível"], "#4CAF50")

    with colunas[i]:

        st.markdown(
            f"""
<div style="
background:{cor};
padding:15px;
border-radius:15px;
color:white;
text-align:center;
">

<h3>Zona {linha["Zona"]}</h3>

<h2>{linha["Nível"].upper()}</h2>

<b>Risco:</b> {linha["Risco"]}

</div>
""",
            unsafe_allow_html=True
        )

        st.metric(
            "Temperatura",
            f'{linha["Temperatura"]} °C'
        )

        st.metric(
            "Fumaça",
            linha["Fumaça"]
        )

        st.metric(
            "Gás",
            linha["Gás"]
        )

        st.metric(
            "Umidade",
            f'{linha["Umidade"]}%'
        )

        st.metric(
            "Ventilação",
            linha["Ventilação"]
        )

st.divider()

# ==========================
# TABELA
# ==========================

st.subheader("Estado Atual do Gêmeo Digital")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

st.divider()

# ==========================
# GRÁFICOS
# ==========================

c1, c2 = st.columns(2)

with c1:

    st.subheader("Temperatura por Zona")

    st.bar_chart(
        df.set_index("Zona")["Temperatura"]
    )

with c2:

    st.subheader("Risco Atual")

    st.bar_chart(
        df.set_index("Zona")["Risco"]
    )

st.divider()

# ==========================
# INDICADORES
# ==========================

c1, c2, c3 = st.columns(3)

zona_critica = df.loc[df["Risco"].idxmax()]

c1.metric(
    "Maior risco",
    f'Zona {zona_critica["Zona"]}',
    f'{zona_critica["Risco"]:.1f}'
)

c2.metric(
    "Temperatura média",
    f'{df["Temperatura"].mean():.1f} °C'
)

c3.metric(
    "Risco médio",
    f'{df["Risco"].mean():.1f}'
)

st.divider()

st.subheader("Análise Operacional")

st.info(f"""
**Pergunta respondida pelo painel**

Qual região da mina apresenta maior risco operacional neste momento?

**Resposta atual**

A Zona **{zona_critica["Zona"]}** possui o maior risco da operação, com índice de **{zona_critica["Risco"]:.1f}**, exigindo maior atenção da equipe de monitoramento.
""")

# Atualização automática
time.sleep(4)
st.rerun()