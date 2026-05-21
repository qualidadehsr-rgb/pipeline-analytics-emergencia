# Runbook — pipeline-analytics-emergencia

Guia de procedimentos operacionais para manutenção do pipeline.

---

## Deploy da imagem de ingestão

**Quando usar:** sempre que houver alteração em qualquer arquivo dentro da pasta `ingestion/`.

1. Build da imagem:
```bash
gcloud builds submit ingestion/ --tag us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/ingestao:vX
```

2. Atualizar o Cloud Run Service com a nova imagem:
```bash
gcloud run services update ingestao-pipeline-emergencia-service --image us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/ingestao:vX --region us-east1
```

> **Atenção:** os passos 1 e 2 devem sempre ser executados em sequência. O Cloud Run não atualiza automaticamente após o build.

---

## Deploy da imagem do dbt

**Quando usar:** sempre que houver alteração em qualquer arquivo dentro da pasta `dbt/`.

1. Limpar pastas temporárias antes do build:
```bash
Remove-Item -Recurse -Force pipeline_analytics\target -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force pipeline_analytics\dbt_packages -ErrorAction SilentlyContinue
```

2. Build da imagem (executar de dentro da pasta `dbt/`):
```bash
gcloud builds submit --tag us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/dbt-pipeline:vX
```

3. Atualizar o Cloud Run Job com a nova imagem:
```bash
gcloud run jobs update dbt-pipeline-job --image us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/dbt-pipeline:vX --region us-east1
```

> Substituir `vX` pela próxima versão sequencial. Para consultar a última versão:
> ```bash
> gcloud artifacts docker tags list us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/dbt-pipeline
> ```

---

## Execução manual do dbt Job

**Quando usar:** para testar alterações no dbt sem precisar re-ingerir os dados.

```bash
gcloud run jobs execute dbt-pipeline-job --region us-east1
```

---

## Limpeza de locks

**Quando usar:** para limpar o storage dos arquivos de meses que já foram ingeridos.

**Frequência:** a cada 2 meses.

**Antes de remover:** confirme que a competência já foi processada e não será re-ingerida.

1. Listar locks existentes:
```bash
gcloud storage ls gs://pipeline-analytics-emergencia-ingestao/locks/
```

2. Remover locks específicos:
```bash
gcloud storage rm gs://pipeline-analytics-emergencia-ingestao/locks/dbt_run_2026-03.lock
```

3. Remover todos os locks:
```bash
gcloud storage rm gs://pipeline-analytics-emergencia-ingestao/locks/*
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