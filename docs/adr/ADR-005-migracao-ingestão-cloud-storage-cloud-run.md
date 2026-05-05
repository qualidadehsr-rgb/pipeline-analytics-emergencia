# ADR-005 — Migração da Ingestão para Cloud Storage + Cloud Run

## Contexto
O pipeline de ingestão depende da máquina local do responsável técnico, 
do seu ambiente Python configurado e do seu conhecimento para execução. 
Isso cria um ponto único de falha humana — se o responsável não estiver 
disponível, o pipeline para. Não há continuidade operacional garantida.

## Decisão
Migrar o script de ingestão para o Cloud Run e substituir a pasta de rede 
local pelo Cloud Storage como ponto de entrada dos arquivos.

## Justificativa
- Cloud Storage permite que qualquer pessoa da equipe faça upload dos 
  arquivos pelo navegador, sem instalar nada
- Cloud Run executa o pipeline na nuvem via URL, sem depender de máquina 
  ou ambiente local
- Ambos operam dentro da cota gratuita do GCP dado o volume mensal do pipeline
- O setor já possui conta GCP ativa com outros projetos, eliminando 
  barreiras de aprovação e configuração

## Consequências
- Positivas:
  - Qualquer pessoa da equipe consegue operar o pipeline sem conhecimento técnico
  - Código versionado no GitHub — não depende de máquina específica
  - Pipeline continua funcionando independente de mudanças na equipe
- Negativas:
  - Requer configuração inicial do Cloud Run e Cloud Storage
  - Equipe precisa aprender a usar o Cloud Storage para upload dos arquivos