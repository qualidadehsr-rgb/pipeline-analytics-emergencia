select atend_PA
from {{ ref('atendimentos_pa') }}
where IDADE is not null and IDADE < 0