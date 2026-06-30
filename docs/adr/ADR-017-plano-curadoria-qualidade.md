# ADR-017 — Expansão da Curadoria para Inconsistências de Qualidade

**Data:** 2026-05-29

**Status:** Implementado (2026-06-30)

## Contexto

Os testes de negócio implementados no dbt identificam inconsistências reais
nos dados que afetam diretamente o cálculo dos KPIs. O primeiro caso concreto
encontrado foi o atendimento `1621248`, com `fl_conversao = 1` e `fl_evasao = 1`
simultaneamente — paciente com internação vinculada e origem válida
(`EMERGENCIA ADULTO`), mas com `MOTIVO_ALTA = 'EVASAO'` por erro de registro
no sistema hospitalar.

Esse tipo de inconsistência não é capturado pelo fluxo automático do pipeline
e não gera falha de infraestrutura — o dbt conclui com sucesso, os dados chegam
ao Power BI, mas os KPIs estão incorretos. Sem visibilidade sobre esses casos,
a equipe gestora toma decisões com base em números imprecisos.

A interface de curadoria existente (ADR-012) já estabeleceu o padrão de revisão
humana para suspeitos de conversão. Esse mesmo princípio se aplica às
inconsistências de qualidade identificadas pelos testes de negócio.

## Decisão

Expandir o escopo da interface de curadoria para acomodar dois tipos de revisão:

| Tipo | Origem | Ação esperada | Tabela de decisão |
|---|---|---|---|
| Suspeitos de conversão | `fl_suspeito_conversao = 1` no modelo dbt | Confirmar ou descartar a conversão | `curadoria_conversao` |
| Lógica de negócio | Falha em teste de negócio com flags logicamente excludentes (ex: `fl_conversao` e `fl_evasao` simultâneos) | Decidir qual flag prevalece, com justificativa opcional | `curadoria_decisao_logica` |
| Sequência temporal / Integridade | Falha em teste de negócio por evento fora de ordem ou valor impossível/ausente | Confirmar erro sem correção, ou imputar o valor correto encontrado no sistema fonte (MV) | `curadoria_imputacao_integridade` |

Os casos de inconsistência de qualidade devem ser apresentados na interface
de curadoria com identificação do teste que falhou, o registro afetado e
o tipo de violação encontrada.

## Justificativa

- Qualidade de dados não é negociável independente de volume — 1 registro
  incorreto em 10.000 ainda afeta os KPIs e pode distorcer decisões
- O padrão de curadoria já está estabelecido e conhecido pelos operadores —
  expandir o escopo é mais eficiente do que criar um fluxo paralelo
- Centralizar as revisões em um único ponto reduz o risco de casos não tratados
- Erros de cadastro são comuns em sistemas hospitalares e tendem a se repetir
  — ter visibilidade sobre eles é insumo para a gestão melhorar o processo
  no sistema MV

## Consequências

**Positivas:**
- KPIs calculados sobre dados revisados — maior confiabilidade nos números
- Visibilidade para a diretoria sobre o volume e padrão de inconsistências
  no sistema hospitalar
- Insumo para ação corretiva no cadastro do sistema MV
- Reaproveitamento da infraestrutura de curadoria já existente

**Negativas:**
- A interface de curadoria precisará ser evoluída para suportar o novo tipo
  de revisão — novo desenvolvimento necessário
- O fluxo operacional mensal ganha mais uma etapa de revisão humana antes
  da liberação dos dados para o BI
- Inconsistências recorrentes do mesmo tipo podem gerar volume de revisão
  crescente sem resolução na origem

## Posição no Roadmap

A implementação foi antecipada em relação ao plano original: a construção
da Página 1 no Power BI estava em andamento quando ficou evidente que KPIs
calculados sem essa camada de revisão estariam incorretos (caso do
atendimento `1621248`). A construção da Página 1 foi pausada para priorizar
esta expansão, retomando apenas após a conclusão.

**Pendência remanescente:** o JOIN das tabelas `curadoria_decisao_logica` e
`curadoria_imputacao_integridade` nos modelos dbt ainda não existe — as
decisões ficam registradas no BigQuery, mas ainda não refletem na
`marts.atendimentos_pa`. Detalhes no `plano-analitico.md`, Fase 1.

A página dedicada a inconsistências no painel (mencionada na versão anterior
desta ADR) está registrada no plano analítico como item de escopo futuro,
fora do roadmap imediato.