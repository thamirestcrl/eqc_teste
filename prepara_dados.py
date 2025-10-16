# preparar_dados.py
# OBJETIVO: Converter o arquivo Excel pesado em um arquivo .parquet leve e rápido
# para ser usado no aplicativo Streamlit. Execute este script apenas uma vez.

import pandas as pd
import os

# --- CONFIGURAÇÃO ---
# Garante que a pasta 'data' exista
if not os.path.exists("data"):
    os.makedirs("data")

# 1. Definir os nomes dos arquivos
arquivo_excel = "data/MICRODADOS_DE_VIOLÊNCIA_DOMÉSTICA_JAN_2015_A_SET_2025.xlsx"
arquivo_otimizado = "data/dados_app.parquet"

# --- EXECUÇÃO ---
try:
    print(f"Lendo o arquivo Excel: '{arquivo_excel}' (isso pode demorar um pouco)...")
    
    # 2. Ler o arquivo Excel e limpar os nomes das colunas (equivalente a janitor::clean_names)
    df = pd.read_excel(arquivo_excel, sheet_name="Plan1")
    df.columns = (
        df.columns.str.lower()
        .str.replace(" ", "_", regex=False)
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .decode("utf-8")
    )

    # 3. Renomear e processar os dados (equivalente a dplyr::mutate)
    if "data_do_fato" in df.columns:
        df.rename(columns={"data_do_fato": "data"}, inplace=True)

    # Converte para data, extrai ano e limpa a coluna 'natureza'
    df["data"] = pd.to_datetime(df["data"], errors='coerce')
    df["ano"] = df["data"].dt.year
    df["natureza"] = df["natureza"].astype(str).str.replace(
        "POR VIOLÊNCIA DOMÉSTICA/FAMILIAR", "", regex=False
    ).str.strip()

    # Filtra linhas com datas ou anos inválidos e anos futuros
    df_limpo = df.dropna(subset=['ano'])
    df_limpo = df_limpo[df_limpo["ano"] < 2025].copy()
    df_limpo['ano'] = df_limpo['ano'].astype(int)

    # 4. Seleciona apenas as colunas necessárias (equivalente a dplyr::select)
    colunas_necessarias = ["ano", "natureza", "regiao_geografica"]
    
    # Verifica se todas as colunas necessárias existem
    colunas_existentes = [col for col in colunas_necessarias if col in df_limpo.columns]
    if len(colunas_existentes) != len(colunas_necessarias):
        print("Aviso: Algumas colunas esperadas não foram encontradas no Excel.")
        print(f"Colunas encontradas: {colunas_existentes}")

    df_final = df_limpo[colunas_existentes]

    # 5. Salvar o arquivo otimizado em formato Parquet
    df_final.to_parquet(arquivo_otimizado)

    print("-" * 50)
    print(f"SUCESSO! Arquivo '{arquivo_otimizado}' foi criado.")
    print("Agora você pode executar o aplicativo com: streamlit run app.py")
    print("-" * 50)

except FileNotFoundError:
    print("-" * 50)
    print(f"ERRO: O arquivo '{arquivo_excel}' não foi encontrado.")
    print("Por favor, certifique-se de que o arquivo Excel está na pasta 'data' antes de executar este script.")
    print("-" * 50)
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
