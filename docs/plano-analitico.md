# Plano Analítico — Emergência

**Data:** 2026-05-21  
**Última atualização:** 2026-05-21  
**Status:** Em construção

## Objetivo

Transformar os dados operacionais da emergência do hospital em análises 
que suportem decisões da diretoria. O plano evolui em fases — da entrega 
imediata com os dados disponíveis até a incorporação de novas fontes que 
ampliam o poder analítico.

## Estrutura de Páginas do Painel

### Página 1 — Visão Geral

Página principal do painel. Estruturada em 4 blocos com lógica de storytelling 
de cima pra baixo: "como estamos?" → "onde estão os números?" → "qual a tendência?" 
→ "qual especialidade precisa de atenção?".

**Bloco 1 — Resumo Executivo**  
Faixa no topo com 2-3 frases geradas automaticamente por medidas DAX. 
Identifica variação do mês, pior e melhor indicador, especialidade crítica 
e volume de suspeitos de conversão. Responde ao filtro da página — se filtrar 
por especialidade, o texto muda. Exemplo:  
*"Em abril, a taxa de conversão caiu 1,2 p.p. frente a março, puxada por 
Clínica Médica. A evasão melhorou 0,8 p.p. O turno da noite concentra 42% 
dos atendimentos."*

**Bloco 2 — KPIs principais**  
6 cards com valor atual e variação em relação ao mês anterior (seta + cor):

| KPI | Descrição |
|---|---|
| Total de atendimentos | Volume do mês selecionado |
| Taxa de conversão | % de atendimentos convertidos em internação |
| Taxa de alta na meta | % de pacientes com permanência ≤ 6h |
| Tempo de espera médica | Média ± desvio padrão |
| Retorno 48h | % de pacientes que retornaram em 48h |
| Taxa de evasão | % de pacientes que evadiram |

**Bloco 3 — Tendência mensal**  
Gráfico combo: barras (total de atendimentos) + linha (taxa de conversão). 
São os dois indicadores mais solicitados pela diretoria pra acompanhamento 
de variação.

**Bloco 4 — Especialidades**  
Barras horizontais com especialidades ranqueadas por indicador-chave. 
Aponta rapidamente qual especialidade precisa de atenção.

**Filtros:** período e especialidade no topo da página.

**Perguntas que responde:**
- Como estamos performando este mês comparado aos anteriores?
- A demanda está crescendo ou caindo?
- Qual especialidade precisa de atenção imediata?

### Página 2 — Jornada do Paciente
Funil completo do fluxo do paciente desde o totem até a alta, com tempo 
médio em cada etapa: espera pra classificação, classificação, espera pra 
recepção, cadastro, espera pro médico, atendimento médico, pós-atendimento 
até a alta. Identificação de abandonos (pacientes que não completaram o ciclo).

**Distribuição por percentil:** mostrar P50, P75, P90 e P95 dos tempos 
em vez de apenas média. Emergência possui cauda longa — a média esconde 
gargalos. Cálculo feito no dbt com `APPROX_QUANTILES` pra não sobrecarregar 
o Power BI.

**SLA visual com faixas:** classificar cada atendimento em faixas de 
permanência — dentro da meta (≤ 6h), fora da meta (6-12h), muito fora 
(> 12h). Gera leitura imediata pra diretoria.

**Perguntas que responde:**
- Onde está o gargalo dos pacientes que ultrapassam 6h de permanência?
- Em qual etapa o tempo é consumido?
- Quantos pacientes desistiram antes de completar o atendimento?
- O que aconteceu com pacientes sem registro de alta?
- Qual o tempo real de 50%, 75%, 90% e 95% dos pacientes em cada etapa?

**Filtros:** especialidade, turno, convênio, classificação de risco, CID

**Campos necessários:** ~~não estão na marts hoje~~ ✅ Timestamps trazidos 
para a marts (sessão 19/05). Campos: CHAMADA_CLASSIFICACAO, 
INICIO_CLASSIFICACAO, CHAMADA_CAD_RECEP, DH_CADASTRO_RECEPCAO, FIM_CAD_RECEP, 
DH_ATEND_MEDICO. Campo calculado turno ✅ criado na marts.

### Página 3 — Perfil do Paciente
Características demográficas: pirâmide etária, distribuição por sexo, mapa 
de demanda por localidade (CEP/cidade/UF), CIDs mais frequentes. Cruzamento 
de perfil com indicadores (ex: faixa etária × taxa de conversão).

**Perguntas que responde:**
- Qual o perfil dos pacientes que mais procuram a emergência?
- De onde vem a demanda geograficamente?
- Existe relação entre perfil demográfico e desfecho?

**Campo calculado:** faixa etária ✅ criado na marts.

### Página 4 — Retornos e Evasões
Análise de pacientes que retornaram em 48h: motivo do retorno, se internaram 
na segunda vez, comparação do CID entre as visitas. Análise de evasões: perfil 
de quem evade, se retornou depois, em quanto tempo, pelo mesmo motivo. 
Pacientes com classificação grave que evadiram.

