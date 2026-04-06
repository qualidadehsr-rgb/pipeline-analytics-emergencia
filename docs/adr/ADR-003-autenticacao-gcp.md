# ADR-003 — Autenticação com GCP

## Contexto
A utilização das chaves de acesso aos serviços de nuvem é um processo delicado que exige máxima atenção e controle. Temos a possibilidade de gerenciar essas credenciais de forma local ou utilizar os próprios serviços da nuvem para isso, exemplo: Secret Manager no GCP. Nesse projeto não foi possível a utilização do ADC por questões de restrição ao Google Workspace da instituição.

## Decisão
Optei por utilizar o gerenciamento da chave em pasta local (chave em arquivo JSON), uma vez que a dinâmica de segurança para contas corporativas necessita de uma liberação da equipe de Ti do hospital o que pode travar o andamento do projeto. E para acessar o serviço de gerenciamento de credencial no GCP é necessário essa liberação.

## Justificativa
Dado o contexto de limitações permissivas da instituição decidi pelo gerenciamento da credencial de conexão por arquivo JSON em pasta local no computador de casa (quando atuar no projeto do trabalho outra chave será criada e armazenada em pasta local). Isso não trava o andamento do projeto, e assim que tiver a liberação da equipe de TI irei migrar para gerenciamento em nuvem.

## Consequências
- **Positivas:**
    - Continuidade do projeto sem depender de liberação do TI
    
- **Negativas:**
    - Gerenciamento de duas chaves (casa e trabalho)
    - Chave em arquivo local representa risco maior de exposição que ADC
    - Necessidade de migração futura quando TI liberar o Google Workspace