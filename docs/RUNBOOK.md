# Runbook — pipeline-analytics-emergencia

Guia de procedimentos operacionais para manutenção do pipeline.

---

## Deploy da imagem de ingestão

**Quando usar:** sempre que houver alteração em qualquer arquivo dentro da pasta `ingestion/`.

**Comando:**
```bash
gcloud builds submit ingestion/ --tag us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/ingestao:latest
```

**O que esse comando faz:**
1. Envia a pasta `ingestion/` para o Cloud Build no GCP
2. Constrói a nova imagem Docker
3. Publica a imagem no Artifact Registry com a tag `latest`

**Após o deploy:** o Cloud Run Service já passa a usar a nova imagem automaticamente na próxima execução.

---

## Atualizar o Cloud Run Service após novo build

**Quando usar:** sempre após executar o comando de build — o Cloud Run não atualiza automaticamente.

**Comando:**
```bash
gcloud run services update ingestao-pipeline-emergencia-service --image us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/ingestao:latest --region us-east1
```

**Atenção:** esses dois comandos — build e update — devem sempre ser executados em sequência toda vez que houver alteração em qualquer arquivo da pasta `ingestion/`.

---

## Deploy da imagem do dbt

**Quando usar:** sempre que houver alteração em qualquer arquivo dentro da pasta `dbt/`.

**Comando:**
```bash
cd dbt
gcloud builds submit --tag us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/dbt-pipeline:vX
```

Substituir `vX` pela próxima versão sequencial (consultar a última versão no Artifact Registry).

**Após o build:** atualizar o Cloud Run Job com a nova imagem:

```bash
gcloud run jobs update dbt-pipeline-job --image us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/dbt-pipeline:vX --region us-east1
```

---

## Execução manual do dbt Job

**Quando usar:** para testar alterações no dbt sem precisar re-ingerir os dados.

**Comando:**
```bash
gcloud run jobs execute dbt-pipeline-job --region us-east1
```

---

## Regiões

| Recurso | Região |
|---|---|
| Cloud Run Service (ingestão) | us-east1 |
| Cloud Run Job (dbt) | us-east1 |
| Artifact Registry | us-east1 |
| BigQuery datasets | southamerica-east1 |
| Cloud Storage bucket | southamerica-east1 |

---

## Limpeza de locks

**Quando usar:** para limpar o storage dos arquivos de meses que já foram ingeridos.

**Frequência:** a cada 2 meses.

**Antes de remover:** confirme que a competência já foi processada e não será re-ingerida

**Comandos:**

***Listar locks existentes***
```bash
gcloud storage ls gs://pipeline-analytics-emergencia-ingestao/locks/
```

***Remover locks específicos***
```bash
gcloud storage rm gs://pipeline-analytics-emergencia-ingestao/locks/dbt_run_2026-03.lock
```

***Remover todos os locks***
```bash
gcloud storage rm gs://pipeline-analytics-emergencia-ingestao/locks/*
```
---