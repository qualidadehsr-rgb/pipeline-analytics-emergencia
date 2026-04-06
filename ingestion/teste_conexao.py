import os
from dotenv import load_dotenv
from google.cloud import bigquery

#carrega variáveis de ambiente
load_dotenv()

#carrega variável do .env
project_id = os.getenv("PROJECT_ID")

#cliente BigQuery
client = bigquery.Client(project = project_id)

#query para testar conexão
query = "SELECT 1 as teste"
resultado = client.query(query)

for row in resultado:
    print(f'Conexão funcionando! Resultado: {row.teste}')