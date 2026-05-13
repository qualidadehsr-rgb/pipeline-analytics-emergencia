# ADR-011 — Proteção contra duplicação na camada Raw

## Contexto
Os scripts de ingestão utilizam `WRITE_APPEND` para carregar dados no BigQuery, permitindo acúmulo de histórico por competência. Porém, se um arquivo for enviado ao bucket mais de uma vez — por engano do operador ou por reprocessamento — os mesmos dados são inseridos novamente, duplicando registros na camada Raw. Essa duplicação se propaga para Staged, Marts e consequentemente para o Power BI.

## Decisão
Adicionar verificação no `main.py`, dentro da função `processar()`, antes de executar o script de ingestão. Uma query consulta se já existem registros na tabela Raw correspondente para aquela competência. Se existirem, a ingestão é ignorada e o evento é encerrado com log informativo. A competência e o nome da tabela são extraídos do nome do arquivo e do nome do script, respectivamente.

## Justificativa
- Centralizar a verificação no `main.py` evita replicar a mesma lógica em 3 scripts de ingestão diferentes
- A verificação antes da ingestão impede que dados cheguem à Raw — corrigir depois exigiria DELETE manual
- Usa o próprio BigQuery que já é consultado na verificação das 3 tabelas, sem infraestrutura adicional
- Competência extraída do nome do arquivo (não mais via query) garante compatibilidade com múltiplas competências no histórico

## Consequências
- **Positivas:**
    - Impede duplicação acidental por re-upload do mesmo arquivo
    - Proteção essencial para a futura carga histórica de ~24 meses
    - Sem custo adicional — reutiliza cliente BigQuery já existente
    - Log claro identifica tabela e competência ignorada
- **Negativas:**
    - Se houver necessidade legítima de reprocessar uma competência (ex: arquivo com dados corrigidos), será necessário primeiro deletar os dados daquela competência no BigQuery manualmente antes de reenviar o arquivo