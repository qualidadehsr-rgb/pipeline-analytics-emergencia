CREATE TABLE IF NOT EXISTS `pipeline-analytics-emergencia.curadoria.curadoria_imputacao_integridade`
(
  id_imputacao      STRING    NOT NULL,
  id_inconsistencia STRING    NOT NULL,
  campo_afetado     STRING    NOT NULL,
  valor_original    STRING,
  valor_imputado    STRING    NOT NULL,
  decidido_por      STRING    NOT NULL,
  decidido_em       TIMESTAMP NOT NULL
);