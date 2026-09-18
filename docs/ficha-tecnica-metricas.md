# Ficha Técnica de Métricas — Emergência

**Data:** 2026-05-29

**Status:** Em construção — expande conforme novas páginas forem desenvolvidas

**Fonte de dados:** `marts.atendimentos_pa`

---

## Sobre este documento

Documento de referência formal para definição, fórmula e regras de negócio de
cada indicador produzido pelo pipeline. Serve como fonte única de verdade quando
houver dúvida sobre como um número foi calculado ou por que dois relatórios
apresentam valores diferentes.

Este documento é vivo — novos indicadores são adicionados conforme as páginas
do Power BI forem construídas.

---

## Flags de Negócio

As flags são campos binários (0 ou 1) calculados no modelo `atendimentos_pa`.
Elas são a base de cálculo dos KPIs e não aparecem diretamente no painel,
mas documentá-las evita ambiguidade sobre o que cada indicador representa.

### `fl_conversao`

Indica que o atendimento no PA resultou em internação hospitalar confirmada.

**Regra:** O paciente possui um registro de internação com o mesmo código de
paciente dentro da janela D/D+1 (data do atendimento ou dia seguinte), e a
origem do atendimento de internação é uma das origens válidas da emergência
(`EMERGENCIA ADULTO`, `EMERGENCIA PEDIATRICA`, etc.).

**Valor 1:** Internação confirmada via JOIN com `stg_internacoes` com origem válida.

**Valor 0:** Sem internação vinculada com origem válida.

**Relação com `fl_suspeito_conversao`:** As duas flags são mutuamente exclusivas.
Um atendimento nunca terá ambas como 1 simultaneamente — a origem do atendimento
determina em qual das duas CTEs o registro se encaixa.

---

### `fl_suspeito_conversao`

Indica que o atendimento possui uma internação vinculada na janela D/D+1, mas
com origem cadastrada incorretamente no sistema hospitalar (origem diferente
das válidas da emergência).

**Regra:** Mesmo critério de JOIN que `fl_conversao`, mas com origem **não**
pertencente às origens válidas da emergência.

**Valor 1:** Internação vinculada com origem inválida — caso investigável.

**Valor 0:** Sem internação suspeita vinculada.

**Fluxo:** Casos com `fl_suspeito_conversao = 1` são encaminhados para revisão
pela assistente via interface de curadoria. Se confirmados, migram para
`fl_conversao = 1` no próximo re-run do dbt. Não entram no cálculo da
taxa de conversão enquanto não confirmados.

---

### `fl_retorno_48h`

Indica que o paciente retornou ao PA em menos de 48 horas após uma alta anterior.

**Regra:** O código do paciente possui outro atendimento registrado dentro de
48 horas antes do atendimento atual.

**Valor 1:** Retorno identificado.

**Valor 0:** Sem retorno em 48h identificado.

**Interpretação:** Evento negativo. Pode indicar alta precoce, resolução
incompleta do quadro ou erro no diagnóstico inicial. Análise aprofundada
reservada para página dedicada no painel.

---

### `fl_evasao`

Indica que o paciente deixou o PA sem receber alta médica formal.

**Regra:** `MOTIVO_ALTA = 'EVASAO'`

**Valor 1:** Evasão registrada.

**Valor 0:** Sem evasão.

**Interpretação:** Evento negativo. Pode indicar longo tempo de espera,
insatisfação com o atendimento ou melhora espontânea percebida pelo paciente.

---

## KPIs — Página 1 (Visão Geral)

### KPI 1 — Total de Atendimentos

**Definição:** Contagem total de atendimentos realizados no PA no período
selecionado.

**Fórmula:**
```
COUNT(atend_PA)
```

**Numerador:** Todos os atendimentos presentes na `atendimentos_pa`.

**Denominador:** Não se aplica — é uma contagem simples.

**Exclusões:** Nenhuma. A deduplicação é garantida na camada de ingestão,
portanto todos os registros da mart representam atendimentos únicos e válidos.

**Meta:** Não se aplica — indicador de volume e acompanhamento de demanda.

**Direção:** Neutro — o volume por si só não é positivo nem negativo sem
contexto de capacidade.

---

### KPI 2 — Taxa de Conversão

