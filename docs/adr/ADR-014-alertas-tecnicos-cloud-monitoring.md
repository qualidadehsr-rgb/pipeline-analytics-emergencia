# ADR-014 — Alertas Técnicos via Cloud Monitoring

**Data:** 2026-05-14  
**Status:** Implementada

## Contexto

O pipeline opera de forma automatizada (Eventarc → Cloud Run Service → Cloud Run Job), mas não havia nenhum mecanismo de notificação quando falhas ocorriam. Uma falha na ingestão ou no dbt poderia passar despercebida por dias até alguém verificar manualmente os logs.

## Decisão

Configurar alertas no Google Cloud Monitoring para notificar por e-mail quando componentes críticos do pipeline falharem.

### Alertas configurados

| Alerta | Recurso | Métrica | Filtros | Severidade |
|--------|---------|---------|---------|------------|
| Alerta - Falha dbt Pipeline Job | Cloud Run Job | Completed exit result and task attempts | job_name = dbt-pipeline-job, result = failed | Critical |
| Alerta - Falha Ingestão Pipeline Service | Cloud Run Revision | Request Count | service_name = ingestao-pipeline-emergencia-service, response_code_class = 5xx | Critical |

### Canal de notificação

- **Tipo:** E-mail
- **Nome:** Alerta Pipeline Emergencia
- **Notificação de encerramento:** ativada (notifica também quando o incidente é resolvido)

## Justificativa

- **Cloud Monitoring nativo:** custo zero dentro do free tier do GCP, sem necessidade de ferramentas externas
- **E-mail como canal:** simples, acessível de qualquer dispositivo, não requer instalação de apps adicionais
- **Dois alertas separados:** falha na ingestão e falha no dbt têm causas e responsáveis diferentes, alertas separados facilitam o diagnóstico
- **Filtro por nome do serviço/job:** evita alertas falsos de outros recursos do projeto
- **Severidade Critical:** qualquer falha no pipeline impacta diretamente a geração dos indicadores para a diretoria

## Consequências

- Responsável técnico recebe e-mail imediato quando ingestão ou dbt falharem
- Possibilidade futura de adicionar canais redundantes (Slack, SMS) conforme o projeto escale
- Alertas adicionais podem ser criados para novos componentes (ex: Cloud Run Service da curadoria)
- O custo real é zero — alertas básicos estão cobertos pelo free tier do Cloud Monitoring