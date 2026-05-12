-- referencia tabela de internações
with source as (
    select * from {{source('raw', 'internacoes')}}
),
tipado as (
    select * except(COD_PACIENTE, ATENDIMENTO, DT_HR_ATENDIMENTO),
        {{cast_inteiro('COD_PACIENTE')}} as COD_PACIENTE,
        {{cast_inteiro('ATENDIMENTO')}} as ATENDIMENTO,
        {{cast_datetime('DT_HR_ATENDIMENTO')}} as DT_HR_ATENDIMENTO
    from source
),
transformado as (
    select
        COD_PACIENTE,
        ATENDIMENTO,
        ORIGEM_ATEND,
        DT_HR_ATENDIMENTO,
        LEITO,
        UNIDADE,
        competencia
    from tipado
)
select * from transformado
