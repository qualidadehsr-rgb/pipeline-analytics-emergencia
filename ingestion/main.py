import os
import sys
import json
import logging
import subprocess
from flask import Flask, request
from google.cloud import storage

# configurações dos registros de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# inicialização do servidor Flask
app = Flask(__name__)

@app.route("/", methods=["POST"])
def ingestao():

    # captura do evento enviado pelo Eventarc
    envelope = request.get_json()
    if not envelope:
        logging.error("Requisição sem corpo JSON!")
        return "Bad Request", 400

    # log do evento completo para diagnóstico
    logging.info(f"Evento recebido: {envelope}")

    # extração dos dados do evento do Cloud Storage
    bucket_nome = envelope.get("bucket")
    blob_nome = envelope.get("name")

    if not bucket_nome or not blob_nome:
        logging.error("Evento sem bucket ou name!")
        return "Bad Request", 400

    # montagem do caminho completo no Cloud Storage
    nome_arquivo = blob_nome.split("/")[-1]
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
        return "Arquivo não reconhecido", 400

    # execução do script de ingestão correspondente
    logging.info(f"Iniciando ingestão: {script} para {nome_arquivo}")
    subprocess.run(["python", script, caminho_local], check=True)
    logging.info("Ingestão concluída com sucesso!")
    return "OK", 200

# ponto de entrada principal — inicia o servidor Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))