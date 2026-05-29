select *
from {{ ref('atendimentos_pa') }}
where DT_HR_ALTA is not null and DT_HR_ALTA < DT_HR_TOTEM_RECEP