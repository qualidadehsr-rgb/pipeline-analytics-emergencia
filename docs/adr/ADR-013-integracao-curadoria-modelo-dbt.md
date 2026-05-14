# ADR-013 — Integração das Decisões de Curadoria no Modelo dbt

**Data:** 2026-05-14  
**Status:** Implementada

## Contexto

A interface de curadoria (ADR-012) permite que o responsável operacional registre decisões sobre casos suspeitos de conversão na tabela `curadoria.curadoria_conversao`. Porém, o modelo `atendimentos_pa` no dbt calculava `fl_conversao` apenas pelo JOIN automático com internações, sem considerar as decisões humanas. As decisões ficavam salvas no BigQuery mas não chegavam à camada marts nem ao Power BI.

## Decisão

Integrar a tabela de curadoria ao modelo `atendimentos_pa` via LEFT JOIN, atualizando a lógica do `fl_conversao` para incorporar confirmações humanas.

### Alterações implementadas

- **`_sources.yml`**: adicionada source `curadoria.curadoria_conversao` no mesmo arquivo das sources existentes (raw)
- **`atendimentos_pa.sql`**: LEFT JOIN com a tabela de curadoria; `fl_conversao` atualizado com CASE WHEN de duas condições (JOIN automático OU decisão confirmada na curadoria)
- **`fl_suspeito_conversao`**: mantido sem alteração — continua marcando todos os casos identificados pela regra automática, independente da decisão do curador

### Lógica atualizada do fl_conversao

```sql
CASE
  WHEN ai.ATENDIMENTO IS NOT NULL THEN 1       -- JOIN automático com internações
  WHEN cur.decisao = 'confirmado' THEN 1        -- confirmado na curadoria
  ELSE 0
END
```

## Justificativa

- **LEFT JOIN**: atendimentos sem registro na curadoria não são afetados (cur.* retorna NULL e o CASE WHEN segue a lógica normal)
- **source() em vez de ref()**: a tabela de curadoria é alimentada pela interface Flask, não é gerenciada pelo dbt
- **fl_suspeito mantido**: funciona como indicador de governança para a diretoria — mostra o volume de cadastros incorretos que precisam de correção manual, evidência para cobrar melhoria no sistema de origem
- **Tabela vazia no primeiro run**: LEFT JOIN com tabela vazia é inofensivo, o modelo funciona normalmente antes de qualquer curadoria ser feita

## Consequências

- O fluxo completo está conectado: curadoria → Finalizar → dbt re-run → marts atualizada → Power BI reflete decisões humanas
- O dbt precisa rodar duas vezes por competência: uma após ingestão (gera suspeitos) e outra após curadoria (incorpora decisões)
- Qualquer nova coluna adicionada à curadoria no futuro pode ser incorporada ao modelo via o mesmo LEFT JOIN