-- Correções da curadoria (lógica de negócio e integridade) em uma linha por atendimento, para uso no modelo atendimentos_pa
with decisao_logica as(
    select ci.nr_atendimento, dl.flag_prevalece
    from {{ source('curadoria', 'curadoria_decisao_logica') }} as dl
    inner join {{ source('curadoria', 'curadoria_inconsistencias') }} as ci
    on dl.id_inconsistencia = ci.id_inconsistencia
),

imputacao_integridade as(
    select ci.nr_atendimento, ii.campo_afetado, ii.valor_imputado
    from {{ source('curadoria', 'curadoria_imputacao_integridade') }} as ii
    inner join {{ source('curadoria', 'curadoria_inconsistencias') }} as ci
    on ii.id_inconsistencia = ci.id_inconsistencia
),

integridade_pivotada as(
    select
        nr_atendimento,
        max(case when campo_afetado = 'CD_PACIENTE' then valor_imputado end) as CD_PACIENTE_corrigido,
        max(case when campo_afetado = 'IDADE' then valor_imputado end) as IDADE_corrigido,
        max(case when campo_afetado = 'SEXO' then valor_imputado end) as SEXO_corrigido,
        max(case when campo_afetado = 'CEP' then valor_imputado end) as CEP_corrigido,
        max(case when campo_afetado = 'CIDADE' then valor_imputado end) as CIDADE_corrigido,
        max(case when campo_afetado = 'UF' then valor_imputado end) as UF_corrigido,
        max(case when campo_afetado = 'CONVENIO' then valor_imputado end) as CONVENIO_corrigido,
        max(case when campo_afetado = 'SERVICO' then valor_imputado end) as SERVICO_corrigido,
        max(case when campo_afetado = 'COR_CLASSIF' then valor_imputado end) as COR_CLASSIF_corrigido,
        max(case when campo_afetado = 'PRESTADOR' then valor_imputado end) as PRESTADOR_corrigido,
        max(case when campo_afetado = 'ESPECIALIDADE' then valor_imputado end) as ESPECIALIDADE_corrigido,
        max(case when campo_afetado = 'CID' then valor_imputado end) as CID_corrigido,
        max(case when campo_afetado = 'MOTIVO_ALTA' then valor_imputado end) as MOTIVO_ALTA_corrigido,
        max(case when campo_afetado = 'DT_ATENDIMENTO' then valor_imputado end) as DT_ATENDIMENTO_corrigido,
        max(case when campo_afetado = 'DT_HR_TOTEM_RECEP' then valor_imputado end) as DT_HR_TOTEM_RECEP_corrigido,
        max(case when campo_afetado = 'DT_HR_CLASSIF_RISCO' then valor_imputado end) as DT_HR_CLASSIF_RISCO_corrigido,
        max(case when campo_afetado = 'INI_ATD_MEDICO' then valor_imputado end) as INI_ATD_MEDICO_corrigido,
        max(case when campo_afetado = 'FIM_ATD_MEDICO' then valor_imputado end) as FIM_ATD_MEDICO_corrigido,
        max(case when campo_afetado = 'DT_HR_ALTA' then valor_imputado end) as DT_HR_ALTA_corrigido
    from imputacao_integridade
    group by nr_atendimento
),

final as(
    select
        coalesce(dl.nr_atendimento, ip.nr_atendimento) as nr_atendimento,
        flag_prevalece,
        ip.CD_PACIENTE_corrigido,
        ip.IDADE_corrigido,
        ip.SEXO_corrigido,
        ip.CEP_corrigido,
        ip.CIDADE_corrigido,
        ip.UF_corrigido,
        ip.CONVENIO_corrigido,
        ip.SERVICO_corrigido,
        ip.COR_CLASSIF_corrigido,
        ip.PRESTADOR_corrigido,
        ip.ESPECIALIDADE_corrigido,
        ip.CID_corrigido,
        ip.MOTIVO_ALTA_corrigido,
        ip.DT_ATENDIMENTO_corrigido,
        ip.DT_HR_TOTEM_RECEP_corrigido,
        ip.DT_HR_CLASSIF_RISCO_corrigido,
        ip.INI_ATD_MEDICO_corrigido,
        ip.FIM_ATD_MEDICO_corrigido,
        ip.DT_HR_ALTA_corrigido
    from decisao_logica as dl
    full outer join integridade_pivotada as ip
    on dl.nr_atendimento = ip.nr_atendimento
)
select * from final