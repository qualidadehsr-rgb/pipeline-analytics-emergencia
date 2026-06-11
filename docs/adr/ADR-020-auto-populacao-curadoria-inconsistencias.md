# ADR-020 — Auto-população da Curadoria de Inconsistências via populate_curadoria.py

## Contexto

O pipeline executa 47 testes de qualidade após cada ciclo de transformações dbt.
Quando testes falham, as inconsistências precisam ser visíveis ao responsável técnico
e à diretoria para acompanhamento e tomada de decisão.

Antes desta solução, as falhas de testes eram visíveis apenas nos logs do Cloud Run —
inacessíveis ao operador não técnico e sem histórico consolidado para análise de tendência.

Era necessário um mecanismo que registrasse automaticamente as inconsistências detectadas
numa tabela estruturada, sem intervenção manual, sempre que o pipeline fosse executado.

## Decisão

Criar o script `populate_curadoria.py`, executado automaticamente dentro do container
Docker do dbt após o `dbt test`, responsável por:

1. Ler o arquivo `run_results.json` gerado pelo dbt e identificar os testes com falha
2. Executar a query compilada de cada teste com falha diretamente no BigQuery para
   obter os atendimentos afetados
3. Inserir os registros na tabela `curadoria.curadoria_inconsistencias` de forma
   idempotente — delete por competência e teste antes de cada inserção

O script é invocado via `;` no ENTRYPOINT do Dockerfile, garantindo execução mesmo
quando o `dbt test` retorna erro.

## Funcionamento

Cada teste com falha gera um ou mais registros em `curadoria_inconsistencias` com os campos:
`id_inconsistencia`, `tipo`, `teste`, `nr_atendimento`, `competencia`, `servico`,
`detectado_em` e `status`.

O tipo de inconsistência é determinado pelo dicionário `TIPO_POR_TESTE` mapeado no script:
`logica_negocio`, `sequencia_temporal` ou `integridade`.

Testes definidos em arquivos `.yml` geram um hash hexadecimal no final do `unique_id`
(ex: `test.pipeline_analytics.unique_atendimentos_pa_atend_PA.308e485d02`). O script
detecta esse padrão e extrai o nome correto do penúltimo elemento da lista.

Testes cujas queries não retornam a coluna `competencia` (como o teste `unique` do dbt)
têm o valor buscado diretamente na tabela `marts.atendimentos_pa` via query auxiliar.

## Alternativas Consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| Registrar inconsistências manualmente após revisão dos logs | Depende de intervenção técnica — inacessível ao operador; sem histórico automático |
| Script externo acionado por Cloud Scheduler | Adiciona complexidade de orquestração; desacopla o registro das inconsistências da execução do dbt — risco de dessincronia |
| Usar dbt on-run-end hooks | Limitado ao contexto do dbt — não permite queries arbitrárias no BigQuery nem controle de idempotência por competência |

## Consequências

- Toda execução do pipeline registra automaticamente as inconsistências na tabela
  `curadoria.curadoria_inconsistencias`, independente de falhas nos testes
- O operador e a diretoria têm visibilidade estruturada das inconsistências sem
  acesso aos logs técnicos
- A idempotência garante que re-execuções do pipeline não geram duplicatas
- O `servico` de inconsistências do tipo `unique` fica como `NAO_IDENTIFICADO` —
  limitação conhecida da query gerada internamente pelo dbt