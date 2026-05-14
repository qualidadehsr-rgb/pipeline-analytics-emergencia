# ADR-012 — Interface de Curadoria Human-in-the-Loop

**Data:** 2026-05-14  
**Status:** Implementada

## Contexto

O modelo `atendimentos_pa` identifica casos suspeitos de conversão (`fl_suspeito_conversao = 1`) — atendimentos de emergência que não foram vinculados automaticamente a uma internação, mas cujo motivo de alta sugere que houve internação. Esses casos precisam de validação humana no sistema MV antes de serem confirmados ou descartados.

## Decisão

Criar um Cloud Run Service separado (`curadoria-pipeline-emergencia-service`) com interface web Flask para o responsável operacional revisar os casos suspeitos e registrar suas decisões.

### Componentes implementados

- **Back-end:** Flask com 4 rotas (`/`, `/decidir`, `/finalizar`, `/health`)
- **Front-end:** HTML com CSS embutido, JavaScript para validação e exibição condicional de campos
- **Armazenamento:** Dataset `curadoria` com tabela `curadoria_conversao` no BigQuery
- **Deploy:** Cloud Run Service com imagem Docker no Artifact Registry

### Estrutura da tabela `curadoria_conversao`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| CD_ATENDIMENTO | STRING | Atendimento da emergência (suspeito) |
| decisao | STRING | "confirmado" ou "descartado" |
| competencia | STRING | Mês de referência |
| atend_internacao | STRING | Atendimento de internação (preenchido se confirmado) |
| destino | STRING | Leito de destino |
| unidade | STRING | Unidade de destino |
| tipo | STRING | UTI ou Unidade de Internação |
| decidido_por | STRING | Nome do responsável pela decisão |
| decidido_em | TIMESTAMP | Data e hora da decisão |

## Justificativa

- **Serviço separado da ingestão:** responsabilidades distintas (automática vs interativa), ciclos de deploy independentes, sem risco de impacto cruzado
- **Flask:** biblioteca Python leve, equipe já utiliza Python no projeto, curva de aprendizado mínima
- **Tabela dedicada no BigQuery:** decisões humanas ficam separadas dos dados brutos e transformados, permitindo auditoria completa
- **Validação no front-end:** campos obrigatórios quando a decisão é "confirmado" impedem gravação de dados incompletos
- **Seletor de competências:** necessário para carga histórica, onde múltiplos meses precisam de curadoria

## Consequências

- O modelo `atendimentos_pa` no dbt precisará ser atualizado para consultar a tabela `curadoria_conversao` e incorporar as decisões (confirmados viram conversão, descartados deixam de ser suspeitos)
- Após a curadoria, o botão "Finalizar" dispara o Cloud Run Job do dbt para reprocessar os dados
- A URL do serviço precisa ser salva como favorito no navegador do responsável operacional
- O serviço usa `--allow-unauthenticated` — qualquer pessoa com a URL pode acessar (aceitável por estar em rede interna; autenticação pode ser adicionada futuramente)