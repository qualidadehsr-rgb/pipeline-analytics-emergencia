CREATE TABLE IF NOT EXISTS `pipeline-analytics-emergencia.curadoria.curadoria_inconsistencias`
(
  id_inconsistencia  STRING    NOT NULL,
  tipo               STRING    NOT NULL,
  teste              STRING    NOT NULL,
  atend_PA           INT64     NOT NULL,
  competencia        DATE      NOT NULL,
  servico            STRING,
  detectado_em       TIMESTAMP NOT NULL,
  status             STRING    NOT NULL
);