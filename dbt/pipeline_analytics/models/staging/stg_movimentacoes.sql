with source as (
    select * from {{source('raw', 'movimentacoes')}}
),
transformado as(
    select
        {{cast_inteiro('ATEND')}} as ATENDIMENTO,
        cast(HORA as time) as HORA,
        TIPO,
        ORIGEM,
        DESTINO,
        TIP_ACOM,
        CID,
        CONVENIO,
        MOTIVO_ALTA,
        UNIDADE,
        safe_cast(nullif(DATA, 'NaT') as date) as DATA,
        parse_date('%Y-%m', competencia) as COMPETENCIA
    from source
)
select * from transformado