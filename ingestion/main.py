import os
import sys
import json
import logging
import subprocess
import threading
import google.auth
import requests
import google.auth.transport.requests
from flask import Flask, request
from google.cloud import storage
from google.cloud import bigquery

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
    
    if blob_nome.startswith("locks/"):
        logging.info("Evento ignorado! Arquivo Lock.")
        return "Ok", 200
    
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

    def processar(script, caminho_local, nome_arquivo, bucket_nome):
        
        # criando cliente
        projeto = os.environ.get("PROJECT_ID")
        cliente = bigquery.Client(project=projeto)

        #definindo competência a partir do nome do arquivo
        periodo = nome_arquivo.split("_")
        competencia = periodo[2].split(".")
        competencia = "-".join([periodo[1], competencia[0]])

        # execução do script de ingestão correspondente
        logging.info(f"Iniciando ingestão: {script} para {nome_arquivo}")
        subprocess.run(["python", script, caminho_local], check=True)
        logging.info("Ingestão concluída com sucesso!")

        #lista das tabelas para confirmação da competência
        tabelas = ["atendimentos", "internacoes", "movimentacoes"]
        contador = 0
        for i in tabelas:
            registro_competencia = f"select count(*) as total from {projeto}.raw.{i} where competencia  = '{competencia}'"
            #executando
            resultado_tabela = cliente.query(registro_competencia).result()
            for linha in resultado_tabela:
                if linha.total > 0:
                    contador += 1
        
        #confere se todas as tabelas estão carregadas na competência certa
        if contador == 3:
            
            #nome do arquivo lock
            arquivo_lock = f'locks/dbt_run_{competencia}.lock'

            #cliente
            cliente = storage.Client()
            bucket = cliente.bucket(bucket_nome)
            blob = bucket.blob(arquivo_lock)

            #verificando a concorrência das instâncias
            try:
                blob.upload_from_string("",if_generation_match=0)
                logging.info('Lock criado!')
            except Exception as e:
                logging.info(f'Lock já existe para competência {competencia} - dbt Job já foi acionado por outra instância! Erro:{e}')
                return

            #busca as credenciais do ambiente
            credentials,_ = google.auth.default()
            
            #cria objeto http para renovação do token
            auth_req = google.auth.transport.requests.Request()

            #token de autenticação
            credentials.refresh(auth_req)

            #URL API Cloud Run
            url = f"https://us-east1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/{projeto}/jobs/dbt-pipeline-job:run"

            #cabeçalho
            headers = {'Authorization':f'Bearer {credentials.token}'}

            #chamada HTTP
            resposta = requests.post(url, headers=headers)
            logging.info(f"dbt Job acionado — status: {resposta.status_code} — resposta: {resposta.text}")
        else:
            logging.info(f"Aguardando demais arquivos — {contador}/3 carregados para competência {competencia}")
    
    thread = threading.Thread(target=processar, args=(script, caminho_local, nome_arquivo, bucket_nome))
    thread.start()
    return "OK", 200

# ponto de entrada principal — inicia o servidor Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))