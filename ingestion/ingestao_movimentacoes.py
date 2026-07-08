import os
import sys
import re
import pandas as pd
import logging
from google.cloud import bigquery

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
periodo_mes = os.path.splitext(periodo[2])[0]

#unifica o ano ao mês
competencia = "-".join([periodo[1], periodo_mes])

# leitura do arquivo
df = pd.read_excel(caminho_arquivo, header=None, sheet_name=0)

# reproduz a unidade de internação e a data de movimentação para cada linha de dado
unidade_atual = None
data_atual = None

df['UNIDADE'] = None
df['DATA'] = None

# percorre o dataframe linha por linha, retornando dois valores a cada iteração: o número da linha e o conteúdo da linha
for numero_linha, linha in df.iterrows():
    # verifica se a string começa com esse texto. Quando sim, usa o valor da coluna 5 onde esta o nome da unidade
    if str(linha[0]).startswith('Unidade de Internação'):
           unidade_atual = linha[6]
    # remove espaços em branco no início e fim da string
    elif str(linha[0]).strip() == 'Data:':
          data_atual = linha[2]
    # acessa uma célula específica do dataframe para escrita
    df.at[numero_linha, 'UNIDADE'] = unidade_atual
    df.at[numero_linha, 'DATA'] = data_atual

# filtra apenas as linhas com dados de movimentações (Atend. numérico na coluna 1)
df = df[pd.to_numeric(df[1], errors='coerce').notna()]

# função auxiliar para verificar se um valor é horário (HH:MM:SS)
def eh_horario(valor):
      if pd.isna(valor):
            return False
      return bool(re.match(r'^\d{2}:\d{2}:\d{2}$', str(valor).strip()))

# normaliza as colunas deslocadas para um layout único
linhas_normalizadas = []

for numero_linha, linha in df.iterrows():
    # layout A: hora na coluna 10 (com coluna paciente)
    if eh_horario(linha[10]):
        linhas_normalizadas.append({
            'ATEND': linha[1],
            'NM_PACIENTE': linha[3],
            'HORA': linha[10],
            'TIPO': linha[11],
            'ORIGEM': linha[13],
            'DESTINO': linha[15],
            'TIP_ACOM': linha[16],
            'CID': linha[17],
            'CONVENIO': linha[18],
            'MOTIVO_ALTA': linha[19],
            'UNIDADE': linha['UNIDADE'],
            'DATA': linha['DATA'],
        })
    # layout B: hora na coluna 7
    elif eh_horario(linha[7]):
        linhas_normalizadas.append({
            'ATEND': linha[1],
            'NM_PACIENTE': linha[3],
            'HORA': linha[7],
            'TIPO': linha[8],
            'ORIGEM': linha[10],
            'DESTINO': linha[12],
            'TIP_ACOM': linha[13],
            'CID': linha[14],
            'CONVENIO': linha[15],
            'MOTIVO_ALTA': linha[16],
            'UNIDADE': linha['UNIDADE'],
            'DATA': linha['DATA'],
        })
    # layout C: hora na coluna 8
    elif eh_horario(linha[8]):
        linhas_normalizadas.append({
            'ATEND': linha[1],
            'NM_PACIENTE': linha[3],
            'HORA': linha[8],
            'TIPO': linha[9],
            'ORIGEM': linha[11],
            'DESTINO': linha[13],
            'TIP_ACOM': linha[14],
            'CID': linha[15],
            'CONVENIO': linha[16],
            'MOTIVO_ALTA': linha[17],
            'UNIDADE': linha['UNIDADE'],
            'DATA': linha['DATA'],
        })

df = pd.DataFrame(linhas_normalizadas)

# resetando a coluna de índice
df = df.reset_index(drop=True)


#cria coluna da competência no Dataframe
df["competencia"] = competencia

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

#deleta tabela se já existente
cliente.query(f"delete from {destino} where competencia = '{competencia}'").result()

#execução da carga
job = cliente.load_table_from_dataframe(df, destino, job_config=job_config)
logging.info('Enviando dados ao BigQuery...')

#aguardar carga
job.result()
logging.info(f'Carga realizada com sucesso: {job.output_rows} linhas carregadas em {destino}!')


