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

## Histórico de Alterações

| Data | Alteração |
|---|---|
| 2026-05-29 | Criação do documento com flags de negócio e KPIs da Página 1 |