**Definição:** Percentual de atendimentos no PA que resultaram em internação
hospitalar confirmada.

**Fórmula:**
```
(SUM(fl_conversao) / COUNT(atend_PA)) * 100
```

**Numerador:** Atendimentos com `fl_conversao = 1` — internações confirmadas.

**Denominador:** Total de atendimentos no período (`COUNT(atend_PA)`).

**Exclusões:** Suspeitos de conversão (`fl_suspeito_conversao = 1`) não entram
no numerador enquanto não confirmados via curadoria.

**Meta:** 9% — quanto maior, melhor. Indica capacidade de resolução de casos
complexos dentro da emergência.

**Direção:** Positivo — quanto maior o valor, melhor o desempenho.

---

### KPI 3 — Taxa de Alta na Meta

**Definição:** Percentual de atendimentos com alta registrada dentro de 6 horas
a partir da chegada ao totem de recepção.

**Fórmula:**
```
(
  SUM(CASE WHEN TIMESTAMP_DIFF(DT_HR_ALTA, DT_HR_TOTEM_RECEP, MINUTE) <= 360
           THEN 1 ELSE 0 END)
  /
  COUNT(atend_PA)
) * 100
```

**Numerador:** Atendimentos com permanência ≤ 360 minutos (6 horas).

**Denominador:** Total de atendimentos no período, incluindo os sem
registro de alta.

**Permanência calculada como:**
`TIMESTAMP_DIFF(DT_HR_ALTA, DT_HR_TOTEM_RECEP, MINUTE)`

**Exclusões e penalizações:** Atendimentos com `DT_HR_ALTA` nulo **não são
excluídos** — entram no denominador com valor 0 no numerador, penalizando
a taxa. O registro de alta é obrigatório; sua ausência é tratada como
não conformidade.

**Meta:** 100% — todos os atendimentos devem ser resolvidos em até 6 horas.

**Direção:** Positivo — quanto maior o valor, melhor o desempenho.

---

### KPI 4 — Tempo de Espera Médica

**Definição:** Tempo médio, em minutos, entre a chegada do paciente ao totem
de recepção e o início do atendimento médico. Acompanhado do desvio padrão
para evidenciar a variabilidade.

**Fórmula:**
```
AVG(TIMESTAMP_DIFF(INI_ATD_MEDICO, DT_HR_TOTEM_RECEP, MINUTE))
STDEV(TIMESTAMP_DIFF(INI_ATD_MEDICO, DT_HR_TOTEM_RECEP, MINUTE))
```

**Numerador:** Soma dos tempos de espera individuais.

**Denominador:** Contagem de atendimentos com `INI_ATD_MEDICO` preenchido.

**Exclusões:**
- Registros com `INI_ATD_MEDICO` nulo — ficam fora do cálculo.
- Tempos negativos — indicam inconsistência de cadastro e são capturados
  pelos testes de qualidade do dbt.

**Meta por Protocolo de Manchester:**

| Classificação | Cor | Tempo máximo |
|---|---|---|
| Emergência | Vermelho | Imediato |
| Muito urgente | Laranja | 10 minutos |
| Urgente | Amarelo | 60 minutos |
| Pouco urgente | Verde | 120 minutos |
| Não urgente | Azul | 240 minutos |

**Exibição na Página 1:** Média geral ± desvio padrão.

**Detalhamento por classificação:** A avaliar — Página 1 se houver espaço,
ou página dedicada.

**Direção:** Negativo — quanto menor o tempo, melhor o desempenho.

---

### KPI 5 — Taxa de Retorno em 48h

**Definição:** Percentual de atendimentos cujo paciente retornou ao PA em
menos de 48 horas após uma alta anterior.

**Fórmula:**
```
(SUM(fl_retorno_48h) / COUNT(atend_PA)) * 100
```

**Numerador:** Atendimentos com `fl_retorno_48h = 1`.

**Denominador:** Total de atendimentos no período (`COUNT(atend_PA)`).

**Exclusões:** Nenhuma.

**Tolerância:** 0,05%. Não é uma meta a ser atingida — é o limite aceitável.
O ideal é 0%, sabendo que eventos esporádicos podem ocorrer.

