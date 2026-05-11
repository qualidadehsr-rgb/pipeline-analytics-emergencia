# ADR-008 — Verificação de Competência e Acionamento Automático do dbt Job

## Contexto
O pipeline recebe 3 arquivos mensais de forma independente — cada upload 
dispara uma ingestão separada via Eventarc. Sem controle de completude, 
o dbt poderia ser acionado antes que todos os arquivos do mês estivessem 
carregados, gerando resultados parciais e incorretos nos indicadores.

## Decisão
Após cada ingestão bem-sucedida, o `main.py` consulta as 3 tabelas da 
camada `raw` no BigQuery verificando se todas possuem registros para a 
mesma competência (YYYY-MM). Somente quando as 3 tabelas confirmarem 
dados da competência do mês, o Cloud Run Job `dbt-pipeline-job` é acionado 
automaticamente via chamada à API do Google Cloud.

## Justificativa
- A competência já está presente nas tabelas `raw` como coluna — não é 
  necessário controle externo ou tabela auxiliar
- O acionamento via API do Cloud Run mantém tudo na mesma infraestrutura 
  já definida, sem ferramentas adicionais
- A lógica dentro do `main.py` elimina a necessidade de orquestradores 
  externos como Cloud Scheduler ou Workflows
- Custo zero — a verificação usa consultas simples ao BigQuery dentro da 
  cota gratuita

## Consequências
- **Positivas:**
    - Pipeline totalmente automático do upload ao dbt sem intervenção humana
    - Garantia de que o dbt só roda com os dados do mês completos
    - Rastreabilidade via logs do Cloud Run registrando cada etapa
- **Negativas:**
    - Se um dos 3 arquivos não for carregado no mês, o dbt nunca é acionado 
      automaticamente — requer intervenção manual
    - Lógica de orquestração acoplada ao `main.py` — em caso de crescimento 
      do pipeline pode exigir migração para orquestrador dedicado