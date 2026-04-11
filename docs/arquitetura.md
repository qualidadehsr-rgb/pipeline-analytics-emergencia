# Arquitetura do Pipeline — Emergência

## Visão Geral
O pipeline proposto automatiza o processo de coleta, tratamento e compilação dos dados da Emergência do hospital. O processo atual é realizado utilizando planilhas do excel para armazenar, tratar e compilar os resultados assistenciais, expondo aos riscos de erros na compilação, cálculos e perda da rastreabilidade. A proposta reduz o tempo de atualização desses indicadores que hoje é de 3 dias para menos de 1 dia. O fluxo dos dados será realizado através de camadas - Raw, Staged e Marts - antes de chegarem para consumo no BI.

## Stack Tecnológica

| Ferramenta | Versão | Papel |
|---|---|---|
| Python | 3.13 | Scripts para realizar a ingestão de 3 bases de dados (relatórios) mensais |
| Polars | 1.39.3 | Biblioteca Python para leitura dos arquivos |
| dbt Core | 1.11.8 | Responsável pelas transformações necessárias para qualidade dos dados e atendimento às regras de negócio |
| BigQuery | Gerenciado pelo GCP | Armazenamento dos dados de acordo com suas camadas |
| GitHub | Cloud | Versionamento de código |
| Power BI | ??? | Visualização dos resultados |

## Camadas de Dados

### Raw
Camada de armazenamento dos dados brutos ingeridos dos relatórios dentro do projeto: `pipeline-analytics-emergencia`, dataset: `raw`. Guarda os dados como vem dos relatórios, sendo realizada apenas a conversão dos tipos para `string`em todas as colunas.

### Staged
Camada de transformação dos dados brutos lendo a camada raw. Localizados dentro do projeto: `pipeline-analytics-emergencia`, dataset: `staged`. Guarda as transformações realizadas nos dados em tabelas, os dados entram brutos e saem com tipagem correta, apenas as colunas necessárias para regras de negócio são materializadas em tabelas.

### Marts
Camada de consumo dos dados em indicadores de resultado assistencial. Localizados dentro do projeto: `pipeline-analytics-emergencia`, dataset: `marts`. Guarda as transformações realizadas nos dados em uma única tabela, os dados entram transformados e saem prontos para consumo do BI.

## Fonte dos Dados

| Nome da Fonte | Formato | Frequência | Descrição |
|---|---|---|---|
| Relatório de atendimentos | xlsx | mensal |Relatório contendo os registros de atendimentos realizados na emergência |
| Relatório de internações | xlsx | mensal |Relatório contendo os registros de internações realizados no hospital |
| Relatório de movimentações | csv | mensal |Relatório contendo os registros de movimentações de leitos dos pacientes com origem de internação na emergência e nos leitos virtuais (extras) no hospital |

## Fluxo de Execução
> Em construção — será atualizado após finalização do pipeline completo.

## Governança e Segurança

### Tratamento de Dados Sensíveis
Os dados sensíveis são excluídos já na leitura dos dados antes mesmo de carregá-los à nuvem. São excluídos dados de identificação do paciente como: nome completo, data de nascimento e endereço. Detalhes completos no ADR-002.

### Controle de Acesso e Credenciais
O gerenciamento das credenciais de acesso ao armazenamento no GCP é realizado localmente através de chave em arquivo JSON.
O Power BI terá acesso mínimo apenas a leitura e jobs na camada Mart.

### Versionamento e Rastreabilidade
Os códigos são versionados no GitHub e a rastreabilidade através de logs de execução.

## Monitoramento

**Implementado:**
- Logs de execução nos scripts Python — registram quantidade de linhas carregadas, duplicatas removidas e erros.

**Planejado:**
- Testes de qualidade de dados no dbt — validação de chaves únicas, valores nulos, valores esperados.

## Escalabilidade
A arquitetura em camadas permite adicionar novas fontes de dados e indicadores sem impactar o fluxo existente. Novos relatórios podem ser incorporados criando novos scripts de ingestão e modelos dbt seguindo os padrões já estabelecidos.

O consumo no Power BI está limitado ao acesso atual — um link compartilhado com a diretoria — sem perspectiva de expansão de usuários no curto prazo.