**Direção:** Negativo — quanto menor o valor, melhor o desempenho.

**Nota:** A interpretação causal (alta precoce, erro de diagnóstico, etc.)
é reservada para página dedicada no painel.

---

### KPI 6 — Taxa de Evasão

**Definição:** Percentual de atendimentos em que o paciente deixou o PA
sem receber alta médica formal.

**Fórmula:**
```
(SUM(fl_evasao) / COUNT(atend_PA)) * 100
```

**Numerador:** Atendimentos com `fl_evasao = 1` (`MOTIVO_ALTA = 'EVASAO'`).

**Denominador:** Total de atendimentos no período (`COUNT(atend_PA)`).

**Exclusões:** Nenhuma.

**Meta:** Não declarada formalmente pela gestão. Espera-se a minimização
do indicador, sem tolerância definida.

**Direção:** Negativo — quanto menor o valor, melhor o desempenho.


---

## Indicadores — Página 2 (Jornada do Paciente)

Indicadores calculados no modelo `atendimentos_pa` (campos por atendimento) e
nos modelos agregados `percentis_jornada` e `volume_jornada` (por competência
e especialidade).

### `faixa_sla`

**Definição:** Classificação categórica da permanência total do atendimento
(do totem à alta) em quatro categorias de SLA.

**Regra:**
| Faixa | Condição |
|---|---|
| Dentro da meta | Permanência ≤ 360 minutos (6h) |
| Fora da meta | Permanência entre 361 e 720 minutos (6h–12h) |
| Muito fora da meta | Permanência > 720 minutos (12h) |
| Alta não registrada | `DT_HR_ALTA` nulo |
| Registro inconsistente | `DT_HR_ALTA` anterior ao totem (inconsistência de sequência) |

**Nota de implementação:** as duas últimas categorias eram originalmente
representadas como `null` na coluna. Foram convertidas em texto explícito em
2026-08-17 porque `null` impedia a criação de relacionamento de chave única
entre `atendimentos_pa` e `volume_jornada` no modelo do Power BI (necessário
para que o gráfico de SLA respeite os mesmos filtros do restante da Página 2).

**Diferença em relação a `fl_alta_na_meta` (KPI 3):** `fl_alta_na_meta` é
binário e penaliza a ausência de alta para uso no ranking de pontuação das
especialidades (usado para cálculo de taxa). `faixa_sla`não penaliza — serve
para visualização granular por atendimento, não para métricas agregadas de desempenho.

---

### Durações por etapa da jornada

Calculadas em `atendimentos_pa` como a diferença, em minutos, entre o timestamp
de chegada em cada etapa e o timestamp da etapa anterior.

| Campo | Etapa | Do timestamp | Ao timestamp |
|---|---|---|---|
| `minutos_espera_classificacao` | Espera para classificação | `DT_HR_TOTEM_RECEP` | `INICIO_CLASSIFICACAO` |
| `minutos_duracao_classificacao` | Duração da classificação | `INICIO_CLASSIFICACAO` | `DT_HR_CLASSIF_RISCO` |
| `minutos_espera_cadastro` | Espera para cadastro | `DT_HR_CLASSIF_RISCO` | `DH_CADASTRO_RECEPCAO` |
| `minutos_duracao_cadastro` | Duração do cadastro | `DH_CADASTRO_RECEPCAO` | `FIM_CAD_RECEP` |
| `minutos_espera_medica_pos_cadastro` | Espera para o médico (pós-cadastro) | `FIM_CAD_RECEP` | `INI_ATD_MEDICO` |
| `minutos_duracao_atendimento_medico` | Duração do atendimento médico | `INI_ATD_MEDICO` | `FIM_ATD_MEDICO` |
| `minutos_permanencia_total` | Permanência total | `DT_HR_TOTEM_RECEP` | `DT_HR_ALTA` |

**Exclusões (regra comum a todas):** Retornam `null` quando o timestamp de
destino é nulo, **ou** quando o timestamp de destino é anterior ao de origem
(inconsistência de sequência temporal, capturada pelos testes de qualidade
correspondentes — ver seção de testes de negócio).

