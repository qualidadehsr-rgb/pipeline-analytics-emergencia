# ADR-007 — Migração de Cloud Run Job para Cloud Run Service + Eventarc

## Status
Aceito

## Contexto
A ingestão automatizada foi inicialmente implementada como um Cloud Run Job, 
disparado manualmente via variável de ambiente `CAMINHO_ARQUIVO`. Esse modelo 
exigia intervenção técnica a cada execução mensal — inviável para um processo 
operado por usuários não técnicos.

O objetivo é que qualquer pessoa autorizada consiga iniciar o pipeline 
simplesmente fazendo upload do arquivo xlsx no bucket do Cloud Storage, 
sem nenhuma interação com o GCP além disso.

## Decisão
Migrar de Cloud Run Job para Cloud Run Service, integrado ao Eventarc para 
detecção automática de uploads no Cloud Storage.

O fluxo implementado:
1. Usuário faz upload do arquivo xlsx no bucket `pipeline-analytics-emergencia-ingestao`
2. Eventarc detecta o evento de finalização do upload (`google.cloud.storage.object.v1.finalized`)
3. Eventarc envia uma requisição HTTP POST ao Cloud Run Service com os metadados do arquivo
4. O Service identifica o tipo de arquivo pelo nome, baixa para `/tmp/` e executa o script correspondente
5. Os dados são carregados no BigQuery na camada Raw

## Justificativa
O Cloud Run Job não suporta o parâmetro `--destination-run-job` no Eventarc — 
apenas `--destination-run-service` é aceito. Portanto a arquitetura orientada 
a eventos exige obrigatoriamente um Service.

O Cloud Run Service com billing por requisição escala para zero quando ocioso, 
sem custo em standby. Para uma execução mensal de poucos minutos, o custo 
permanece dentro do nível gratuito do GCP.

## Consequências
- O processo mensal não exige mais intervenção técnica após o upload
- O `main.py` passou a usar Flask para receber eventos HTTP do Eventarc
- A variável de ambiente `CAMINHO_ARQUIVO` foi eliminada
- O Cloud Run Job `ingestao-pipeline-emergencia` permanece no GCP mas não é mais utilizado
- Permissões IAM configuradas: `roles/eventarc.eventReceiver` para `pipeline-analytics-sa` e `roles/pubsub.publisher` para a conta de serviço do Cloud Storage