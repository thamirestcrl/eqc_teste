# preparar_dados.py
# OBJETIVO: Converter o arquivo Excel pesado em um arquivo .parquet leve e rápido
# para ser usado no aplicativo Streamlit. Execute este script apenas uma vez.

import pandas as pd
import os

# --- CONFIGURAÇÃO ---
# Garante que a pasta 'data' exista para evitar erros.
if not os.path.exists("data"):
    os.makedirs("data")

# 1. Definir os nomes e caminhos dos arquivos.
# O script espera que o Excel esteja DENTRO da pasta 'data'.
arquivo_excel = "data/MICRODADOS_DE_VIOLÊNCIA_DOMÉSTICA_JAN_2015_A_SET_2025.xlsx"

# O arquivo otimizado será salvo na pasta principal (raiz) do projeto.
arquivo_otimizado = "dados_app.parquet"


# --- EXECUÇÃO ---
try:
    print("-" * 50)
    print(f"Iniciando o processamento do arquivo: '{arquivo_excel}'")
    print("Isso pode demorar um pouco dependendo do tamanho do arquivo...")

    # 2. Ler o arquivo Excel e limpar os nomes das colunas.
    # Esta é a etapa que mais consome memória.
    df = pd.read_excel(arquivo_excel, sheet_name="Plan1")
    
    # Limpa os nomes das colunas (ex: "Data do Fato" -> "data_do_fato")
    df.columns = (
        df.columns.str.lower()
        .str.replace(" ", "_", regex=False)
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .decode("utf-8")
    )

    print("Arquivo Excel lido. Iniciando a limpeza dos dados...")

    # 3. Renomear e processar os dados.
    if "data_do_fato" in df.columns:
        df.rename(columns={"data_do_fato": "data"}, inplace=True)

    # Converte a coluna 'data' para o formato de data, extrai o ano, e limpa 'natureza'.
    df["data"] = pd.to_datetime(df["data"], errors='coerce')
    df["ano"] = df["data"].dt.year
    df["natureza"] = df["natureza"].astype(str).str.replace(
        "POR VIOLÊNCIA DOMÉSTICA/FAMILIAR", "", regex=False
    ).str.strip()

    # Remove linhas onde a data não pôde ser convertida (resultando em NaT/NaN no ano)
    df_limpo = df.dropna(subset=['ano'])
    df_limpo = df_limpo[df_limpo["ano"] < 2025].copy()
    df_limpo['ano'] = df_limpo['ano'].astype(int)

    # 4. Seleciona APENAS as colunas que o aplicativo realmente usa.
    # Esta é a etapa mais importante para reduzir o tamanho do arquivo final.
    colunas_necessarias = ["ano", "natureza", "regiao_geografica"]
    df_final = df_limpo[colunas_necessarias]

    print("Limpeza concluída. Salvando o arquivo otimizado...")

    # 5. Salvar o arquivo otimizado em formato Parquet.
    df_final.to_parquet(arquivo_otimizado)

    print("-" * 50)
    print(f"✅ SUCESSO! O arquivo '{arquivo_otimizado}' foi criado.")
    print("Ele está pronto para ser enviado ao GitHub junto com app.py e requirements.txt.")
    print("-" * 50)

except FileNotFoundError:
    print("-" * 50)
    print(f"❌ ERRO: O arquivo Excel não foi encontrado no caminho esperado:")
    print(f"'{arquivo_excel}'")
    print("\nPor favor, certifique-se de que:")
    print("1. Você criou uma pasta chamada 'data'.")
    print("2. O arquivo Excel está DENTRO dessa pasta 'data'.")
    print("-" * 50)

except Exception as e:
    print(f"❌ Ocorreu um erro inesperado durante o processamento: {e}")
