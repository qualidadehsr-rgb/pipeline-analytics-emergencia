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

> **Atenção:** os passos 1 e 2 devem sempre ser executados em sequência. Para consultar a última versão:
> ```bash
> gcloud artifacts docker tags list us-east1-docker.pkg.dev/pipeline-analytics-emergencia/pipeline-ingestao/curadoria
> ```

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
| Botão "Finalizar Curadoria" não aparece quando não há casos pendentes | Botão estava dentro do bloco condicional `{% else %}` que só renderiza quando existem casos suspeitos | Movido para fora do bloco, protegido por `{% if competencias %}` independente | Verificar no template se o botão está fora do `{% endif %}` do bloco de suspeitos |
| Casos de `sequencia_temporal` não fornecem informação suficiente para revisão | A interface exibia apenas o tipo e o atendimento, sem detalhar qual sequência temporal falhou | Resolvido: exibição do nome do `teste` como badge na interface (`curadoria.html`), já disponível na tabela `curadoria_inconsistencias` sem necessidade de gravar contexto adicional | Verificar se a coluna `teste` está incluída no `SELECT` de `listar_suspeitos()` em `main.py` |
| Mesmo atendimento aparece duplicado (2-3 vezes) na tela de curadoria para o mesmo tipo/teste | A comparação em `filtrar_novos()` (`populate_curadoria.py`) comparava a `competencia` como `STRING` (registro novo) contra `DATE` (retorno do BigQuery) — tipos diferentes nunca são considerados iguais em Python, então o filtro nunca reconhecia registros já existentes | Corrigido em `v36`: adicionado `str()` ao redor de `row.competencia` na construção do conjunto `existentes`, garantindo comparação consistente | Verificar se a comparação em `filtrar_novos()` usa o mesmo tipo (string) dos dois lados da tupla antes de qualquer alteração nessa função |
| Teste dbt novo aparece como `nao_mapeado` na coluna "Tipo" da curadoria | `populate_curadoria.py` usa um dicionário fixo (`TIPO_POR_TESTE`) para classificar cada teste; testes novos não incluídos nele caem no valor padrão `"nao_mapeado"` | Adicionada a entrada correspondente em `TIPO_POR_TESTE`; os registros já inseridos incorretamente foram corrigidos via `UPDATE` direto na `curadoria_inconsistencias` | Ao criar qualquer teste dbt novo destinado à curadoria, adicionar a entrada em `TIPO_POR_TESTE` (e, se aplicável, em `TESTES_SEM_CORRECAO`) antes do deploy — não depois |
| Um teste dbt novo, ao ser criado, gera um volume grande de casos na curadoria de uma vez, incluindo competências antigas já dadas como concluídas | `stg_atendimentos` reprocessa a tabela Raw inteira a cada execução (sem filtro de competência) — um teste novo é aplicado a todo o histórico já carregado na primeira vez que roda, não só à competência do mês corrente | Comportamento esperado, não é bug — nenhuma ação corretiva aplicada | Antes de criar um teste novo, considerar avisar quem for revisar a curadoria que um volume maior que o usual pode aparecer na primeira execução após o deploy |
| `git push` falha com "Invalid username or token. Password authentication is not supported" | Token de acesso pessoal do GitHub expirado — pode estar salvo em cache no Gerenciador de Credenciais do Windows ou embutido na URL do remote (`git remote -v`) | Gerado novo token em `github.com/settings/tokens`, e atualizado via `git remote set-url origin https://usuario:novo_token@github.com/...` | Gerar novo token com escopo `repo`, verificar se o token está embutido na URL do remote (`git remote -v`) antes de mexer no Gerenciador de Credenciais do Windows — a credencial pode estar em qualquer um dos dois lugares |

| Um atendimento aparece com mais de uma linha de internação (ou de suspeita de conversão) na `atendimentos_pa`, mesmo sem duplicata na origem | `QUALIFY ROW_NUMBER() OVER(PARTITION BY ...)` particionando pela chave da tabela "de dentro" do JOIN (ex: `lc.ATENDIMENTO`, o nº da internação) em vez da chave "de fora" (`u.CD_ATENDIMENTO`, o nº do atendimento), garante 1 linha por internação, não 1 linha por atendimento, então mais de uma internação candidata no mesmo atendimento sobrevive ao filtro | Corrigido em `atendimentos_pa.sql` adicionando um CTE de dedupe posterior (`_unico`), que reparticiona pela chave certa, sem alterar a lógica original do CTE de origem | Ao escrever `QUALIFY ROW_NUMBER() ... PARTITION BY` logo após um JOIN, confirmar que a partição está na chave da tabela que deve ficar única no resultado final, não na chave da tabela do outro lado do JOIN |
| Contagem de suspeitos de conversão (`fl_suspeito_conversao`) muda inesperadamente entre execuções do dbt, sem mudança nos dados de origem | Um mesmo `nr_atendimento` tinha mais de uma decisão registrada em `curadoria_decisao_logica` (caso reaberto e revisado de novo), o CTE `decisao_logica` em `int_curadoria_correcoes.sql` não filtrava pra manter só uma, então o JOIN duplicava a linha | Adicionado `QUALIFY ROW_NUMBER() OVER(PARTITION BY ci.nr_atendimento ORDER BY dl.decidido_em DESC) = 1` no CTE `decisao_logica`, mantém sempre a decisão mais recente | Antes de investigar um caso de contagem divergente na curadoria, checar se `nr_atendimento` tem mais de uma linha em `curadoria_decisao_logica`, reabertura de caso é uma causa legítima e recorrente, não incomum |

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