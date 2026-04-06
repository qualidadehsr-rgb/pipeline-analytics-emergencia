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
│   └── adr/          # Architecture Decision Records
├── ingestion/        # Scripts Python de ingestão
├── dbt/              # Projeto dbt - transformações SQL
└── README.md         # Apresentação do projeto
```
## Como Rodar
> Em construção — será atualizado após configuração do ambiente.

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