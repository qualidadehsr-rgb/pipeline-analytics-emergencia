select *
from {{ ref('atendimentos_pa') }}
where FIM_ATD_MEDICO is not null and
    INI_ATD_MEDICO is not null and
    FIM_ATD_MEDICO < INI_ATD_MEDICO