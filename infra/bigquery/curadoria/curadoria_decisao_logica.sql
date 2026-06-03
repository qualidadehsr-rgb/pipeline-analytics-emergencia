CREATE TABLE IF NOT EXISTS `pipeline-analytics-emergencia.curadoria.curadoria_decisao_logica`
(
  id_decisao        STRING    NOT NULL,
  id_inconsistencia STRING    NOT NULL,
  flag_prevalece    STRING    NOT NULL,
  justificativa     STRING,
  decidido_por      STRING    NOT NULL,
  decidido_em       TIMESTAMP NOT NULL
);