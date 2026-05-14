import datetime
import os
import logging
from flask import Flask, request, render_template, redirect, url_for
from google.cloud import bigquery

# configurações dos registros de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# inicialização do servidor Flask
app = Flask(__name__)

# criando cliente BQ
projeto = os.environ.get("PROJECT_ID")
cliente = bigquery.Client(project=projeto)

#apresenta os casos suspeitos de conversão para investigação
@app.route("/")
def listar_suspeitos():

    #busca competência selecionada pelo usuario (se houver)
    par_competencia = request.args.get("competencia")
    
    #busca competências que possuem suspeitos pendentes
    query_competencias = f"""
        SELECT DISTINCT competencia 
        FROM {projeto}.marts.atendimentos_pa 
        WHERE fl_suspeito_conversao = 1 
        AND CAST(atend_PA AS STRING) NOT IN (SELECT CD_ATENDIMENTO FROM {projeto}.curadoria.curadoria_conversao)
        ORDER BY competencia DESC
    """
    competencias = [str(row.competencia) for row in cliente.query(query_competencias)]

    #se nao houver suspeitos pendentes em nenhuma competência
    if not competencias:
        return render_template(
            "curadoria.html",
            competencias=[],
            competencia=None,
            suspeitos=[],
            mensagem=None
        )

    #usa competência selecionada ou a mais recente
    competencia = par_competencia if par_competencia in competencias else competencias[0]

    # buscar suspeitos pendentes da competencia
    query_suspeitos = f"""
        SELECT atend_PA, CD_PACIENTE, DT_ATENDIMENTO, competencia
        FROM {projeto}.marts.atendimentos_pa 
        WHERE fl_suspeito_conversao = 1 
        AND competencia = '{competencia}'
        AND CAST(atend_PA AS STRING) NOT IN (SELECT CD_ATENDIMENTO FROM {projeto}.curadoria.curadoria_conversao)
    """
    suspeitos = [dict(row) for row in cliente.query(query_suspeitos)]
    
    return render_template(
        "curadoria.html",
        competencias=competencias,
        competencia=competencia,
        suspeitos=suspeitos,
        mensagem=None
    )

#grava as decisões após investigação dos casos suspeitos
@app.route("/decidir", methods=["POST"])
def gravar_decisao():
    
    #recebe dados do formulário
    cd_atendimento = request.form.get("cd_atendimento")
    decisao = request.form.get("decisao")
    competencia = request.form.get("competencia")
    atend_internacao = request.form.get("atend_internacao")
    destino = request.form.get("destino")
    unidade = request.form.get("unidade")
    tipo = request.form.get("tipo")
    decidido_por = request.form.get("decidido_por")
    decidido_em = datetime.datetime.now().isoformat()

    #gravar dados no bigquery
    query = f"""
        insert into {projeto}.curadoria.curadoria_conversao
        (CD_ATENDIMENTO, decisao, competencia,
        atend_internacao, destino, unidade,
        tipo, decidido_por, decidido_em)
        values ('{cd_atendimento}', '{decisao}', '{competencia}',
        '{atend_internacao}', '{destino}', '{unidade}',
        '{tipo}', '{decidido_por}', '{decidido_em}')
    """
    cliente.query(query)
    return redirect(url_for("listar_suspeitos"))

#dispara o dbt para materializar as tabelas após revisão dos casos suspeitos
@app.route("/finalizar", methods=["POST"])
def finalizar_curadoria():
    
    from google.cloud.run_v2 import JobsClient

    # configurações do job
    regiao = os.environ.get("REGION", "us-east1")
    nome_job = f"projects/{projeto}/locations/{regiao}/jobs/dbt-pipeline-job"

    # disparar o Cloud Run Job do dbt
    logging.info("Disparando re-run do dbt após curadoria...")
    jobs_client = JobsClient()
    jobs_client.run_job(name=nome_job)
    logging.info("dbt Job disparado com sucesso!")

    return render_template(
        "curadoria.html",
        competencias=[],
        competencia=None,
        suspeitos=[],
        mensagem="Curadoria finalizada! O dbt está reprocessando os dados."
    )
#confirmação
@app.route("/health", methods=["GET"])
def checagem():
    return "Ok", 200

# ponto de entrada principal — inicia o servidor Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))