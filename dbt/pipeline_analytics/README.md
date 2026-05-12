# dbt — pipeline-analytics-emergencia

## Sobre
Projeto dbt responsável pelas transformações dos dados da Emergência do hospital.
Lê os dados brutos do BigQuery Raw e os transforma em indicadores prontos para 
consumo no Power BI.

## Estrutura
```
dbt/
├── models/
│   ├── staging/          # Modelos de limpeza e tipagem — leem do Raw
│   │   ├── stg_atendimentos.sql
│   │   ├── stg_internacoes.sql
│   │   └── stg_movimentacoes.sql
│   └── marts/            # Modelos de negócio — leem do Staged
│       └── atendimentos_pa.sql
├── seeds/                # Dados de referência estáticos
│   └── dim_leitos.csv    # Cadastro de referência para as movimentações de leitos no hospital
├── macros/               # Macros reutilizáveis
└── dbt_project.yml       # Configuração do projeto
```

## Camadas

| Camada | Dataset BigQuery | Descrição |
|---|---|---|
| Staging | `staged` | Tipagem correta, colunas necessárias, sem regras de negócio |
| Marts | `marts` | Indicadores finais com flags de negócio prontos para o BI |

## Particionamento e Clusterização

Todas as tabelas staged e marts são particionadas por `competencia` (DATE), 
coluna extraída do nome do arquivo na ingestão (padrão: `tipo_YYYY_MM.csv`) 
e convertida de STRING para DATE no staged.

A tabela `marts.atendimentos_pa` possui clusterização adicional por:
- `SERVICO` — agrupamento corrigido de especialidades
- `CONVENIO` — tipo de convênio do paciente
- `COR_CLASSIF` — classificação de risco

Configuração centralizada no `dbt_project.yml`.

## Indicadores Gerados

| Flag | Descrição |
|---|---|
| `fl_conversao` | Atendimento convertido em internação |
| `fl_suspeito_conversao` | Possível conversão com erro de cadastro de origem |
| `fl_retorno_48h` | Paciente retornou ao PA em menos de 48h |
| `fl_evasao` | Paciente evadiu sem alta médica |

## Comandos

Em produção, o dbt é executado automaticamente via Cloud Run Job (`dbt-pipeline-job`) 
após a ingestão dos 3 arquivos mensais. Os comandos abaixo servem como referência 
para desenvolvimento local:

```bash
dbt run                       # Executar todos os modelos
dbt run --select staging      # Executar só staging
dbt run --select marts        # Executar só marts
dbt test                      # Rodar os testes
dbt docs generate && dbt docs serve  # Documentação
```

## Testes

O projeto conta com 25 testes automatizados:

- `not_null` e `unique` nos campos-chave de staging e marts
- `not_null` em `competencia` nas 4 tabelas (staged e marts)
- `accepted_values` nas flags binárias (0 ou 1)
- Teste singular `movimentacoes_nulos_invalidos` — valida que nenhuma linha com número de atendimento válido possui `Hora` ou `Destino` nulos

## Configuração
O projeto utiliza macro `generate_schema_name` para roteamento correto 
dos datasets `staged` e `marts` no BigQuery.
Detalhes de arquitetura em [docs/arquitetura.md](../docs/arquitetura.md).