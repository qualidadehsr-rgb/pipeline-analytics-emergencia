# Plano Analítico — Emergência

**Data:** 2026-05-14  
**Status:** Em construção

## Objetivo

Transformar os dados operacionais da emergência do hospital em análises 
que suportem decisões da diretoria. O plano evolui em fases — da entrega 
imediata com os dados disponíveis até a incorporação de novas fontes que 
ampliam o poder analítico.

## Estrutura de Páginas do Painel

### Página 1 — Visão Geral
**Já existe.** KPIs principais: média de atendimentos, taxa de conversão, 
permanência, espera médica, retorno 48h, taxa de evasão. Gráfico de tendência 
mensal com número de atendimentos e taxa de conversão. Filtros por período 
e especialidade.

**Perguntas que responde:**
- Como estamos performando este mês comparado aos anteriores?
- A demanda está crescendo ou caindo?

### Página 2 — Jornada do Paciente
Funil completo do fluxo do paciente desde o totem até a alta, com tempo 
médio em cada etapa: espera pra classificação, classificação, espera pra 
recepção, cadastro, espera pro médico, atendimento médico, pós-atendimento 
até a alta. Identificação de abandonos (pacientes que não completaram o ciclo).

**Perguntas que responde:**
- Onde está o gargalo dos pacientes que ultrapassam 6h de permanência?
- Em qual etapa o tempo é consumido?
- Quantos pacientes desistiram antes de completar o atendimento?
- O que aconteceu com pacientes sem registro de alta?

**Filtros:** especialidade, turno, convênio, classificação de risco, CID

**Campos necessários (não estão na marts hoje):** CHAMADA_CLASSIFICACAO, 
INICIO_CLASSIFICACAO, CHAMADA_CAD_RECEP, DH_CADASTRO_RECEPCAO, FIM_CAD_RECEP, 
DH_ATEND_MEDICO. Novo campo calculado: turno (derivado do horário do totem).

### Página 3 — Perfil do Paciente
Características demográficas: pirâmide etária, distribuição por sexo, mapa 
de demanda por localidade (CEP/cidade/UF), CIDs mais frequentes. Cruzamento 
de perfil com indicadores (ex: faixa etária × taxa de conversão).

**Perguntas que responde:**
- Qual o perfil dos pacientes que mais procuram a emergência?
- De onde vem a demanda geograficamente?
- Existe relação entre perfil demográfico e desfecho?

**Novo campo calculado:** faixa etária (derivado da idade).

### Página 4 — Retornos e Evasões
Análise de pacientes que retornaram em 48h: motivo do retorno, se internaram 
na segunda vez, comparação do CID entre as visitas. Análise de evasões: perfil 
de quem evade, se retornou depois, em quanto tempo, pelo mesmo motivo. 
Pacientes com classificação grave que evadiram.

**Perguntas que responde:**
- Por que os pacientes que retornaram em 48h não internaram na primeira consulta?
- Quem evadiu retornou? Em quanto tempo? Pelo mesmo motivo?
- Pacientes graves estão evadindo? Estão retornando?

### Página 5 — Conversão e Gravidade
Análise aprofundada da conversão: perfil de quem converte por classificação 
de risco, especialidade, CID, convênio. Destino da internação (UTI vs enfermaria) 
por gravidade. Pacientes graves que não internaram.

**Perguntas que responde:**
- Pacientes com classificações mais graves estão internando? Onde?
- As especialidades estão performando em conversões como esperado?
- Existe padrão nos CIDs que mais convertem?

### Página 6 — Performance das Especialidades
Ranking de desempenho das especialidades usando indicador composto ponderado. 
Drill-down por indicador para identificar onde cada especialidade perde pontos.

| Indicador | Peso |
|---|---|
| Taxa de conversão | 25 |
| Tempo médio de atendimento | 25 |
| Taxa de altas dentro da meta (6h) | 20 |
| Taxa de retorno 48h | 20 |
| Taxa de evasão | 10 |
| **Total** | **100** |

**Perguntas que responde:**
- Qual especialidade está performando melhor/pior?
- No quê exatamente a especialidade com baixa pontuação está falhando?
- A performance está melhorando ou piorando ao longo dos meses?

### Página 7 — Previsão de Demanda
Projeção de demanda de atendimentos para próximas semanas/meses usando 
séries temporais. Previsão por especialidade para dimensionamento de equipe.

**Perguntas que responde:**
- Qual a demanda provável para o próximo mês?
- Qual especialidade vai precisar de mais médicos?

**Requer:** mínimo de 24 meses de dados históricos (carga histórica — item 5 do roadmap).

## Indicador de Governança — Casos Suspeitos de Conversão
Exibido na Visão Geral ou em destaque próprio. Mostra o volume mensal de 
casos suspeitos que precisaram de curadoria manual por erros de cadastro 
na origem. Serve como evidência para a diretoria avaliar a necessidade de 
melhorias no processo de cadastro do sistema MV.

## Fases de Entrega

### Fase 1 — Dados atuais (imediata)
Entregar as 7 páginas com os dados já disponíveis no pipeline. Requer:
- Trazer timestamps completos da jornada do raw pra marts (staging e marts)
- Criar campos calculados: turno, faixa etária, flag de desistência
- Criar modelo do ranking de especialidades no dbt
- Carga histórica de ~24 meses

### Fase 2 — Exames e prescrição
Incorporar ao pipeline novas fontes do sistema MV:
- Exames laboratoriais: pedido, resultado, tempo de retorno
- Exames de imagem: pedido, resultado, tempo de retorno
- Prescrição de medicamentos no box

**Impacto no painel:** enriquece a Página 2 (jornada) com o tempo entre 
atendimento médico e alta — mostra que o paciente estava aguardando exames, 
não "parado". Permite novas análises: volume de exames por paciente, 
relação entre exames e desfecho.

### Fase 3 — Cruzamentos avançados e financeiro
- Cruzamento com base de cirurgias: taxa de conversão cirúrgica
- Dados financeiros: custo por atendimento, impacto financeiro de evasões 
  e retornos
- Análise de risco clínico: relação entre exames alterados e retorno 48h

## Fontes de Dados

| Fonte | Status | Fase |
|---|---|---|
| Relatório de atendimentos | Ingerida | 1 |
| Relatório de internações | Ingerida | 1 |
| Relatório de movimentações | Ingerida | 1 |
| Exames laboratoriais | Disponível no MV | 2 |
| Exames de imagem | Disponível no MV | 2 |
| Prescrição de medicamentos | Disponível no MV | 2 |
| Cirurgias realizadas | Disponível no MV | 3 |
| Dados financeiros | A avaliar | 3 |