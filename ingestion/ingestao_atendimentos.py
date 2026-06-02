import os
import sys
import polars as pl
import logging
from dotenv import load_dotenv
from google.cloud import bigquery

#carregar variáveis de ambiente
load_dotenv()

#configuração logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

#buscar credencial de acesso
project_id = os.getenv("PROJECT_ID")

#cliente BigQuery
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

#leitura do arquivo excel
df = pl.read_excel(caminho_arquivo)

#========================================
# TRATAMENTO DOS DADOS
#========================================

#filtrar empresa
df = df.filter(pl.col("EMPRESA") == "HSR")
linhas_hsr = len(df)
logging.info(f'Selecionado HSR: {linhas_hsr} linhas.')

#remover atendimentos duplicados
df = df.unique(subset=["CD_ATENDIMENTO"], keep="first")
linhas_hsr_unicas = len(df)
logging.info(f'Removido {linhas_hsr - linhas_hsr_unicas} registros duplicados!\n{linhas_hsr_unicas} linhas restantes.')

#lista de colunas sensíveis
colunas_sensiveis = ['NM_PACIENTE', 'DT_NASC', 'ENDERECO',
                     'USUARIO_CLASSIF', 'USUARIO_CAD_RECEPCAO',
                     'USUARIO_ALTA', 'TOTAL_CONTA', 'CONTA',
                     'CONTA_FECHADA', 'REGISTRO_ANS']

#excluir colunas sensíveis
df = df.drop(colunas_sensiveis)

#converter colunas em string
df = df.cast(pl.Utf8)

#cria coluna da competência no Dataframe
df = df.with_columns(pl.lit(competencia).alias("competencia"))

#========================================
# Carga no BigQuery
#========================================

#configuração da carga
job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    autodetect=False,
    schema=[bigquery.SchemaField(col, "STRING") for col in df.columns]
)

#tabela de destino
destino = f'{project_id}.raw.atendimentos'

#deleta tabela se já existente
cliente.query(f"delete from {destino} where competencia = '{competencia}'").result()

#execução da carga
job = cliente.load_table_from_dataframe(df.to_pandas(), destino, job_config=job_config)

#aguardar
job.result()
logging.info(f'Carga realizada com sucesso: {job.output_rows} linhas carregadas em {destino}!')