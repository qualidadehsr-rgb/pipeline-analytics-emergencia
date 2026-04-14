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
caminho = sys.argv[1]

#leitura do arquivo
df = pl.read_csv(caminho, skip_rows=0, has_header=False, encoding="latin1", infer_schema_length=0, truncate_ragged_lines=True, separator=',')

#renomeando as colunas necessárias
df = df.rename({'column_2': 'Atendimento', 'column_4': 'Paciente', 'column_8': 'Hora', 'column_9': 'Tipo',
                'column_11': 'Origem', 'column_13': 'Destino', 'column_14': 'Tip_Acom', 'column_15': 'Cid',
                'column_16': 'Convenio', 'column_17': 'Motivo_alta'})

#removendo "lixo"
df = df.filter(pl.col('Atendimento').str.contains(r"^\d+$"))

logging.info(f'Carregado {len(df)} linhas!')
print(df.head(5))

#converter colunas em strings
df = df.cast(pl.Utf8)

#========================================
# Carga no BigQuery
#========================================

#configuração da carga
job_config = bigquery.LoadJobConfig(
    write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE,
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


