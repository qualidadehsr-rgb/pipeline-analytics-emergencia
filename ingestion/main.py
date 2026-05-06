import sys
import os
import logging
import subprocess

# configurações dos registros de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# verificação do ponto de entrada principal
if __name__ == "__main__":

    # validação do argumento de entrada
    if len(sys.argv) < 2:
        logging.error("Caminho do arquivo não informado!")
        sys.exit(1)

    # captura do caminho do arquivo via variável de ambiente
    caminho = os.environ.get("CAMINHO_ARQUIVO")
    if not caminho:
        logging.error("Variável de ambiente CAMINHO_ARQUIVO não informada!")
        sys.exit(1)

    # captura do nome do arquivo
    nome_arquivo = caminho.split("/")[-1]

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

    # rodando script de ingestão
    subprocess.run(["python", script, caminho], check=True)

    logging.info("Ingestão concluída com sucesso!")