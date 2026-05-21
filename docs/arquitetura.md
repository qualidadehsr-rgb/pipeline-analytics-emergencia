# Arquitetura do Pipeline — Emergência

## Visão Geral
O pipeline proposto automatiza o processo de coleta, tratamento e compilação 
dos dados da Emergência do hospital. O processo atual é realizado utilizando 
planilhas do excel para armazenar, tratar e compilar os resultados assistenciais, 
expondo aos riscos de erros na compilação, cálculos e perda da rastreabilidade. 
A proposta reduz o tempo de atualização desses indicadores que hoje é de 3 dias 
para menos de 1 dia. O fluxo dos dados será realizado através de camadas - Raw, 
Staged e Marts - antes de chegarem para consumo no BI.

## Stack Tecnológica

| Ferramenta | Versão | Papel |
|---|---|---|
| Python | 3.12 | Scripts para realizar a ingestão de 3 bases de dados (relatórios) mensais |
| Polars | 1.39.3 | Biblioteca Python para leitura dos arquivos |
| dbt Core | 1.11.6 | Responsável pelas transformações necessárias para qualidade dos dados e atendimento às regras de negócio |
| dbt-bigquery | 1.11.0 | Adaptador do dbt para o BigQuery |
| BigQuery | Gerenciado pelo GCP | Armazenamento dos dados de acordo com suas camadas |
| Cloud Storage | Gerenciado pelo GCP | Ponto de entrada dos arquivos mensais — substitui a pasta de rede local |
| Cloud Run Service | Gerenciado pelo GCP | Recebe eventos do Eventarc e executa o pipeline na nuvem — elimina dependência de máquina local |
| Cloud Run Job | Gerenciado pelo GCP | Executa dbt run + dbt test automaticamente após ingestão dos 3 arquivos mensais |
| Eventarc | Gerenciado pelo GCP | Detecta o upload de arquivos no Cloud Storage e dispara automaticamente o Cloud Run Service |
| GitHub | Cloud | Versionamento de código |
| Power BI | — | Visualização dos resultados |

## Camadas de Dados

### Raw
Camada de armazenamento dos dados brutos ingeridos dos relatórios dentro do 
projeto: `pipeline-analytics-emergencia`, dataset: `raw`. Guarda os dados como 
vem dos relatórios, sendo realizada apenas a conversão dos tipos para `string` 
em todas as colunas.
Cada tabela possui a coluna `competencia` (STRING, YYYY-MM) extraída do nome 
do arquivo, utilizada para controle de carga via WRITE_APPEND.

### Staged
Camada de transformação dos dados brutos lendo a camada raw. Localizados dentro 
do projeto: `pipeline-analytics-emergencia`, dataset: `staged`. Guarda as 
transformações realizadas nos dados em tabelas, os dados entram brutos e saem 
com tipagem correta, apenas as colunas necessárias para regras de negócio são 
materializadas em tabelas.
Todas as tabelas são particionadas por `competencia` (DATE), convertida de 
STRING para DATE via PARSE_DATE.

### Marts
Camada de consumo dos dados em indicadores de resultado assistencial. Localizados 
dentro do projeto: `pipeline-analytics-emergencia`, dataset: `marts`. Os modelos 
estão organizados em subpastas por domínio:
- `atendimentos/` — tabela `atendimentos_pa` com dados prontos para consumo do BI, 
  particionada por `competencia` (DATE) e clusterizada por `SERVICO`, `CONVENIO` 
  e `COR_CLASSIF`
- `ranking/` — tabela `ranking_especialidades` com indicador composto de desempenho 
  por especialidade, particionada por `competencia` (DATE), sem clusterização

Detalhes da decisão de reorganização no ADR-015.

## Fonte dos Dados

| Nome da Fonte | Formato | Frequência | Descrição |
|---|---|---|---|
| Relatório de atendimentos | xlsx | mensal | Relatório contendo os registros de atendimentos realizados na emergência |
| Relatório de internações | xlsx | mensal | Relatório contendo os registros de internações realizados no hospital |
| Relatório de movimentações | csv | mensal | Relatório contendo os registros de movimentações de leitos dos pacientes com origem de internação na emergência e nos leitos virtuais (extras) no hospital |

## Fluxo de Execução

