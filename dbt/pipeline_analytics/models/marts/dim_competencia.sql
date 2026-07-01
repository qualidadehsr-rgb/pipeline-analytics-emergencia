-- tabela para gerar competência dinamicamente a partir dos dados existentes
with competencias as(
    select distinct competencia
    from {{ ref('atendimentos_pa') }}
),

final as(
    select
        competencia,
        extract(year from competencia) as ano,
        extract(month from competencia) as mes,
        case
            when extract(month from competencia) = 1 then 'Jan'
            when extract(month from competencia) = 2 then 'Fev'
            when extract(month from competencia) = 3 then 'Mar'
            when extract(month from competencia) = 4 then 'Abr'
            when extract(month from competencia) = 5 then 'Mai'
            when extract(month from competencia) = 6 then 'Jun'
            when extract(month from competencia) = 7 then 'Jul'
            when extract(month from competencia) = 8 then 'Ago'
            when extract(month from competencia) = 9 then 'Set'
            when extract(month from competencia) = 10 then 'Out'
            when extract(month from competencia) = 11 then 'Nov'
            when extract(month from competencia) = 12 then 'Dez' end as nome_mes,
        extract(quarter from competencia) as trimestre
    from competencias
),

with_label as(
    select *,
            concat(nome_mes, '/', cast(ano as string)) as competencia_label
    from final
)
select * from with_label