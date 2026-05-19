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

ultima_movimentacao as(
    select *,
        row_number() over(
            partition by Atendimento
            order by Hora desc
        ) as ranking
    from movimentacoes
    qualify ranking = 1
),

movimentacao_enriquecida as(
    select *
    from ultima_movimentacao as u
    left join leitos as l
    on u.destino = l.leito
),

internacao_leito_certo as (
    select
    i.ATENDIMENTO,
    i.COD_PACIENTE,
    i.ORIGEM_ATEND,
    i.DT_HR_ATENDIMENTO,
    coalesce(m.Destino, i.LEITO) as LEITO,
    coalesce(m.Unidade, i.UNIDADE) as UNIDADE,
    l.Tipo
    from internacoes as i
    left join movimentacao_enriquecida as m
    on i.ATENDIMENTO = m.Atendimento
    left join leitos as l
    on coalesce(m.Destino, i.LEITO) = l.leito
),

ultimo_atendimento as (
    select *,
    row_number() over(
        partition by CD_PACIENTE, DT_ATENDIMENTO
        order by DT_HR_TOTEM_RECEP desc
    ) as ranking
    from atendimentos
    qualify ranking = 1
),

atendimento_com_internacoes as(
    select
    u.CD_ATENDIMENTO,
    lc.ATENDIMENTO,
    lc.ORIGEM_ATEND,
    lc.LEITO as Destino,
    lc.UNIDADE as Unidade,
    lc.Tipo
    from ultimo_atendimento as u
    left join internacao_leito_certo as lc
    on u.CD_PACIENTE = lc.COD_PACIENTE
    and date(lc.DT_HR_ATENDIMENTO) between date(u.DT_ATENDIMENTO)
    and date_add(date(u.DT_ATENDIMENTO), interval 1 day)
    and lc.ORIGEM_ATEND in ('EMERGENCIA ADULTO', 'EMERGENCIA INFANTIL')
    qualify row_number() over(
        partition by lc.ATENDIMENTO
        order by timestamp_diff(lc.DT_HR_ATENDIMENTO, u.DT_HR_TOTEM_RECEP, minute) asc
    ) = 1
),

possivel_conversao as(
    select
    u.CD_ATENDIMENTO,
    lc.ATENDIMENTO,
    lc.ORIGEM_ATEND,
    lc.LEITO as Destino,
    lc.UNIDADE as Unidade,
    lc.Tipo
    from ultimo_atendimento as u
    left join internacao_leito_certo as lc
    on u.CD_PACIENTE = lc.COD_PACIENTE
    and date(lc.DT_HR_ATENDIMENTO) between date(u.DT_ATENDIMENTO)
    and date_add(date(u.DT_ATENDIMENTO), interval 1 day)
    and lc.ORIGEM_ATEND not in ('EMERGENCIA ADULTO', 'EMERGENCIA INFANTIL')
    qualify row_number() over(
        partition by lc.ATENDIMENTO
        order by timestamp_diff(lc.DT_HR_ATENDIMENTO, u.DT_HR_TOTEM_RECEP, minute) asc
    ) = 1
),

retorno_48h as(
    select distinct a1.CD_ATENDIMENTO
    from atendimentos as a1
    inner join atendimentos as a2
    on a1.CD_PACIENTE = a2.CD_PACIENTE
    and a1.CID = a2.CID
    and a2.DT_ATENDIMENTO > a1.DT_ATENDIMENTO
    and a2.DT_ATENDIMENTO <= date_add(a1.DT_ATENDIMENTO, interval 2 day)
    and a1.CD_ATENDIMENTO != a2.CD_ATENDIMENTO
),

final as (
    select
       a.CD_ATENDIMENTO as atend_PA,
       a.CD_PACIENTE,
       a.IDADE,
       a.SEXO,
       a.CEP,
       a.CIDADE,
       a.UF,
       a.CONVENIO,
       a.SERVICO,
       a.COR_CLASSIF,
       a.PRESTADOR,
       a.ESPECIALIDADE,
       a.CID,
       a.MOTIVO_ALTA,
       a.DT_ATENDIMENTO,
       a.DT_HR_TOTEM_RECEP,
       a.CHAMADA_CLASSIFICACAO,
       a.INICIO_CLASSIFICACAO,
       a.DT_HR_CLASSIF_RISCO,
       a.CHAMADA_CAD_RECEP,
       a.DH_CADASTRO_RECEPCAO,
       a.FIM_CAD_RECEP,
       a.DH_ATEND_MEDICO,
       a.INI_ATD_MEDICO,
       a.FIM_ATD_MEDICO,
       a.DT_HR_ALTA,
       ai.ATENDIMENTO as atend_internacao,
       ai.ORIGEM_ATEND,
       ai.Destino,
       ai.Unidade,
       ai.Tipo,
       case
        when a.DT_HR_TOTEM_RECEP is null then null
        when extract(hour from a.DT_HR_TOTEM_RECEP) between 7 and 11 then 'Manhã'
        when extract(hour from a.DT_HR_TOTEM_RECEP) between 12 and 17 then 'Tarde'
        when extract(hour from a.DT_HR_TOTEM_RECEP) between 18 and 23 then 'Noite'
        else 'Madrugada' end as turno,
       case
        when a.IDADE is null then null
        when a.IDADE between 0 and 2 then '0 a 2'
        when a.IDADE between 3 and 5 then '3 a 5'
        when a.IDADE between 6 and 8 then '6 a 8'
        when a.IDADE between 9 and 11 then '9 a 11'
        when a.IDADE between 12 and 14 then '12 a 14'
        when a.IDADE between 15 and 19 then '15 a 19'
        when a.IDADE between 20 and 29 then '20 a 29'
        when a.IDADE between 30 and 39 then '30 a 39'
        when a.IDADE between 40 and 49 then '40 a 49'
        when a.IDADE between 50 and 59 then '50 a 59'
        else '60 ou mais' end as faixa_etaria,
       case
        when ai.ATENDIMENTO is not null then 1
        when cur.decisao = 'confirmado' then 1
        else 0 end as fl_conversao,
       case when r.CD_ATENDIMENTO is not null then 1 else 0 end as fl_retorno_48h,
       case when a.MOTIVO_ALTA = 'EVASAO' then 1 else 0 end as fl_evasao,
       case when pc.CD_ATENDIMENTO is not null then 1 else 0 end as fl_suspeito_conversao,
       a.competencia
    from atendimentos as a
    left join atendimento_com_internacoes as ai
    on a.CD_ATENDIMENTO = ai.CD_ATENDIMENTO
    left join retorno_48h as r
    on a.CD_ATENDIMENTO = r.CD_ATENDIMENTO
    left join possivel_conversao as pc
    on a.CD_ATENDIMENTO = pc.CD_ATENDIMENTO
    left join {{ source('curadoria', 'curadoria_conversao') }} as cur
    on a.CD_ATENDIMENTO = cur.CD_ATENDIMENTO
)

select * from final