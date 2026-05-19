with indicadores as (
    select
        SERVICO,
        competencia,
        (sum(fl_conversao) / count(*)) * 100.0 as tx_conversao,
        (sum(fl_retorno_48h) / count(*)) * 100.0 as tx_retorno48h,
        (sum(fl_evasao) / count(*)) * 100.0 as tx_evasao,
        avg(timestamp_diff(INI_ATD_MEDICO, DT_HR_TOTEM_RECEP, minute)) as tempo_inicio_medico,
        (sum(case
        when DT_HR_ALTA is null then 0
        when timestamp_diff(DT_HR_ALTA, DT_HR_TOTEM_RECEP, hour) <= 6 then 1 else 0 end) / count(*)) * 100.0 as tx_alta_na_meta
    from {{ ref('atendimentos_pa') }}
    where SERVICO != 'OUTROS'
    group by SERVICO, competencia
),

posicao as (
    select *,
    dense_rank() over(
        partition by competencia
        order by tx_conversao desc
    ) as conversao,
    dense_rank() over(
        partition by competencia
        order by tx_alta_na_meta desc
    ) as alta_na_meta,
    dense_rank() over(
        partition by competencia
        order by tempo_inicio_medico asc
    ) as tempo_atend_medico,
    dense_rank() over(
        partition by competencia
        order by tx_retorno48h asc
    ) as retorno48h,
    dense_rank() over(
        partition by competencia
        order by tx_evasao asc
    ) as evasao
    from indicadores
),

posicao_final as (
    select *,
    case
        when conversao = 1 then 100
        when conversao = 2 then 90
        when conversao = 3 then 70
        when conversao = 4 then 50
        when conversao = 5 then 30
        when conversao = 6 then 10
    end * 0.25 as pontos_conversao,
    case
        when alta_na_meta = 1 then 100
        when alta_na_meta = 2 then 90
        when alta_na_meta = 3 then 70
        when alta_na_meta = 4 then 50
        when alta_na_meta = 5 then 30
        when alta_na_meta = 6 then 10
    end * 0.20 as pontos_alta_meta,
    case
        when tempo_atend_medico = 1 then 100
        when tempo_atend_medico = 2 then 90
        when tempo_atend_medico = 3 then 70
        when tempo_atend_medico = 4 then 50
        when tempo_atend_medico = 5 then 30
        when tempo_atend_medico = 6 then 10
    end * 0.25 as pontos_atend_medico,
    case
        when evasao = 1 then 100
        when evasao = 2 then 90
        when evasao = 3 then 70
        when evasao = 4 then 50
        when evasao = 5 then 30
        when evasao = 6 then 10
    end * 0.10 as pontos_evasao,
    case
        when retorno48h = 1 then 100
        when retorno48h = 2 then 90
        when retorno48h = 3 then 70
        when retorno48h = 4 then 50
        when retorno48h = 5 then 30
        when retorno48h = 6 then 10
    end * 0.20 as pontos_retorno48h
    from posicao
),

final as (
    select *,
    (pontos_conversao + pontos_atend_medico + pontos_alta_meta + pontos_evasao + pontos_retorno48h) as total_pontos
    from posicao_final
)

select * from final