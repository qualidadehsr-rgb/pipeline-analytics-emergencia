# ADR-004 — Uso da categoria 'OUTROS' para especialidades não contratadas

## Contexto
Na emergência existem especialidades contratadas para prestação de atendimento nas 24h. Eventualmente faz-se necessário avaliação por parte de algum especialista que não esteja contemplado nesse rol contratado. Esses profissionais realizam atendimento (avaliação de parecer) mediante solicitação, e registram no sistema sua especialidade e atendimento realizado ao paciente. Isso gera uma lista de especialidades que "não fazem" parte dos serviços contratados pelo hospital para atendimento na emergência.

## Decisão
Para essas especialidades fora do contrato, usei a categoria `OUTROS` para agrupa-los na coluna `SERVICO` durante as análises.

## Justificativa
- Para evitar poluição durante a visualização das especialidades no dashboard;
- Facilitar o acompanhamento de solicitação de pareceres na emergência.

## Consequências
- **Positivas:**
    - Melhor visualização no BI
    
- **Negativas:**
    - Necessidade de revisão das especialidades que estão entrando nessa categoria, pois eventualmente pode haver cadastro de especialidades sinônimas, ausência ou erro de digitação.