**Análise temporal:** heatmap hora × dia da semana para evasão e retorno 
por horário. Revela padrões de subdimensionamento de equipe, gargalos e 
horários críticos. Campos já disponíveis na marts (`DT_HR_TOTEM_RECEP`, 
`turno`, flags de evasão e retorno). Pode exigir colunas auxiliares no dbt 
(hora e dia da semana extraídos).

**Perguntas que responde:**
- Por que os pacientes que retornaram em 48h não internaram na primeira consulta?
- Quem evadiu retornou? Em quanto tempo? Pelo mesmo motivo?
- Pacientes graves estão evadindo? Estão retornando?
- Em quais horários e dias da semana a evasão é mais frequente?

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
Modelo dbt `ranking_especialidades` ✅ já implementado.

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

**Análise temporal:** heatmap de demanda por hora × dia da semana. Revela 
padrões de volume que alimentam o dimensionamento de equipe por turno.

**Perguntas que responde:**
- Qual a demanda provável para o próximo mês?
- Qual especialidade vai precisar de mais médicos?
- Quais horários e dias concentram maior volume de atendimentos?

**Requer:** mínimo de 24 meses de dados históricos (carga histórica).

## Indicador de Governança — Casos Suspeitos de Conversão
Exibido na Visão Geral ou em destaque próprio. Mostra o volume mensal de 
casos suspeitos que precisaram de curadoria manual por erros de cadastro 
na origem. Serve como evidência para a diretoria avaliar a necessidade de 
melhorias no processo de cadastro do sistema MV. Dados de decisão 
(confirmado/descartado) disponíveis na tabela `curadoria.curadoria_conversao`.

## Ficha Técnica de Métricas

Documento formal (`docs/ficha-tecnica-metricas.md`) com definição, fórmula, 
regra, exclusões e owner de cada métrica do painel. Métricas documentadas:

- Taxa de conversão
- Retorno 48h
- Taxa de evasão
- Taxa de alta na meta (permanência)
- Tempo de espera médica
- Ranking de especialidades

**Objetivo:** eliminar disputas de número e garantir que todas as áreas 
usem a mesma definição. Deve ser criado antes da entrega da Página 1.

## Testes de Negócio no dbt

Testes singulares que validam regras de negócio além dos testes estruturais 
já existentes (not_null, unique, accepted_values). Implementados como 
arquivos `.sql` na pasta `tests/`. Devem ser criados antes da entrega da 
Página 1 para garantir confiança nos números.

| Teste | Regra |
|---|---|
| Permanência nunca negativa | `DT_HR_ALTA` >= `DT_HR_TOTEM_RECEP` |
| Internação após atendimento | Data de internação não anterior ao atendimento |
| Retorno 48h exige anterior | Retorno só existe com atendimento prévio |
| Evasão sem alta médica | `MOTIVO_ALTA` = 'EVASAO' não pode coexistir com alta médica |
| Classificação após totem | `DT_HR_CLASSIF_RISCO` >= `DT_HR_TOTEM_RECEP` |
| Atendimento médico após classificação | `INI_ATD_MEDICO` >= `DT_HR_CLASSIF_RISCO` |
| Fim após início do atendimento | `FIM_ATD_MEDICO` >= `INI_ATD_MEDICO` |
| Conversão e evasão exclusivos | `fl_conversao` e `fl_evasao` não podem ser 1 simultaneamente |
| Idade não negativa | `IDADE` >= 0 |

## Observabilidade Analítica

Painel de saúde do pipeline (Cloud Run) que monitora em tempo real:

- Status da última ingestão de cada tabela
- Tempo desde a última carga
- Volume por competência com faixa esperada
- Testes que falharam e quando
- Histórico de execuções do dbt
- Detecção de atraso na ingestão

Notificação automática quando algo estiver fora do esperado. 
**Implementação:** último item do roadmap, após conclusão de todas as fases.

## Fases de Entrega

### Fase 1 — Dados atuais
Entregar as 7 páginas com os dados já disponíveis no pipeline. Requer:
- ~~Trazer timestamps completos da jornada do raw pra marts~~ ✅
- ~~Criar campos calculados: turno, faixa etária~~ ✅ (flag de desistência adiada pra após carga histórica)
- ~~Criar modelo do ranking de especialidades no dbt~~ ✅
- Criar ficha técnica de métricas
- Criar testes de negócio no dbt (9 testes)
- Construir Página 1 no Power BI
- Carga histórica de ~24 meses
- Validar Página 1 com dados históricos
- Construir Páginas 2 a 7 (conforme dados disponíveis na Fase 1)

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

### Fase 4 — Observabilidade analítica
Painel de saúde do pipeline com monitoramento, alertas e detecção de anomalias. 
Detalhes na seção "Observabilidade Analítica" deste documento.

## Fontes de Dados

| Fonte | Status | Fase |
|---|---|---|
| Relatório de atendimentos | ✅ Ingerida | 1 |
| Relatório de internações | ✅ Ingerida | 1 |
| Relatório de movimentações | ✅ Ingerida | 1 |
| Exames laboratoriais | Disponível no MV | 2 |
| Exames de imagem | Disponível no MV | 2 |
| Prescrição de medicamentos | Disponível no MV | 2 |
| Cirurgias realizadas | Disponível no MV | 3 |
| Dados financeiros | A avaliar | 3 |