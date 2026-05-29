select *
from {{ ref('atendimentos_pa') }}
where INI_ATD_MEDICO is not null
    and DT_HR_CLASSIF_RISCO is not null
    and COR_CLASSIF is not null
    and COR_CLASSIF != 'VERMELHO'
    and INI_ATD_MEDICO < DT_HR_CLASSIF_RISCO