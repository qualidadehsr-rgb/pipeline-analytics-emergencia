# ADR-018 — Idempotência na Ingestão via Delete + Insert por Competência

## Contexto

Os três scripts de ingestão (`ingestao_atendimentos.py`, `ingestao_internacoes.py`, `ingestao_movimentacoes.py`) utilizavam `WRITE_APPEND` como estratégia de carga no BigQuery. Essa abordagem acumula linhas a cada execução, sem verificar o que já existe na tabela. Ao reprocessar uma competência — seja por correção de dados, complemento de campos vazios ou qualquer outro motivo operacional — os registros daquela competência seriam duplicados na camada Raw, propagando inconsistências para Staged e Marts.

A necessidade de corrigir os arquivos de maio/2026 antes da reingestão evidenciou o risco: sem idempotência, o pipeline não é seguro para reprocessamento.

## Decisão

Refatorar os três scripts de ingestão para adotar a estratégia **delete + insert por competência**:

1. Antes de inserir os dados, executa-se um `DELETE` na tabela Raw filtrando pela competência do arquivo
2. Em seguida, os dados são inseridos normalmente via `load_table_from_dataframe`

A implementação utiliza `cliente.query(...).result()` para garantir que o delete seja concluído antes do insert iniciar, evitando condição de corrida.

```python
# Exemplo aplicado nos três scripts
cliente.query(f"delete from {destino} where competencia = '{competencia}'").result()
job = cliente.load_table_from_dataframe(df.to_pandas(), destino, job_config=job_config)
job.result()
```

O `write_disposition` permanece como `WRITE_APPEND` — correto para o padrão de acumulação histórica — mas agora protegido pelo delete prévio por competência.

## Alternativas Consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| `WRITE_TRUNCATE` | Apaga toda a tabela, incluindo meses anteriores — incompatível com acúmulo histórico |
| Manter `WRITE_APPEND` | Não é idempotente — qualquer reingestão duplica os dados |
| Verificação prévia no BigQuery | Mais complexo, não elimina o risco de duplicata se a verificação falhar |

## Consequências

- O pipeline passa a ser seguro para reprocessamento: executar a ingestão de uma mesma competência N vezes sempre resulta no mesmo estado final na Raw
- Correções e complementos de arquivos podem ser feitos e reingeridos sem risco de duplicação
- A estratégia se aplica às três tabelas Raw: `atendimentos`, `internacoes`, `movimentacoes`
- Compatível com a futura carga histórica (~24 meses): cada competência pode ser reprocessada de forma independente e segura