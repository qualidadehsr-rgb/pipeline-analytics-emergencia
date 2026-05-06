import os
import sys
import json
import logging
import subprocess
from google.cloud import storage

# configurações dos registros de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":

    # captura do evento enviado pelo Eventarc via variável de ambiente
    evento = os.environ.get("CLOUD_RUN_JOB")
    bucket_nome = os.environ.get("BUCKET_NAME")
    blob_nome = os.environ.get("OBJECT_NAME")

    # validação das variáveis do evento
    if not bucket_nome or not blob_nome:
        logging.error("Variáveis BUCKET_NAME ou OBJECT_NAME não informadas!")
        sys.exit(1)

    # montagem do caminho completo no Cloud Storage
    caminho_gcs = f"gs://{bucket_nome}/{blob_nome}"
    nome_arquivo = blob_nome.split("/")[-1]

    # definição do caminho local temporário dentro do container
    caminho_local = f"/tmp/{nome_arquivo}"

    # download do arquivo do Cloud Storage para o container
    logging.info(f"Baixando {nome_arquivo} do Cloud Storage...")
    cliente_storage = storage.Client()
    bucket = cliente_storage.bucket(bucket_nome)
    blob = bucket.blob(blob_nome)
    blob.download_to_filename(caminho_local)
    logging.info(f"Download concluído: {caminho_local}")

    # identificação do script correto pelo nome do arquivo
    if "atendimentos" in nome_arquivo:
        script = "ingestao_atendimentos.py"
    elif "internacoes" in nome_arquivo:
        script = "ingestao_internacoes.py"
    elif "movimentacoes" in nome_arquivo:
        script = "ingestao_movimentacoes.py"
    else:
        logging.error(f"Arquivo não reconhecido: {nome_arquivo}")
        sys.exit(1)

    # execução do script de ingestão correspondente
    logging.info(f"Iniciando ingestão: {script} para {nome_arquivo}")
    subprocess.run(["python", script, caminho_local], check=True)
    logging.info("Ingestão concluída com sucesso!")