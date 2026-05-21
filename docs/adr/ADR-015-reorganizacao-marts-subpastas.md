# ADR-015 — Reorganização da marts em subpastas com clusterização por modelo

**Data:** 2026-05-21  
**Status:** Aceita

## Contexto

A camada marts possuía dois modelos (`atendimentos_pa` e `ranking_especialidades`) 
no mesmo diretório. A configuração de `cluster_by` no `dbt_project.yml` era 
definida no nível `marts`, aplicando-se a todos os modelos igualmente.

O modelo `ranking_especialidades` não possui as colunas `CONVENIO` e `COR_CLASSIF` 
definidas no cluster, causando erro no BigQuery: 
`Unrecognized name: CONVENIO at [9:25]`.

## Decisão

Reorganizar a marts em subpastas por domínio:

```
marts/
├── atendimentos/
│   ├── atendimentos_pa.sql
│   └── atendimentos_pa.yml
└── ranking/
    ├── ranking_especialidades.sql
    └── ranking_especialidades.yml
```

Configurações comuns (materialização, schema, particionamento) permanecem 
no nível `marts` do `dbt_project.yml`. Configurações específicas (clusterização) 
ficam no nível da subpasta:

```yaml
marts:
  +materialized: table
  +schema: marts
  +partition_by:
    field: competencia
    data_type: date
  atendimentos:
    +cluster_by:
      - SERVICO
      - CONVENIO
      - COR_CLASSIF
```

## Alternativas consideradas

**Usar `config()` no topo de cada modelo SQL:** resolve o problema com menos 
alteração de estrutura, mas descentraliza as configurações. Pra revisar 
clusterização, seria necessário abrir cada arquivo SQL individualmente.

**Manter pasta única e remover cluster_by do nível marts:** resolve o erro 
imediato, mas perde a clusterização do `atendimentos_pa` ou obriga a usar 
`config()` no modelo — mesma desvantagem da alternativa anterior.

## Consequências

- Configurações centralizadas no `dbt_project.yml` — um único local pra 
  revisar todas as configurações de materialização, particionamento e cluster
- Estrutura preparada pra crescimento — novos modelos de marts entram na 
  subpasta adequada e herdam ou definem suas configurações
- Subpastas vazias (sem configuração específica) não devem ser declaradas 
  no `dbt_project.yml` para evitar warning de deprecation `MissingPlusPrefixDeprecation`