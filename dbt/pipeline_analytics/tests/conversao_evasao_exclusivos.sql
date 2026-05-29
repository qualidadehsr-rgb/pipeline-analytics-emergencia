select atend_PA
from {{ ref('atendimentos_pa') }}
where fl_conversao = 1 and fl_evasao = 1