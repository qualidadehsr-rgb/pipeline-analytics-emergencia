select atend_PA, count(*) as total
from `pipeline_analytics-emergencia.marts.atendimentos_pa`
group by atend_PA
having count(*) > 1;