**Etapa descartada:** `minutos_pos_atendimento_ate_alta` (fim do atendimento
médico → alta) foi avaliada e removida do escopo. Em ~82% dos casos
`DT_HR_ALTA` antecede `FIM_ATD_MEDICO` — não é erro de dado, é uma
particularidade operacional (registro de alta antecede o fechamento do atendimento
pelo médico no sistema). Sem uma sequência confiável entre os dois eventos, 
a duração não é uma métrica válida.

**Nota:** `minutos_espera_medica` (já existente, fora desta tabela) mede
`DT_HR_TOTEM_RECEP → INI_ATD_MEDICO` diretamente — é uma métrica diferente
("tempo até o médico"), não uma etapa do funil sequencial.

---

### Percentis por etapa (`percentis_jornada`)

**Definição:** P50 (mediana) e P90 de cada duração listada acima, agregados
por competência, especialidade (`SERVICO`), turno, convênio, classificação de
risco (`COR_CLASSIF`) e grupo CID (`grupo_cid`), as 6 dimensões de filtro da
Página 2.

**Linhas consolidadas:** para cada dimensão categórica (especialidade, turno,
convênio, classificação de risco, grupo CID), existe também uma linha com
valor `'Todas'`, representando o consolidado daquela dimensão, necessário
para que os cards e visuais da página mostrem um resultado coerente quando
nenhum filtro específico está selecionado. Existe ainda uma linha totalmente
consolidada (todas as 5 dimensões categóricas em `'Todas'` e `competencia`
nula), representando o histórico completo.

**Por que percentil em vez de média:** o PA tem cauda longa, poucos casos
extremos distorcem a média e escondem gargalos reais. P50 mostra o tempo
típico; P90 mostra o teto para a grande maioria dos casos, expondo a cauda
longa sem a instabilidade estatística de percentis mais extremos (ex: P95)
em grupos com poucos atendimentos.

**Cálculo:** `APPROX_QUANTILES(duração, 100)`, extraindo os offsets 50 e 90.

**Formato:** uma linha por competência + especialidade + turno + convênio +
classificação de risco + grupo CID + etapa, com colunas `p50` e `p90`
(formato longo, não uma coluna por percentil). Inclui a coluna `ordem` para
ordenação correta das etapas na exibição.

**Validação:** teste de qualidade `percentis_p90_maior_p50` garante que P90
nunca seja menor que P50 na mesma linha.
**Limitação de uso no Power BI:** apesar de pré-calculada, esta tabela não
suporta filtro de competência livre (seleção de múltiplos meses arbitrários)
sem gerar uma linha nova por combinação, inviável dado o número de
combinações possíveis. Por isso, o card de Permanência Mediana e a tabela de
Duração por Etapa da Página 2 calculam P50/P90 sob demanda em DAX
(`PERCENTILEX.INC` sobre `atendimentos_pa`, filtrando valores nulos), não a
partir desta tabela. `percentis_jornada` permanece útil para auditoria e
validação cruzada de valores, mas não é a fonte de nenhum visual interativo
da página.

---

### Volume por etapa (`volume_jornada`)

**Definição:** Contagem de atendimentos com cada marco da jornada preenchido
(não-nulo), por competência, especialidade, turno, convênio, classificação de
risco, grupo CID e faixa de SLA, as 6 dimensões de filtro da página mais a
dimensão do gráfico de SLA (usada para a interação de clique entre os dois
visuais). Insumo para o funil visual da Página 2.

**Marcos contados (8):** Totem, Início Classificação, Fim Classificação,
Início Cadastro, Fim Cadastro, Início Médico, Fim Médico, Alta.

**Origem da decisão:** substitui o indicador de desistência, avaliado e
descartado (ver `plano-analitico.md`) — o dado não permite distinguir
"paciente que desistiu" de "atendimento de natureza pontual que não segue o
fluxo padrão" (ex: procedimentos/infusões). O volume por etapa responde "onde
o funil estreita" sem exigir esse julgamento por atendimento individual, e
também cobre a pergunta "o que aconteceu com pacientes sem registro de alta?"
(marco "Alta" no funil).

**Nota:** não há garantia de decrescimento estrito entre etapas consecutivas —
atendimentos que pulam etapas (ex: procedimentos pontuais) podem gerar
pequenas inversões de volume entre marcos adjacentes. Validado como
comportamento esperado (~1% dos atendimentos), não uma inconsistência de dado.

