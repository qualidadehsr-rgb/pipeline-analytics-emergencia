# ADR-001 — Arquitetura Geral do Pipeline

## Contexto
A diretoria do hospital precisa ter acesso mensal a indicadores de performance do Pronto Atendimento (Emergência) de forma confiável e em tempo hábil para análise. Atualmente esse processo leva em torno de 3 dias para consolidação dos dados e + 1 dia para conferência e publicação no painel de visualização (Power BI). O processo de consolidação é extremamente moroso e perigoso pois requer atenção e concentração dedicada. Isso pode levantar questionamentos sobre o resultado final além de exposição a erros devido ao processo de tratamento e manipulação dos dados em planilhas excel.

## Decisão
| Processo | Decisão |
|---|---|
| Camadas | Raw → Staged → Marts |
| Ingestão | Python + ADC |
| Armazenamento | BigQuery |
| Transformação | dbt Core |
| Agendamento | Automático via Eventarc + verificação de competência |
| Visualização | Power BI |
| Documentação | README, ADRs, dbt docs |
| Rastreabilidade | log de carga |
| Recarga | WRITE_APPEND com particionamento por competência |
| Particionamento | competencia (DATE) no Staged/Marts + clusterização na Marts |

## Justificativa
Decidi pelo armazenamento dos dados em BigQuery, pois o custo zero com o limite oferecido atende por muitos anos aos dados que serão guardados. Também por ser um workload analítico, facilita o consumo do dataset final pela ferramenta de BI para análises;
Para transformação dos dados optei pelo dbt Core por ser opensource e pelo fato de não necessitar de agendamentos para realizar as transformações necessárias, uma vez que os dados terão atualizações mensais;
Para visualização final do resultado optei pelo Power BI pelo fato de ser a ferramenta atual de visualização pela diretoria, e também por não requerer vários acessos (apenas a diretoria utiliza);
Por fim, para conexão com o GCP decidi pela chave gerenciada na própria GCP. Uma vez que atuo em ambientes distintos (presencial e home office), isso facilita conexão não sendo necessário gerar várias chaves para conexões e ter uma proliferação de chaves sem controle.

## Consequências
- **Positivas:**
    - **Rastreabilidade:** Armazenamento seguro dos dados analisados;
    - **Organização:** Responsabilidades definidas em cada etapa;
    - **Otimização:** Redução do tempo de atualização dos resultados mensais;
    - **Continuidade:** Registro do processo e conhecimento gerado;
    - **Qualidade:** Aumento da confiabilidade nos resultados finais.

- **Negativas:**
    - Atualização manual das transformações via dbt Core;
    - Monitoramento constante do processo por estar utilizando serviços em nuvem (Custos, LGPD)