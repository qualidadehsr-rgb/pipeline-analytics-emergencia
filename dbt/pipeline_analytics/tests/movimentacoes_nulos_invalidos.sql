select * 
from {{ ref('stg_movimentacoes') }}
where safe_cast(Atendimento as int64) is not null and (Hora is null or Destino is null)