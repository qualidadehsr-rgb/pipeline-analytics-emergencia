# ADR-009 — Particionamento e Clusterização no BigQuery

## Contexto
Com a implementação do WRITE_APPEND e acúmulo de histórico na camada Raw, as tabelas tendem a crescer ao longo dos meses. Sem particionamento, toda consulta ao BigQuery lê a tabela inteira — aumentando custo e tempo de resposta. O Power BI consome a camada Marts com filtros frequentes por período, serviço, convênio e classificação de risco.

## Decisão
| Camada | Particionamento | Clusterização |
|---|---|---|
| Raw | `competencia` (STRING, via ingestão) | — |
| Staged | `competencia` (DATE, convertida via PARSE_DATE) | — |
| Marts | `competencia` (DATE) | `SERVICO`, `CONVENIO`, `COR_CLASSIF` |

Configuração centralizada no `dbt_project.yml`, não nos modelos individuais.

## Justificativa
- Particionamento por `competencia` é o filtro mais natural do pipeline — todas as consultas são mensais
- Clusterização no Marts pelas 3 colunas mais filtradas no Power BI reduz custo e melhora performance
- Staged não tem clusterização porque o volume mensal não justifica e o único consumidor é o dbt
- Raw mantém `competencia` como STRING porque é a camada bruta — a conversão para DATE acontece no Staged
- BigQuery não suporta particionamento nativo por STRING, o que exigiu a conversão para DATE nas camadas dbt

## Consequências
- **Positivas:**
    - Consultas no Power BI leem apenas a partição e os clusters necessários
    - Custo de processamento reduzido conforme o histórico cresce
    - Configuração centralizada facilita manutenção
- **Negativas:**
    - Coluna `competencia` tem tipos diferentes entre Raw (STRING) e Staged/Marts (DATE)
    - Limite de 4 colunas no cluster_by pode exigir reavaliação futura se novos filtros surgirem