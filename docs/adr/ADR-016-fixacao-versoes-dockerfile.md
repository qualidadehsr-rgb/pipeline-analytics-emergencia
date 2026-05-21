# ADR-016 — Fixação de versões de dependências no Dockerfile

**Data:** 2026-05-21  
**Status:** Aceita

## Contexto

O Dockerfile do dbt Cloud Run Job instalava apenas `dbt-bigquery==1.11.0`, 
sem fixar a versão do `dbt-core`. O pip resolvia a dependência automaticamente 
e instalou `dbt-core==1.12.0-b1` (versão beta), causando:

- Warning `MissingArgumentsPropertyInGenericTestDeprecation` no teste 
  `dbt_utils.unique_combination_of_columns`
- Comportamento diferente entre ambiente local (`dbt-core==1.11.6`) e 
  Cloud Run (`dbt-core==1.12.0-b1`)
- Risco de builds não-reproduzíveis: o mesmo Dockerfile podia gerar 
  imagens diferentes dependendo do dia da build

## Decisão

Fixar todas as dependências críticas com operador `==`:

```dockerfile
RUN pip install dbt-bigquery==1.11.0 dbt-core==1.11.6
```

Atualizações de versão são feitas manualmente, de forma consciente, 
testando em ambiente local antes de atualizar o Dockerfile.

## Alternativas consideradas

**Usar operador `~=` (compatível):** permitiria atualizações de patch 
automaticamente (ex: `1.11.6` → `1.11.7`). Menor risco que sem fixação, 
mas ainda permite mudanças não-intencionais entre builds.

**Usar arquivo `requirements.txt` com hash:** máxima reprodutibilidade, 
mas adiciona complexidade de manutenção desproporcional ao tamanho do projeto.

## Consequências

- Builds reproduzíveis: a mesma imagem é gerada independente do dia
- Paridade entre ambiente local e Cloud Run
- Atualizações de dependências requerem decisão explícita e teste prévio
- Risco de ficar em versão desatualizada — mitigado com revisão periódica 
  (sugerido a cada 3-6 meses)