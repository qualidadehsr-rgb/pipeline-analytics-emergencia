import json
import uuid
from datetime import datetime, timezone
from google.cloud import bigquery

# dicionário de testes
TIPO_POR_TESTE = {
    "conversao_evasao_exclusivos": "logica_negocio",
    "unique_atendimentos_pa_atend_PA": "integridade",
    "idade_nao_negativa": "integridade",
    "movimentacoes_nulos_invalidos": "integridade",
    "atend_medico_apos_classif_risco": "sequencia_temporal",
    "classif_risco_apos_totem": "sequencia_temporal",
    "fim_atend_medico_apos_inicio": "sequencia_temporal",
    "permanencia_nao_negativa": "sequencia_temporal",
}

# leitura do run_results para extração dos testes que falharam
def ler_testes_com_falha(caminho_run_results):
    with open(caminho_run_results, "r") as f:
        run_results = json.load(f)

    testes_com_falha = []
    for resultado in run_results["results"]:
        if resultado["status"] == "fail":
            testes_com_falha.append(resultado)
    
    return testes_com_falha

# verificar quais atendimentos estão falhando
def buscar_atendimentos(cliente, compiled_code):
    resultado = cliente.query(compiled_code).result()

    atendimentos = []
    for linha in resultado:
        atendimentos.append(dict(linha))
    
    return atendimentos

# estruturar o registro para persistência no BigQuery
def montar_registro(cliente, teste_nome, tipo, atendimento, detectado_em):
    # verificar se a coluna de competência esta em atendimento
    if "competencia" not in atendimento:
        query = f"""
            select competencia from `pipeline-analytics-emergencia.marts.atendimentos_pa`
            where atend_PA = {atendimento["unique_field"]}
        """
        resultado = cliente.query(query).result()
        atendimento["competencia"] = next(resultado)["competencia"]

    return{
        "id_inconsistencia": str(uuid.uuid4()),
        "tipo": tipo,
        "teste": teste_nome,
        "nr_atendimento": atendimento.get("atend_PA") or atendimento.get("Atendimento") or atendimento.get("unique_field"),
        "competencia": str(atendimento["competencia"]),
        "servico": atendimento.get("SERVICO") or atendimento.get("servico") or "NAO_IDENTIFICADO",
        "detectado_em": detectado_em.isoformat(),
        "status": "pendente",
    }

def deletar_registros_existentes(cliente, registros):
    # extrair combinações únicas de competência e teste da lista de registro
    combinacoes = set()
    for registro in registros:
        combinacoes.add((registro["competencia"], registro["teste"]))

    # percorre o set combinações desempacotando a tupla nas variáveis competencia e teste
    for competencia, teste in combinacoes:
        # query para fazer o delete
        query = f"""
            DELETE FROM `pipeline-analytics-emergencia.curadoria.curadoria_inconsistencias`
            WHERE competencia = '{competencia}'
            AND teste = '{teste}'
        """
        # executa a query no BigQuery
        cliente.query(query).result()
        print(f"Registros deletados — competencia: {competencia}, teste: {teste}")

def main():
    caminho_run_results = "/app/pipeline_analytics/target/run_results.json"

    testes_com_falha = ler_testes_com_falha(caminho_run_results)

    if not testes_com_falha:
        print("Nenhuma falha encontrada nos testes dbt. Nada a registrar.")
        return
    
    print(f"{len(testes_com_falha)} teste(s) com falha encontrado(s). Iniciando registro na curadoria...")

    # variável para criar conexão com BigQuery
    cliente = bigquery.Client()
    
    # endereço da tabela onde será salvo os registros
    tabela = "pipeline-analytics-emergencia.curadoria.curadoria_inconsistencias"
    
    # registra o momento que o script esta rodando e guarda na variável
    detectado_em = datetime.now(timezone.utc)
    # lista para acumular os registros inseridos no BigQuery
    registros = []

    # iteração sobre a lista de falhas
    for teste in testes_com_falha:
        # pega o valor do campo unique_id do dicionário de teste e guarda na variável
        unique_id = teste["unique_id"]

        
        # separa o nome do teste, divide a string nos pontos para formar uma lista
        partes = unique_id.split(".")

        # verifica se é hexadecimal
        try:
            int(partes[-1], 16)
            eh_hex = True
        except ValueError:
            eh_hex = False
        
        if eh_hex:
            teste_nome = partes[-2]
        else:
            teste_nome = partes[-1]

        # busca o tipo da inconsistência no dicionário pré-definido
        tipo = TIPO_POR_TESTE.get(teste_nome, "nao_mapeado")

        # guarda o valor do teste no compiled e guarda na variável
        compiled_code = teste["compiled_code"]

        print(f"Buscando atendimentos para o teste: {teste_nome}")
        
        # guarda a lista de atendimentos que falharam usando a função buscar_atendimentos
        atendimentos = buscar_atendimentos(cliente, compiled_code)

        # percorre os atendimentos com falhas para registrar na curadoria_inconsistencia
        for atendimento in atendimentos:
            # monta a estrutura dos registros das falhas e guarda na variável
            registro = montar_registro(cliente, teste_nome, tipo, atendimento, detectado_em)
            registros.append(registro)
    
    # verifica se a lista tem algum registro antes de inserir no BigQuery
    if registros:
        # deleta registros existentes para evitar duplicatas
        deletar_registros_existentes(cliente, registros)
        # inseri todos os registros na tabela curadoria_inconsistencias
        erros = cliente.insert_rows_json(tabela, registros)
        if erros:
            print(f"Erros ao inserir registros: {erros}")
        else:
            print(f"{len(registros)} registro(s) inserido(s) na curadoria_inconsistencias.")

if __name__ == "__main__":
    main()