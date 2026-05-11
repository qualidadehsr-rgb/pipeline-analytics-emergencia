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
#buscar credenciais
project_id = os.getenv('PROJECT_ID')

#configurar cliente
cliente = bigquery.Client(project=project_id)

#caminho do arquivo
caminho_arquivo = sys.argv[1]

#separa o nome do arquivo do caminho dele
nome_arquivo = os.path.basename(caminho_arquivo)

#separa o nome do arquivo por "_"
periodo = nome_arquivo.split("_")

#limpa o mês
periodo_mes = periodo[2].replace(".csv", "")

#unifica o ano ao mês
competencia = "-".join([periodo[1], periodo_mes])

#leitura do arquivo
df = pl.read_csv(caminho_arquivo, skip_rows=0, has_header=True, encoding="latin1", infer_schema_length=0, truncate_ragged_lines=True, separator=';')
print(f"Colunas encontradas: {df.columns}")
#renomeando as colunas necessárias
df = df.rename({
    'Atend.': 'Atendimento',
    'Tip. Acom': 'Tip_Acom',
    'CID ': 'CID',
    'Convênio': 'Convenio',
    'Motivo Alta': 'Motivo_Alta'
})

#removendo "lixo"
df = df.filter(pl.col('Atendimento').str.contains(r"^\d+$"))

logging.info(f'Carregado {len(df)} linhas!')
print(df.head(5))

#converter colunas em strings
df = df.cast(pl.Utf8)

#cria coluna da competência no Dataframe
df = df.with_columns(pl.lit(competencia).alias("competencia"))

#========================================
# Carga no BigQuery
#========================================

#configuração da carga
job_config = bigquery.LoadJobConfig(
    write_disposition = bigquery.WriteDisposition.WRITE_APPEND,
    autodetect=False,
    schema=[bigquery.SchemaField(col, "STRING") for col in df.columns]
)

#tabela_destino
destino = f'{project_id}.raw.movimentacoes'

#execução da carga
job = cliente.load_table_from_dataframe(df.to_pandas(), destino, job_config=job_config)
logging.info('Enviando dados ao BigQuery...')

#aguardar carga
job.result()
logging.info(f'Carga realizada com sucesso: {job.output_rows} linhas carregadas em {destino}!')


