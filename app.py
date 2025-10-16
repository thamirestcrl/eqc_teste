# app.py (VERSÃO FINAL E CORRIGIDA)

import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Análise de Violência de Gênero - PE",
    page_icon="💜",
    layout="wide"
)

# --- CARREGAMENTO E LIMPEZA DOS DADOS ---
@st.cache_data
def carregar_dados():
    caminho_do_ficheiro = "data/MICRODADOS_DE_VIOLÊNCIA_DOMÉSTICA_JAN_2015_A_SET_2025.xlsx"
    
    try:
        df_bruto = pd.read_excel(caminho_do_ficheiro, sheet_name="Plan1")
    except FileNotFoundError:
        st.error(f"ERRO: O ficheiro não foi encontrado no caminho '{caminho_do_ficheiro}'.")
        st.error("Verifique se o ficheiro Excel está dentro de uma pasta chamada 'data' no seu GitHub.")
        return pd.DataFrame()

    df = df_bruto.copy()
    
    novas_colunas = []
    for col in df.columns:
        nome_limpo = str(col).lower().replace(" ", "_")
        nome_limpo = (
            nome_limpo.encode("ascii", "ignore")
            .decode("utf-8", "ignore")
        )
        novas_colunas.append(nome_limpo)
    
    df.columns = novas_colunas

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
    
    # CORREÇÃO: Usar o nome da coluna correto após a limpeza
    if 'regiao_geogrfica' not in df_limpo.columns:
        st.error("A coluna 'regiao_geogrfica' não foi encontrada. Verifique o nome da coluna no ficheiro Excel original.")
        st.write("Colunas encontradas:", df_limpo.columns)
        return pd.DataFrame()

    colunas_necessarias = ["ano", "natureza", "regiao_geogrfica"]
    df_final = df_limpo[colunas_necessarias]
    
    return df_final

df = carregar_dados()

if df.empty:
    st.warning("A aplicação não pode ser carregada porque os dados não foram encontrados ou processados corretamente.")
else:
    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("Filtros de Análise")

    # CORREÇÃO: Usar o nome da coluna correto 'regiao_geogrfica'
    regiao = st.sidebar.selectbox(
        "Filtrar por Região Geográfica:",
        options=["Todas"] + sorted(df["regiao_geogrfica"].unique().tolist()),
        index=0
    )
    
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
        # CORREÇÃO: Usar o nome da coluna correto 'regiao_geogrfica'
        df_filtrado = df[df["regiao_geogrfica"] == regiao]

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
        # CORREÇÃO: Usar o nome da coluna correto 'regiao_geogrfica'
        frequencia_regiao = df['regiao_geogrfica'].value_counts()
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
