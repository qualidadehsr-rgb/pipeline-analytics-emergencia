with source as (
    select * from {{source('raw', 'movimentacoes')}}
),
transformado as(
    select
        {{cast_inteiro('ATEND')}} as ATENDIMENTO,
        {{ cast_time('HORA') }} as HORA,
        TIPO,
        ORIGEM,
        DESTINO,
        TIP_ACOM,
        CID,
        CONVENIO,
        MOTIVO_ALTA,
        UNIDADE,
        {{ cast_data('DATA') }} as DATA,
        parse_date('%Y-%m', competencia) as COMPETENCIA
    from source
)
select * from transformado