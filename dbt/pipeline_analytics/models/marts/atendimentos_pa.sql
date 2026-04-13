with atendimentos as (
    select * from {{ref('stg_atendimentos')}}
),
internacoes as (
    select * from {{ref('stg_internacoes')}}
),
movimentacoes as (
    select * from {{ref('stg_movimentacoes')}}
),
leitos as (
    select * from {{ref('dim_leitos')}}
),
numerado as (
    select *,
        row_number() over(
            partition by CD_PACIENTE, DT_ATENDIMENTO
            order by DT_HR_TOTEM_RECEP desc
        ) as candidato_internacao
    from atendimentos
),
ultimo_atendimento as (
    select * from numerado
    where candidato_internacao = 1
),
conversoes as (
    select
       u.CD_ATENDIMENTO as atend_PA,
       u.CD_PACIENTE,
       u.IDADE,
       u.SEXO,
       u.CEP,
       u.CIDADE,
       u.UF,
       u.CONVENIO,
       u.SERVICO,
       u.COR_CLASSIF,
       u.PRESTADOR,
       u.ESPECIALIDADE,
       u.CID,
       u.MOTIVO_ALTA,
       u.DT_ATENDIMENTO,
       u.DT_HR_TOTEM_RECEP,
       u.DT_HR_CLASSIF_RISCO,
       u.INI_ATD_MEDICO,
       u.FIM_ATD_MEDICO,
       u.DT_HR_ALTA,
       i.ATENDIMENTO as atend_internacao,
       i.ORIGEM_ATEND,
       m.Destino as LEITO,
       l.Unidade,
       l.Tipo,
       case when i.ATENDIMENTO is not null then 1 else 0 end as fl_conversao
    from ultimo_atendimento as u
    left join internacoes as i
    on u.CD_PACIENTE = i.COD_PACIENTE and
    date(i.DT_HR_ATENDIMENTO) between date(u.DT_ATENDIMENTO) and
    date_add(date(u.DT_ATENDIMENTO), interval 1 day) and
    i.ORIGEM_ATEND in ('EMERGENCIA ADULTO', 'EMERGENCIA INFANTIL')
    left join movimentacoes as m
    on i.ATENDIMENTO = m.Atendimento
    left join leitos as l
    on m.destino = l.leito
)
select * from conversoes