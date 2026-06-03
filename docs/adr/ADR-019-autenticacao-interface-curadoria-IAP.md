# ADR-019 — Autenticação da Interface de Curadoria via Identity-Aware Proxy (IAP)

## Contexto

A interface de curadoria (`curadoria-pipeline-emergencia-service`) é um serviço Flask
deployado no Cloud Run que permite revisão humana de casos suspeitos e inconsistências
nos dados do PA. Por processar dados de pacientes, está sujeita à LGPD e exige controle
de acesso adequado.

Durante o desenvolvimento, o serviço operava com a permissão `allUsers` concedida
diretamente no Cloud Run, tornando a interface publicamente acessível a qualquer pessoa
com a URL — sem autenticação. Esse comportamento foi identificado como risco de segurança
e de conformidade antes da entrada em operação.

A restrição de acesso precisava ser resolvida sem impor instalações ou configurações
técnicas no computador do operador (usuário não técnico), dado o ambiente corporativo
com limitações impostas pela TI.

## Decisão

Adotar o **Identity-Aware Proxy (IAP)** do Google Cloud como camada de autenticação
e autorização da interface de curadoria.

A configuração implementada:

1. Remoção da permissão `allUsers` do serviço Cloud Run
2. Configuração da tela de consentimento OAuth (tipo: Interno — restrito à organização
   `gruposanta.com.br`)
3. Ativação do IAP diretamente no serviço `curadoria-pipeline-emergencia-service`
4. Concessão do papel `IAP-secured Web App User` à conta `qualidade.hsr@gruposanta.com.br`

## Funcionamento

O operador acessa a URL do serviço pelo navegador. O IAP intercepta a requisição,
redireciona para autenticação Google e, após login com conta autorizada, libera o acesso
à interface. Nenhuma instalação local é necessária.

Contas não autorizadas são bloqueadas pelo IAP antes de qualquer requisição chegar
ao Flask.

## Alternativas Consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| Manter `allUsers` com login/senha na interface | URL permanece pública; senha hardcoded ou em variável de ambiente; sem controle de sessão robusto |
| Restrição por IP (rede interna) | Depende de configuração pela TI corporativa; impede acesso remoto legítimo |
| Cloud Run Invoker via IAM | Requer token de identidade na requisição HTTP — não funciona pelo navegador sem extensão ou configuração especial |

## Consequências

- A interface de curadoria só é acessível a contas Google explicitamente autorizadas
  no IAP
- O operador não precisa instalar nada — acesso por navegador comum com conta
  corporativa Google
- Novas contas autorizadas são adicionadas pelo painel do IAP no GCP, sem alteração
  de código ou redeploy
- Dados de pacientes processados na curadoria estão protegidos por autenticação
  compatível com os requisitos da LGPD
- O serviço de ingestão (`ingestao-pipeline-emergencia-service`) mantém autenticação
  IAM — não é afetado por esta decisão