# pipeline-analytics-emergencia

## Contexto
A direção do hospital tem no Pronto Atendimento uma de suas unidades de negócio mais importantes por ser uma das portas de entrada aos serviços do hospital. Assim sendo é necessário o acompanhamento dos resultados dessa unidade estratégica. Um dos indicadores que compõe esse resultado é a taxa de conversão dos atendimentos (consultas) em internações. Esses indicadores norteiam as tomadas de decisões sobre recursos humanos, qualidade e segurança assistencial.

## Problema
Atualmente o processo de coleta e tratamento dos dados, consolidação e disponibilização desses indicadores é trabalhoso, arriscado e demorado. São 3 relatórios convertidos em excel: atendimentos, internações e movimentações. É necessário realizar tratamento em cada uma das planilhas para depois fazer cruzamentos e identificar quais atendimentos se converteram em internações;
Após esse processo, faz-se necessário uma revisão onde ainda é possível encontrar inconsistências relacionadas ao cadastro de dados. Essas inconsistências são tratadas nas próprias planilhas, porém no sistema hospitalar (MV) não são feitas correções ou sinalizado ao gestor competente;
Ao final esse processo leva em torno de 2 dias para conclusão, para somente então disponibilizar uma base de dados limpa para consumo e publicação no Power BI.

## Solução
Para melhoria do processo, foi desenvolvida uma arquitetura que cobre todo o ciclo de vida dos dados. Desde a coleta, ingestão, armazenamento, processamento (tratamento) e disponibilização dos dados;
Essa solução define responsabilidades e entregas em cada uma das etapas até a disponibilização dos resultados. Melhora o controle e a rastreabilidade dos dados, aplica métodos e ferramentas modernas de engenharia e análise de dados, garante um resultado com maior confiabilidade e menor tempo de compilação e atualização mensal.

## Impacto
- Aplicação de conceitos de governança, segurança e qualidade dos dados;
- Redução do tempo de compilação e atualização dos resultados (esperado < 1 dia);
- Processos auditáveis sobre o tratamento aplicados aos dados;
- Formalização e documentação de conceitos e métricas aplicadas.

## Estrutura do Projeto
```
pipeline-analytics-emergencia/
├── docs/             # Documentação do projeto
│   ├── adr/          # Architecture Decision Records
│   ├── arquitetura.md # Arquitetura detalhada do pipeline
│   ├── plano-analitico.md # Plano analítico do painel de emergência
│   └── RUNBOOK.md    # Procedimentos operacionais de deploy
├── ingestion/        # Scripts Python de ingestão
├── curadoria/        # Serviço Flask da interface de curadoria
├── dbt/              # Projeto dbt - transformações SQL
├── infra/            # Scripts de infraestrutura
│   └── bigquery/     # Scripts SQL de criação de tabelas no BigQuery
└── README.md         # Apresentação do projeto
```
## Como Rodar

### Pré-requisitos
- Acesso ao bucket `pipeline-analytics-emergencia-ingestao` no Cloud Storage

### Execução mensal
1. Baixar os 3 relatórios do sistema hospitalar (atendimentos, internações, movimentações)
2. Renomear os arquivos seguindo o padrão: `atendimentos_YYYY_MM.csv`, `internacoes_YYYY_MM.csv`, `movimentacoes_YYYY_MM.csv`
3. Remover a coluna de nome do paciente do arquivo de movimentações
4. Fazer upload dos 3 arquivos no bucket `pipeline-analytics-emergencia-ingestao` via console do GCP
5. O pipeline dispara automaticamente — nenhuma ação técnica adicional é necessária
6. Acessar a interface de curadoria via navegador para revisar casos suspeitos
   e inconsistências identificadas pelos testes de negócio
7. Verificar o Power BI com os resultados atualizados

### Desenvolvimento local
```
cd dbt/pipeline_analytics
dbt run
dbt test    
```

## Conventional Commits
| Prefixo | Quando usar |
|---|---|
|`chore` | Configuração, estrutura, sem código de negócio |
|`feat` | Nova funcionalidade |
|`fix` | Correção de bug |
|`docs` | Documentação |
|`refactor` | Melhoria de código sem mudar comportamento |

Exemplo:
```
git add .
git commit -m "docs: adiciona ADR-001 arquitetura geral e ADR-002 LGPD"
git push
```

## Documentação
- [ADR-001 — Arquitetura Geral](docs/adr/ADR-001-arquitetura-geral.md)
- [ADR-002 — LGPD e Dados Sensíveis](docs/adr/ADR-002-lgpd-dados-sensiveis.md)
- [ADR-003 — Autenticação GCP](docs/adr/ADR-003-autenticacao-gcp.md)
- [ADR-004 — Categoria Outros Serviço](docs/adr/ADR-004-categoria-outros-servico.md)
- [ADR-005 — Migração da Ingestão para Cloud Storage + Cloud Run](docs/adr/ADR-005-migracao-ingestao-cloud.md)
- [ADR-006 — Interface de Curadoria de Suspeitos de Conversão](docs/adr/ADR-006-curadoria-suspeitos-conversao.md)
- [ADR-007 — Migração de Cloud Run Job para Service com Eventarc](docs/adr/ADR-007-cloud-run-service-eventarc.md)
- [ADR-008 — Verificação de Competência e Acionamento do dbt](docs/adr/ADR-008-verificacao-competencia-acionamento-dbt.md)
- [ADR-009 — Particionamento e Clusterização no BigQuery](docs/adr/ADR-009-particionamento-clusterizacao.md)
- [ADR-010 — Lock para Acionamento Único do dbt Job](docs/adr/ADR-010-lock-acionamento-unico-dbt-job.md)
- [ADR-011 — Proteção contra Duplicação na Raw](docs/adr/ADR-011-protecao-duplicacao-raw.md)
- [ADR-012 — Interface de Curadoria Human-in-the-Loop](docs/adr/ADR-012-interface-curadoria-human-in-the-loop.md)
- [ADR-013 — Integração Curadoria com Modelo dbt](docs/adr/ADR-013-integracao-curadoria-modelo-dbt.md)
- [ADR-014 — Alertas Técnicos via Cloud Monitoring](docs/adr/ADR-014-alertas-tecnicos-cloud-monitoring.md)
- [ADR-015 — Reorganização da Marts em Subpastas](docs/adr/ADR-015-reorganizacao-marts-subpastas.md)
- [ADR-016 — Fixação de Versões no Dockerfile](docs/adr/ADR-016-fixacao-versoes-dockerfile.md)
- [ADR-017 — Expansão do Escopo da Curadoria para Inconsistências de Qualidade](docs/adr/ADR-017-expansao-escopo-curadoria.md)
- [ADR-018 — Idempotência na Ingestão via Delete + Insert por Competência](docs/adr/ADR-018-idempotencia-ingestao-delete-insert.md)
- [ADR-019 — Autenticação da Interface de Curadoria via IAP](docs/adr/ADR-019-autenticacao-interface-curadoria-IAP.md)