# ADR-017 — Expansão da Curadoria para Inconsistências de Qualidade

**Data:** 2026-05-29

**Status:** Decisão tomada — implementação pendente

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

| Tipo | Origem | Ação esperada |
|---|---|---|
| Suspeitos de conversão | `fl_suspeito_conversao = 1` no modelo dbt | Confirmar ou descartar a conversão |
| Inconsistências de qualidade | Falha em testes de negócio que afetam KPIs | Investigar, registrar e sinalizar para correção no sistema |

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

Esta implementação será realizada após a construção da Página 1 no Power BI
e da carga histórica, como parte da evolução da interface de curadoria.
Uma página dedicada a inconsistências no painel também será avaliada nesse
momento.