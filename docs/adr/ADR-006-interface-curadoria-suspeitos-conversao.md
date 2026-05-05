# ADR-006 — Interface de Curadoria de Suspeitos de Conversão

## Contexto
O pipeline identifica casos de possível conversão com erro de cadastro 
de origem no sistema MV (fl_suspeito_conversao = 1). Esses casos precisam 
de revisão humana antes de serem contabilizados como conversões válidas. 
Não existe hoje nenhum mecanismo formal para registrar essa decisão — 
ela era feita manualmente em planilha Excel sem rastreabilidade.

## Decisão
Criar uma interface simples no navegador, hospedada no Cloud Run, que 
exibe os casos suspeitos do mês e permite confirmar ou descartar cada um. 
As decisões são gravadas numa tabela curadoria_conversao no BigQuery. 
O dbt lê essa tabela e promove os casos confirmados para fl_conversao = 1.

## Justificativa
- Formaliza e rastreia uma decisão que hoje é informal e sem registro
- A decisão de confirmação pertence ao responsável técnico — o pipeline 
  detecta, o humano decide
- Gravação direta no BigQuery elimina planilhas intermediárias
- Hospedagem no Cloud Run mantém tudo na mesma infraestrutura já definida

## Consequências
- Positivas:
  - Decisões de curadoria auditáveis e rastreáveis por competência
  - Casos suspeitos visíveis para a diretoria no Power BI
  - Elimina revisão manual em planilha Excel
- Negativas:
  - Requer desenvolvimento da interface e da tabela de curadoria
  - Adiciona uma etapa no fechamento mensal — revisão dos suspeitos 
    antes de finalizar o pipeline