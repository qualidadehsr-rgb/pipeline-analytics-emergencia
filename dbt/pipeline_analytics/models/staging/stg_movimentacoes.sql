with source as (
    select * from {{source('raw', 'movimentacoes')}}
),
transformado as(
    select
        {{cast_inteiro('Atendimento')}} as Atendimento,
        {{ cast_time('Hora') }} as Hora,
        Destino,
        competencia
    from source
)
select * from transformado