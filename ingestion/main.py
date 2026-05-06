import os
import sys
import logging
import subprocess
from google.cloud import storage

# configurações dos registros de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# verificação do ponto de entrada principal
if __name__ == "__main__":

    # captura do caminho do arquivo via variável de ambiente
    caminho_gcs = os.environ.get("CAMINHO_ARQUIVO")
    if not caminho_gcs:
        logging.error("Variável de ambiente CAMINHO_ARQUIVO não informada!")
        sys.exit(1)

    # captura do nome do arquivo
    nome_arquivo = caminho_gcs.split("/")[-1]

    # definição do caminho local temporário dentro do container
    caminho_local = f"/tmp/{nome_arquivo}"

    # download do arquivo do Cloud Storage para o container
    logging.info(f"Baixando {nome_arquivo} do Cloud Storage...")
    partes = caminho_gcs.replace("gs://", "").split("/")
    bucket_nome = partes[0]
    blob_nome = "/".join(partes[1:])

    cliente_storage = storage.Client()
    bucket = cliente_storage.bucket(bucket_nome)
    blob = bucket.blob(blob_nome)
    blob.download_to_filename(caminho_local)
    logging.info(f"Download concluído: {caminho_local}")

    # verificação do tipo de arquivo para chamar script correspondente
    if "atendimentos" in nome_arquivo:
        script = "ingestao_atendimentos.py"
    elif "internacoes" in nome_arquivo:
        script = "ingestao_internacoes.py"
    elif "movimentacoes" in nome_arquivo:
        script = "ingestao_movimentacoes.py"
    else:
        logging.error(f"Arquivo não reconhecido: {nome_arquivo}")
        sys.exit(1)

    # registro de inicio da ingestão
    logging.info(f"Iniciando ingestão: {script} para {nome_arquivo}")

    # rodando script de ingestão com caminho local
    subprocess.run(["python", script, caminho_local], check=True)

    logging.info("Ingestão concluída com sucesso!")