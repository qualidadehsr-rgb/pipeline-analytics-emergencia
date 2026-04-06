# ADR-002 — Tratamento de Dados Sensíveis e LGPD

## Contexto
As bases de fonte dos dados trazem informações sensíveis do paciente conforme a LGPD. Alguns desses dados como: idade, CEP, Cidade e Estado são necessários para avaliação do perfil do paciente. Porém dados de identificação como: nome completo e data de nascimento não fazem parte do escopo de análise, sendo necessário tratamento adequado já na leitura desses dados na fonte.

## Decisão
Aplicar métodos de anonimização e exclusão de dados sensíveis já na leitura dos dados antes mesmo de carrega-los à nuvem.
- **Exclusão:**
    - Nome completo do paciente
    - Data de nascimento

- **Permanência:**
    - Nome e CRM do médico atendente
    - Idade do paciente
    - CEP
    - Bairro
    - Cidade
    - Estado
    - Número do prontuário
    - Número de atendimento

## Justificativa
Dados que identificam expressamente o paciente não serão necessários para compor análise, como: nome completo e data de nascimento. São dados sensíveis que são utilizados no contexto hospitalar para assistência segura e não para análise de resultados;
Já os dados necessários pará análise de perfil serão mantidos conforme descritos acima, pois há necessidade de acesso pelo responsável e também para análise operacional de consulta do prontuário no sistema MV.

## Consequências
- **Positivas:**
    - Dados permanentes melhoram o entendimento do perfil de atendimento;
    - Controle de acesso pelo responsável.
    
- **Negativas:**
    - Exigência de controle na disponibilização do painel para visualização quando houver necessidade de analisar performance por médico (pseudonimização futura);
    - Alguns campos sobre o bairro podem estar ausente na fonte, exigindo enriquecimento futuro via CEP.