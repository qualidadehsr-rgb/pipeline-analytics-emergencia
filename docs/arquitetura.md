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
| dbt Core | 1.11.9 | Responsável pelas transformações necessárias para qualidade dos dados e atendimento às regras de negócio |
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
dentro do projeto: `pipeline-analytics-emergencia`, dataset: `marts`. Guarda as 
transformações realizadas nos dados em uma única tabela, os dados entram 
transformados e saem prontos para consumo do BI.
A tabela é particionada por `competencia` (DATE) e clusterizada por `SERVICO`, 
`CONVENIO` e `COR_CLASSIF` para otimizar consultas do Power BI.

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
   o log de execução
4. Após cada ingestão, o Cloud Run Service verifica se as 3 tabelas Raw já 
   possuem dados para a mesma competência (YYYY-MM). Somente quando as 3 
   estiverem carregadas, o Cloud Run Job `dbt-pipeline-job` é acionado 
   automaticamente via API do Google Cloud
5. dbt executa as transformações — Raw → Staged → Marts
6. Responsável técnico acessa a interface de curadoria para revisar os casos 
   suspeitos de conversão e registrar as decisões na tabela `curadoria_conversao`
7. Power BI consome a camada Marts atualizada

## Governança e Segurança

### Tratamento de Dados Sensíveis
Os dados sensíveis são excluídos já na leitura dos dados antes mesmo de 
carregá-los à nuvem. São excluídos dados de identificação do paciente como: 
nome completo, data de nascimento e endereço. Detalhes completos no ADR-002.

### Controle de Acesso e Credenciais
O pipeline é executado no Cloud Run com autenticação via Application Default 
Credentials (ADC) — sem arquivos de chave locais. Detalhes completos no ADR-003.
O Power BI terá acesso mínimo apenas a leitura e jobs na camada Mart.

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
- 25 testes de qualidade no dbt — validação de chaves únicas, valores nulos, 
  valores esperados e teste singular para movimentações

**Planejado:**
- Alertas automáticos via Cloud Monitoring em caso de falha na execução
- Notificações ao responsável técnico quando testes dbt falham
- Notificações ao responsável do processo quando existem casos suspeitos de conversão

## Escalabilidade
A arquitetura em camadas permite adicionar novas fontes de dados e indicadores 
sem impactar o fluxo existente. Novos relatórios podem ser incorporados criando 
novos scripts de ingestão e modelos dbt seguindo os padrões já estabelecidos.

O consumo no Power BI está limitado ao acesso atual — um link compartilhado 
com a diretoria — sem perspectiva de expansão de usuários no curto prazo.