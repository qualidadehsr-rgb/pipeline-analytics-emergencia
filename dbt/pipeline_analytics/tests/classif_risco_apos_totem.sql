select *
from {{ ref('atendimentos_pa') }}
where DT_HR_CLASSIF_RISCO is not null and DT_HR_CLASSIF_RISCO < DT_HR_TOTEM_RECEP