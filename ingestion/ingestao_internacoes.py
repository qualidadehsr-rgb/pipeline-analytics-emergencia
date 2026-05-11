import os
import sys
import polars as pl
import logging
from dotenv import load_dotenv
from google.cloud import bigquery

#carregar variáveis de ambiente
load_dotenv()

#configurar logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
#buscar credencial de acesso
project_id = os.getenv('PROJECT_ID')

#configurar cliente bigquery
cliente = bigquery.Client(project=project_id)

#caminho do arquivo excel
caminho_arquivo = sys.argv[1]

#separa o nome do arquivo do caminho dele
nome_arquivo = os.path.basename(caminho_arquivo)

#separa o nome do arquivo por "_"
periodo = nome_arquivo.split("_")

#limpa o mês
periodo_mes = periodo[2].replace(".xlsx", "")

#unifica o ano ao mês
competencia = "-".join([periodo[1], periodo_mes])

#leitura do arquivo
df = pl.read_excel(caminho_arquivo)
linhas_hsr = len(df)
logging.info(f'{linhas_hsr} linhas carregadas!')

# TRATAMENTO DOS DADOS

#verificar e remover atendimentos duplicados
df = df.unique(subset=["ATENDIMENTO"], keep="first")
linhas_hsr_unicas = len(df)
if linhas_hsr > linhas_hsr_unicas:
    logging.info(f'Removido {linhas_hsr - linhas_hsr_unicas} registros duplicados!\n{linhas_hsr_unicas} linhas restantes.')
else:
    logging.info(f'Não há atendimentos duplicados!')

#lista de colunas sensíveis e "inúteis"
colunas_deletadas = ['PACIENTE', 'CID_INT', 'CD_PRESTADOR','CD_LEITO']

#excluir colunas sensíveis e "inúteis"
df = df.drop(colunas_deletadas)

#converter colunas em strings
df = df.cast(pl.Utf8)

#cria coluna da competência no Dataframe
df = df.with_columns(pl.lit(competencia).alias("competencia"))

# CARGA NO BIGQUERY

#configuração da carga
job_config = bigquery.LoadJobConfig(
    write_disposition = bigquery.WriteDisposition.WRITE_APPEND,
    autodetect=False,
    schema=[bigquery.SchemaField(col, "STRING") for col in df.columns],
)

#tabela_destino
destino = f'{project_id}.raw.internacoes'

#execução da carga
job = cliente.load_table_from_dataframe(df.to_pandas(), destino, job_config=job_config)

#aguardar carga
job.result()
logging.info(f'Carga realizada com sucesso: {job.output_rows} linhas carregadas em {destino}!')


