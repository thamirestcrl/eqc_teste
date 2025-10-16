# app.py (VERSÃO SIMPLIFICADA)

import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA E CARREGAMENTO DE DADOS ---

st.set_page_config(
    page_title="Análise de Violência de Gênero - PE",
    page_icon="💜",
    layout="wide"
)

# Usar cache para carregar os dados apenas uma vez, melhorando a performance
@st.cache_data
def carregar_dados():
    # ALTERAÇÃO IMPORTANTE: Ler o ficheiro Excel diretamente
    # Certifique-se de que o nome do ficheiro corresponde EXATAMENTE ao seu.
    nome_do_ficheiro_excel = "MICRODADOS_DE_VIOLÊNCIA_DOMÉSTICA_JAN_2015_A_SET_2025.xlsx"
    
    df_bruto = pd.read_excel(nome_do_ficheiro_excel, sheet_name="Plan1")
    
    # --- Limpeza de dados (anteriormente em preparar_dados.py) ---
    df = df_bruto.copy()
    df.columns = (
        df.columns.str.lower()
        .str.replace(" ", "_", regex=False)
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .decode("utf-8")
    )

    if "data_do_fato" in df.columns:
        df.rename(columns={"data_do_fato": "data"}, inplace=True)

    df["data"] = pd.to_datetime(df["data"], errors='coerce')
    df["ano"] = df["data"].dt.year
    df["natureza"] = df["natureza"].astype(str).str.replace(
        "POR VIOLÊNCIA DOMÉSTICA/FAMILIAR", "", regex=False
    ).str.strip()

    df_limpo = df.dropna(subset=['ano'])
    df_limpo = df_limpo[df_limpo["ano"] < 2025].copy()
    df_limpo['ano'] = df_limpo['ano'].astype(int)

    colunas_necessarias = ["ano", "natureza", "regiao_geografica"]
    df_final = df_limpo[colunas_necessarias]
    
    return df_final

df = carregar_dados()

# --- BARRA LATERAL (SIDEBAR) ---
# (O resto do código permanece exatamente o mesmo)

st.sidebar.header("Filtros de Análise")

regiao = st.sidebar.selectbox(
    "Filtrar por Região Geográfica:",
    options=["Todas"] + sorted(df["regiao_geografica"].unique().tolist()),
    index=0
)

# Corrigir a procura por "AMEACA" que pode não existir após a limpeza
lista_natureza = sorted(df["natureza"].unique().tolist())
index_ameaca = lista_natureza.index("AMEACA") if "AMEACA" in lista_natureza else 0

natureza_evolucao = st.sidebar.selectbox(
    "Natureza para Evolução Anual (Linha):",
    options=lista_natureza,
    index=index_ameaca
)

st.sidebar.markdown("---")
st.sidebar.info("Análise de Dados de Violência Doméstica da SDS-PE (2015-2024).")

# --- FILTRAGEM DOS DADOS ---
if regiao == "Todas":
    df_filtrado = df.copy()
else:
    df_filtrado = df[df["regiao_geografica"] == regiao]

# --- PAINEL PRINCIPAL ---
st.markdown("<h1 style='color: #864ce2;'>ANÁLISE DE DADOS DE VIOLÊNCIA DE GÊNERO EM PERNAMBUCO (EQC)</h1>", unsafe_allow_html=True)

# --- ABAS (TABS) ---
tab1, tab2, tab3 = st.tabs([
    "Resumo & Top Crimes", 
    "Evolução Anual", 
    "Frequência Regional"
])

# --- ABA 1: RESUMO & TOP CRIMES ---
with tab1:
    st.subheader("Top 20 Frequência de Crimes por Natureza")
    top_20_natureza = df_filtrado['natureza'].value_counts().nlargest(20)
    fig1 = px.bar(
        top_20_natureza, 
        x=top_20_natureza.values, 
        y=top_20_natureza.index, 
        orientation='h', 
        labels={'x':'Número de Ocorrências', 'y':'Natureza do Crime'},
        text_auto=True
    )
    fig1.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    fig1.update_traces(marker_color='#864ce2')
    st.plotly_chart(fig1, use_container_width=True)
    
    st.subheader("Top 10 Média Anual de Ocorrências")
    if df_filtrado['ano'].nunique() > 0:
        media_anual = df_filtrado.groupby('natureza')['ano'].count() / df_filtrado['ano'].nunique()
        top_10_media = media_anual.nlargest(10)
        fig2 = px.bar(
            top_10_media, 
            x=top_10_media.values, 
            y=top_10_media.index, 
            orientation='h', 
            labels={'x':'Média de Ocorrências por Ano', 'y':'Natureza do Delito'},
            title="Média Anual de Ocorrências por Tipo de Delito (Top 10)",
            text_auto='.2f'
        )
        fig2.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        fig2.update_traces(marker_color='#ffaad0')
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Tabela Resumo (Top 10 com Estimativa de Subnotificação)")
    tabela_resumo = df_filtrado['natureza'].value_counts().nlargest(10).reset_index()
    tabela_resumo.columns = ["Natureza do Crime", "Casos Registrados"]
    tabela_resumo["Subnotificação (Estimada)"] = round((tabela_resumo["Casos Registrados"] / 0.4) - tabela_resumo["Casos Registrados"])
    st.dataframe(tabela_resumo, use_container_width=True, hide_index=True)

# --- ABA 2: EVOLUÇÃO ANUAL ---
with tab2:
    st.subheader(f'Frequência Anual de "{natureza_evolucao}" (Até 2024)')
    evolucao_selecionada = df_filtrado[df_filtrado['natureza'] == natureza_evolucao].groupby('ano').size().reset_index(name='contagem')
    fig3 = px.line(
        evolucao_selecionada, 
        x='ano', 
        y='contagem',
        labels={'ano': 'Ano', 'contagem': 'Número de Ocorrências'},
        markers=True
    )
    fig3.update_traces(line=dict(color="#cd97f8", width=3))
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Evolução Anual dos 10 Principais Tipos de Crime")
    top_10_geral = df_filtrado['natureza'].value_counts().nlargest(10).index
    df_top_10_evolucao = df_filtrado[df_filtrado['natureza'].isin(top_10_geral)]
    evolucao_todos = df_top_10_evolucao.groupby(['ano', 'natureza']).size().reset_index(name='contagem')
    fig4 = px.line(
        evolucao_todos, 
        x='ano', 
        y='contagem', 
        color='natureza',
        labels={'ano': 'Ano', 'contagem': 'Número de Ocorrências', 'natureza': 'Natureza do Crime'},
        title='Evolução Anual dos 10 Principais Tipos de Crime (Até 2024)'
    )
    st.plotly_chart(fig4, use_container_width=True)

# --- ABA 3: FREQUÊNCIA REGIONAL ---
with tab3:
    st.subheader("Frequência de Crimes por Região Geográfica")
    frequencia_regiao = df['regiao_geografica'].value_counts()
    fig5 = px.bar(
        frequencia_regiao, 
        x=frequencia_regiao.values, 
        y=frequencia_regiao.index, 
        orientation='h',
        labels={'x':'Número de Ocorrências', 'y':'Região Geográfica'},
        title='Frequência de Crimes por Região Geográfica em PE (2015-2024)',
        text_auto=True
    )
    fig5.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    fig5.update_traces(marker_color='#007bff')
    st.plotly_chart(fig5, use_container_width=True)
