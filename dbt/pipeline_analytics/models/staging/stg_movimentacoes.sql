with source as (
    select * from {{source('raw', 'movimentacoes')}}
),
transformado as(
    select
        {{cast_inteiro('Atendimento')}} as Atendimento,
        Destino
    from source
)
select * from transformado