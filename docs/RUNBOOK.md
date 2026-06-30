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

## Deploy da imagem de curadoria

**Quando usar:** sempre que houver alteração em qualquer arquivo dentro da pasta `curadoria/`.

1. Build da imagem:
```bash
gcloud builds submit curadoria/ --tag us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/curadoria:vX
```

2. Atualizar o Cloud Run Service com a nova imagem:
```bash
gcloud run services update curadoria-pipeline-emergencia-service --image us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/curadoria:vX --region us-east1
```

> **Atenção:** os passos 1 e 2 devem sempre ser executados em sequência.

---

## Acesso à interface de curadoria

**URL:** `https://curadoria-pipeline-emergencia-service-533925368095.us-east1.run.app`

**Quando usar:** após cada execução do pipeline, para revisão dos casos suspeitos e inconsistências identificadas pelos testes de negócio.

**Como acessar:**
1. Abrir o navegador (Chrome ou Edge)
2. Acessar a URL acima
3. Fazer login com a conta corporativa `qualidade.hsr@gruposanta.com.br`
4. A interface carrega automaticamente os casos pendentes da competência mais recente

> **Atenção:** o acesso é controlado pelo Identity-Aware Proxy (IAP). Apenas contas explicitamente autorizadas conseguem acessar. Para adicionar novos usuários, acesse o console do GCP → Security → Identity-Aware Proxy → curadoria-pipeline-emergencia-service → Adicionar principal com o papel `IAP-secured Web App User`.

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

---

## Problemas conhecidos

| Sintoma | Causa | Solução aplicada | O que fazer se acontecer de novo |
|---|---|---|---|
| Após revisar um caso na curadoria, o total de casos pendentes na tela não diminui | Cache de resultado de consulta do BigQuery — o `cliente.query()` retorna dados salvos de uma execução anterior em vez de buscar o estado atual | Adicionado `bigquery.QueryJobConfig(use_query_cache=False)` nas duas queries de `listar_suspeitos()` em `curadoria/main.py` | Verificar se o `job_config` com `use_query_cache=False` está presente nas queries da função afetada |
| Um caso específico continua aparecendo na lista mesmo após ser decidido (pode passar despercebido, já que o restante da lista parece normal) | Mesma causa acima — cache de query | Mesma solução acima | Confirmar no BigQuery, via `SELECT status FROM curadoria_inconsistencias WHERE id_inconsistencia = '...'`, se o status realmente está `revisado`; se sim, o problema é de cache, não de dado |


---

## Regiões

| Recurso | Região |
|---|---|
| Cloud Run Service (ingestão) | us-east1 |
| Cloud Run Job (dbt) | us-east1 |
| Artifact Registry | us-east1 |
| BigQuery datasets | southamerica-east1 |
| Cloud Storage bucket | southamerica-east1 |
| Cloud Run Service (curadoria) | us-east1 |