**Por que esta tabela permanece pré-calculada (diferente de `percentis_jornada`):**
contagem (`COUNT`) é uma operação que se combina corretamente entre grupos,
a soma de contagens parciais sempre equivale à contagem total, diferente de
mediana/percentil. Por isso, cruzar as 6+1 dimensões nesta tabela não introduz
o mesmo risco estatístico, e o pré-cálculo no dbt continua sendo a abordagem
correta aqui.

---

## Indicadores — Página 3 (Perfil do Paciente)

Indicadores calculados no modelo `atendimentos_pa`, por atendimento, sem
tabela agregada dedicada (diferente da Página 2), já que os blocos desta
página não sofrem o mesmo problema de combinação estatística que levou
`percentis_jornada` a existir.

### `faixa_etaria` e `ordem_faixa_etaria`

`faixa_etaria` já documentada anteriormente (campo calculado a partir de
`IDADE`, em 11 faixas). Nesta página, ganhou uma coluna auxiliar numérica,
`ordem_faixa_etaria` (1 a 11, uma por faixa), exclusivamente para ordenação
correta no eixo de visuais — sem ela, o Power BI ordena a faixa etária
alfabeticamente (`"12 a 14"` antes de `"3 a 5"`), quebrando a sequência
lógica da pirâmide etária.

### Tratamento de nulos — `SEXO` e `grupo_cid`

Mesmo padrão já adotado em `faixa_sla`: nulo vira categoria explícita, não é
excluído nem escondido.

| Campo | Regra | Categoria explícita |
|---|---|---|
| `SEXO` | Nulo ou vazio (~0,04% dos casos) | `Não Informado` |
| `grupo_cid` | Sem correspondência em `seed_cid_capitulo` (atendimento sem CID registrado) | `Não Classificado` |

### Pirâmide etária

Faixa etária cruzada com sexo, contagem de atendimentos. Implementada como
gráfico de barras clusterizadas nativo (não um visual customizado), o efeito
de pirâmide é obtido multiplicando a contagem de um dos sexos por -1 e
aplicando um formato de exibição customizado (`#,##0;#,##0`) para ocultar o
sinal negativo, tanto na medida quanto no eixo do visual.

### CIDs mais frequentes

Ranking por `CID` (código individual, não `grupo_cid`), decisão deliberada:
como `grupo_cid` já existe como filtro global da página, um ranking por
código individual oferece mais valor analítico do que repetir a mesma
granularidade agregada do filtro.

### Cruzamento perfil × desfecho

Implementado via 2 Parâmetros de Campo (Field Parameters), não como tabela
pré-calculada:
- **Dimensão** (eixo): `faixa_etaria`, `SEXO` ou `UF`
- **Medida** (valor): Taxa de Conversão, Taxa de Evasão, Taxa de Retorno 48h,
  Taxa de Alta na Meta, ou Permanência Mediana P50

**Nota técnica — P50 formatado:** a medida de permanência usada no parâmetro
retorna o valor numérico puro (minutos), obrigatório para que o gráfico de
barras calcule a altura corretamente, uma medida que retorna texto
formatado (`"Xh Ymin"`) não pode definir altura de barra. A versão formatada
em texto é exibida via campo de Dica de Ferramenta do visual, sempre visível
ao passar o mouse, independente de qual medida estiver selecionada no
parâmetro.

---

## Histórico de Alterações

| Data | Alteração |
|---|---|
| 2026-05-29 | Criação do documento com flags de negócio e KPIs da Página 1 |
| 2026-08-14 | Adição dos KPIs da Página 2 |
| 2026-08-17 | Página 2 finalizada: `faixa_sla` com 4 categorias (nulos tratados), `percentis_jornada` e `volume_jornada` expandidos para as 6 dimensões de filtro + `grupo_cid`, card de P50 e tabela de Duração por Etapa migrados para cálculo sob demanda via `PERCENTILEX.INC` |
| 2026-09-16 | Página 3 finalizada: pirâmide etária, CIDs mais frequentes e cruzamento perfil × desfecho via Parâmetros de Campo. `SEXO` e `grupo_cid` com nulos tratados como categoria explícita. |