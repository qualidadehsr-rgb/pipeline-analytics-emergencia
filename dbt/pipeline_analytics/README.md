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
│   └── dim_leitos.csv
├── macros/               # Macros reutilizáveis
└── dbt_project.yml       # Configuração do projeto
```

## Camadas

| Camada | Dataset BigQuery | Descrição |
|---|---|---|
| Staging | `staged` | Tipagem correta, colunas necessárias, sem regras de negócio |
| Marts | `marts` | Indicadores finais com flags de negócio prontos para o BI |

## Indicadores Gerados

| Flag | Descrição |
|---|---|
| `fl_conversao` | Atendimento convertido em internação |
| `fl_suspeito_conversao` | Possível conversão com erro de cadastro de origem |
| `fl_retorno_48h` | Paciente retornou ao PA em menos de 48h |
| `fl_evasao` | Paciente evadiu sem alta médica |

## Comandos

```bash
# Executar todos os modelos
dbt run

# Executar só os modelos de staging
dbt run --select staging

# Executar só os modelos de marts
dbt run --select marts

# Rodar os testes
dbt test

# Gerar documentação
dbt docs generate
dbt docs serve
```

## Configuração
O projeto utiliza macro `generate_schema_name` para roteamento correto 
dos datasets `staged` e `marts` no BigQuery.
Detalhes de arquitetura em [docs/arquitetura.md](../docs/arquitetura.md).