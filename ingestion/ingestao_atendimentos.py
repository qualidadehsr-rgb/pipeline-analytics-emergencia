import os
import sys
import polars as pl
from dotenv import load_dotenv
from google.cloud import bigquery

#carregar variáveis de ambiente
load_dotenv()

#buscar credencial de acesso
project_id = os.getenv("PROJECT_ID")

#cliente BigQuery
cliente = bigquery.Client(project=project_id)

#caminho do arquivo excel
caminho_arquivo = sys.argv[1]

#leitura do arquivo excel
df = pl.read_excel(caminho_arquivo)

#========================================
# TRATAMENTO DOS DADOS
#========================================

#filtrar empresa
df = df.filter(pl.col("EMPRESA") == "HSR")

#lista de colunas sensíveis
colunas_sensiveis = ['NM_PACIENTE', 'DT_NASC', 'ENDERECO',
                     'USUARIO_CLASSIF', 'USUARIO_CAD_RECEPCAO',
                     'USUARIO_ALTA', 'TOTAL_CONTA', 'CONTA',
                     'CONTA_FECHADA', 'REGISTRO_ANS']

#excluir colunas sensíveis
df = df.drop(colunas_sensiveis)

#correção texto de classificação de risco
df = df.with_columns(
    pl.col("COR_CLASSIF").str.replace("AMARELO1", "AMARELO")
)

#separação do nome do prestador do CRM, ficando apenas nome
df = df.with_columns(
    pl.col("PRESTADOR").str.split(" - ").list.last()
)

#configuração da coluna SERVIÇO
df = df.with_columns(
    pl.when(
        (pl.col("IDADE") <= 14) &
        (pl.col("ESPECIALIDADE") != "CIRURGIA GERAL") &
        (pl.col("ESPECIALIDADE") != "ORTOPEDIA/TRAUMATOLOGIA")
    ).then(pl.lit("PEDIATRIA"))
      .when(
          (pl.col("ESPECIALIDADE") == "CIRURGIA GERAL")
      ).then(pl.lit("CIRURGIA GERAL"))
      .when(
          (pl.col("ESPECIALIDADE") == "ORTOPEDIA/TRAUMATOLOGIA")
      ).then(pl.lit("ORTOPEDIA/TRAUMATOLOGIA"))
      .when(
          (pl.col("IDADE") >= 15) &
          (
          (pl.col("ESPECIALIDADE") == "CLINICA MEDICA") |
          (pl.col("ESPECIALIDADE") == "GENERALISTA")
          )
      ).then(pl.lit("CLINICA MEDICA"))
      .when(
          (pl.col("ESPECIALIDADE") == "MEDICO CARDIOLOGISTA")
      ).then(pl.lit("CARDIOLOGIA"))
      .otherwise(pl.lit("OUTROS")).alias("SERVICO")
)