1. Responsável pela operação faz upload dos 3 relatórios mensais no bucket 
   `pipeline-analytics-emergencia-ingestao` no Cloud Storage via navegador
2. Eventarc detecta automaticamente cada upload e dispara o Cloud Run Service
3. Cloud Run Service executa o script Python correspondente — lê o arquivo do 
   Cloud Storage, aplica tratamentos de LGPD, carrega no BigQuery Raw e registra 
   o log de execução. Antes da ingestão, verifica se já existem dados para 
   aquela competência na tabela correspondente — se existirem, o upload é 
   ignorado para evitar duplicação
4. Após cada ingestão, o Cloud Run Service verifica se as 3 tabelas Raw já 
   possuem dados para a mesma competência (YYYY-MM). Somente quando as 3 
   estiverem carregadas, um arquivo de lock é criado no Cloud Storage para 
   garantir que apenas uma instância acione o Cloud Run Job `dbt-pipeline-job` 
   via API do Google Cloud
5. dbt executa as transformações — Raw → Staged → Marts
6. Responsável técnico acessa a interface de curadoria para revisar os casos 
   suspeitos de conversão e registrar as decisões na tabela `curadoria_conversao`
7. Após finalização da curadoria é disparado re-run do dbt para atualização das tabelas
8. Power BI consome a camada Marts atualizada
9. Limpeza de locks no Cloud Storage a cada 2 meses — procedimento no RUNBOOK

## Governança e Segurança

### Tratamento de Dados Sensíveis
Os dados sensíveis são excluídos já na leitura dos dados antes mesmo de 
carregá-los à nuvem. São excluídos dados de identificação do paciente como: 
nome completo, data de nascimento e endereço. Detalhes completos no ADR-002.

### Controle de Acesso e Credenciais
O pipeline é executado no Cloud Run com autenticação via Application Default 
Credentials (ADC) — sem arquivos de chave locais. Detalhes completos no ADR-003.
O Power BI se conecta via service account `powerbi-leitura-marts` com os papéis 
BigQuery Data Viewer e BigQuery Job User — acesso restrito a leitura e execução 
de consultas na camada Marts. A conexão é feita via chave JSON da service account.
Detalhes completos no ADR-014.

### Curadoria de Dados
Casos suspeitos de conversão identificados pelo pipeline são revisados 
mensalmente pelo responsável técnico através de interface dedicada. As decisões 
de confirmação ou descarte são registradas na tabela `curadoria_conversao` no 
BigQuery com rastreabilidade por competência. Detalhes completos no ADR-006.

### Versionamento e Rastreabilidade
Os códigos são versionados no GitHub e a rastreabilidade através de logs de 
execução registrados no BigQuery a cada execução do pipeline.

## Monitoramento

**Implementado:**
- Logs de execução nos scripts Python — registram quantidade de linhas 
  carregadas, duplicatas removidas e erros
- 41 testes de qualidade no dbt — validação de chaves únicas, valores nulos, 
  valores esperados e teste singular para movimentações
- Lock por competência no Cloud Storage — evita acionamento múltiplo do dbt 
  Job em uploads simultâneos
- Proteção contra duplicação na Raw — verifica existência de dados antes da 
  ingestão para evitar re-upload acidental
- Alertas automáticos via Cloud Monitoring em caso de falha na execução
- Limpeza manual de locks a cada 2 meses — procedimento documentado no RUNBOOK

**Planejado:**
- Testes de negócio no dbt (9 testes) — validação de regras como permanência 
  não negativa, sequência temporal de eventos e exclusividade entre flags. 
  Detalhes no plano analítico
- Observabilidade analítica — painel de saúde do pipeline com monitoramento 
  de volume, detecção de anomalias e alertas de atraso na ingestão. 
  Detalhes no plano analítico

## Escalabilidade
A arquitetura em camadas permite adicionar novas fontes de dados e indicadores 
sem impactar o fluxo existente. Novos relatórios podem ser incorporados criando 
novos scripts de ingestão e modelos dbt seguindo os padrões já estabelecidos.

Expansões previstas no plano analítico:
- Fase 2: exames laboratoriais, exames de imagem e prescrição de medicamentos
- Fase 3: cirurgias realizadas e dados financeiros

O consumo no Power BI está limitado ao acesso atual — um link compartilhado 
com a diretoria — sem perspectiva de expansão de usuários no curto prazo.