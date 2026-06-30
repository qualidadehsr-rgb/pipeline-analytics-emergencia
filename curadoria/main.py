import datetime
import os
import uuid
import logging
from flask import Flask, request, render_template, redirect, url_for
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

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
    
    #desativa o uso de dados em cachê no BigQuery
    job_config = bigquery.QueryJobConfig(use_query_cache=False)

    #busca competências que possuem suspeitos pendentes
    query_competencias = f"""
        SELECT DISTINCT competencia 
        FROM {projeto}.curadoria.curadoria_inconsistencias 
        WHERE status = 'pendente'
        ORDER BY competencia DESC
    """
    competencias = [str(row.competencia) for row in cliente.query(query_competencias, job_config=job_config)]

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
        SELECT id_inconsistencia, tipo, nr_atendimento, detectado_em, competencia, servico
        FROM {projeto}.curadoria.curadoria_inconsistencias 
        WHERE status = 'pendente'
        AND competencia = '{competencia}'
    """
    suspeitos = [dict(row) for row in cliente.query(query_suspeitos, job_config=job_config)]
    
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
    tipo_inconsistencia = request.form.get("tipo_inconsistencia")
    cd_atendimento = request.form.get("cd_atendimento")
    decidido_por = request.form.get("decidido_por")
    decidido_em = datetime.datetime.now().isoformat()

    #verificando o tipo de inconsistência para carregar dados do formulário
    if tipo_inconsistencia == "conversao":
        decisao = request.form.get("decisao")
        competencia = request.form.get("competencia")
        atend_internacao = request.form.get("atend_internacao")
        destino = request.form.get("destino")
        unidade = request.form.get("unidade")
        tipo = request.form.get("tipo")
        id_inconsistencia = request.form.get("id_inconsistencia")
    
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

        #atualizar status após a revisão
        query_status = f"""
            update {projeto}.curadoria.curadoria_inconsistencias
            set status = 'revisado'
            where id_inconsistencia = '{id_inconsistencia}'
        """
        cliente.query(query_status)

        return redirect(url_for("listar_suspeitos"))
    elif tipo_inconsistencia == 'logica_negocio':
        id_inconsistencia = request.form.get("id_inconsistencia")
        prevalece = request.form.get("flag_prevalece")
        justificativa = request.form.get("justificativa")
        id_decisao = str(uuid.uuid4())

        #gravar dados no BigQuery
        query = f"""
            insert into {projeto}.curadoria.curadoria_decisao_logica
            (id_decisao, id_inconsistencia, flag_prevalece,
            justificativa, decidido_por, decidido_em)
            values('{id_decisao}', '{id_inconsistencia}', '{prevalece}',
            '{justificativa}', '{decidido_por}', '{decidido_em}')
        """
        cliente.query(query)

        #atualizar o status após revisão
        query_status = f"""
            update {projeto}.curadoria.curadoria_inconsistencias
            set status = 'revisado'
            where id_inconsistencia = '{id_inconsistencia}'
        """
        cliente.query(query_status)

        return redirect(url_for("listar_suspeitos"))
    elif tipo_inconsistencia == 'sequencia_temporal' or tipo_inconsistencia == 'integridade':
        id_inconsistencia = request.form.get("id_inconsistencia")
        campo_afetado = request.form.get("campo_afetado")
        valor_original = request.form.get("valor_original")
        valor_imputado = request.form.get("valor_imputado")
        id_imputacao = str(uuid.uuid4())
        if not valor_imputado:
            valor_imputado = valor_original
        #grava os dados
        query = f"""
            insert into {projeto}.curadoria.curadoria_imputacao_integridade
            (id_imputacao, id_inconsistencia, campo_afetado,
            valor_original, valor_imputado, decidido_por, decidido_em)
            values('{id_imputacao}', '{id_inconsistencia}', '{campo_afetado}',
            '{valor_original}', '{valor_imputado}', '{decidido_por}', '{decidido_em}')
        """
        cliente.query(query)
        #atualiza o status após revisão
        query_status = f"""
            update {projeto}.curadoria.curadoria_inconsistencias
            set status = 'revisado'
            where id_inconsistencia = '{id_inconsistencia}'
        """
        cliente.query(query_status)
        return redirect(url_for("listar_suspeitos"))
    else:
        logging.error("Tipo de inconsistência inexistente!")
        return render_template(
            "curadoria.html",
            competencias=[],
            competencia = None,
            suspeitos=[],
            mensagem="Tipo de inconsistência não identificado!"
        )
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