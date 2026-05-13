# ADR-010 — Lock para acionamento único do dbt Job

## Contexto
O Eventarc dispara um evento para cada arquivo enviado ao bucket. Como são 3 arquivos mensais enviados quase simultaneamente, o Cloud Run pode criar instâncias em paralelo. Quando duas ou mais instâncias verificam ao mesmo tempo que as 3 tabelas já estão carregadas, ambas acionam o dbt Job — gerando execuções duplicadas. Esse cenário é conhecido como race condition (condição de corrida).

## Decisão
Implementar um mecanismo de lock no Cloud Storage usando arquivo vazio com nome baseado na competência (ex: `locks/dbt_run_2026-03.lock`). A criação usa o parâmetro `if_generation_match=0`, que garante atomicidade — apenas uma instância consegue criar o arquivo. As demais recebem erro e encerram sem acionar o Job. Adicionado também filtro no `main.py` para ignorar eventos do Eventarc disparados pela criação do próprio arquivo de lock.

## Justificativa
- Cloud Storage é mais leve e rápido que BigQuery para operações simples de leitura/escrita
- `if_generation_match=0` é uma operação atômica nativa do Cloud Storage — não requer infraestrutura adicional
- Lock por competência permite execuções independentes de meses diferentes
- Alternativas como Pub/Sub ou Cloud Tasks adicionariam complexidade e custo desnecessários para o volume atual

## Consequências
- **Positivas:**
    - Garante acionamento único do dbt Job mesmo com uploads simultâneos
    - Sem custo adicional — usa recurso já existente (bucket)
    - Rastreável via logs (criação do lock e tentativas rejeitadas)
- **Negativas:**
    - Locks antigos acumulam no bucket e precisam ser limpos periodicamente
    - Se o dbt Job falhar após a criação do lock, o reprocessamento exige remoção manual do lock