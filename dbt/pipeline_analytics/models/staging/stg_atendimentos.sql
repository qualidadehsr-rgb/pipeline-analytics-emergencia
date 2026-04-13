-- referencia tabela de atendimentos
with source as (
    select * from {{source('raw', 'atendimentos')}}
),
tipado as (
    select
        * except(CD_PACIENTE, CD_ATENDIMENTO, IDADE, DT_ATENDIMENTO, DT_HR_TOTEM_RECEP,
                 CHAMADA_CLASSIFICACAO, INICIO_CLASSIFICACAO, DT_HR_CLASSIF_RISCO,
                 CHAMADA_CAD_RECEP, DH_CADASTRO_RECEPCAO, FIM_CAD_RECEP, DH_ATEND_MEDICO,
                 INI_ATD_MEDICO, FIM_ATD_MEDICO, DT_HR_ALTA),
        {{cast_inteiro('CD_PACIENTE')}} as CD_PACIENTE,
        {{cast_inteiro('CD_ATENDIMENTO')}} as CD_ATENDIMENTO,
        {{cast_inteiro('IDADE')}} as IDADE,
        {{cast_data('DT_ATENDIMENTO')}} as DT_ATENDIMENTO,
        {{cast_datetime('DT_HR_TOTEM_RECEP')}} as DT_HR_TOTEM_RECEP,
        {{cast_datetime('CHAMADA_CLASSIFICACAO')}} as CHAMADA_CLASSIFICACAO,
        {{ cast_datetime('INICIO_CLASSIFICACAO')}} as INICIO_CLASSIFICACAO,
        {{cast_datetime('DT_HR_CLASSIF_RISCO')}} as DT_HR_CLASSIF_RISCO,
        {{cast_datetime('CHAMADA_CAD_RECEP')}} as CHAMADA_CAD_RECEP,
        {{ cast_datetime('DH_CADASTRO_RECEPCAO')}} as DH_CADASTRO_RECEPCAO,
        {{ cast_datetime('FIM_CAD_RECEP')}} as FIM_CAD_RECEP,
        {{ cast_datetime('DH_ATEND_MEDICO')}} as DH_ATEND_MEDICO,
        {{ cast_datetime('INI_ATD_MEDICO')}} as INI_ATD_MEDICO,
        {{ cast_datetime('FIM_ATD_MEDICO')}} as FIM_ATD_MEDICO,
        {{cast_datetime('DT_HR_ALTA')}} as DT_HR_ALTA
    from source
),
transformado as(
    select
        CD_PACIENTE,
        CD_ATENDIMENTO,
        IDADE,
        SEXO,
        CEP,
        CIDADE,
        UF,
        CONVENIO,
        case
            when IDADE < 15 AND
            ESPECIALIDADE != 'CIRURGIA GERAL' AND
            ESPECIALIDADE != 'ORTOPEDIA/TRAUMATOLOGIA' THEN 'PEDIATRIA'
            when ESPECIALIDADE = 'CIRURGIA GERAL' THEN 'CIRURGIA GERAL'
            when ESPECIALIDADE = 'ORTOPEDIA/TRAUMATOLOGIA' THEN 'ORTOPEDIA/TRAUMATOLOGIA'
            when ESPECIALIDADE = 'MEDICO CARDIOLOGISTA' OR ESPECIALIDADE = 'CIRURGIA CARDIOVASCULAR' THEN 'CARDIOLOGIA'
            when IDADE > 14 AND
            (ESPECIALIDADE = 'CLINICA MEDICA' OR ESPECIALIDADE = 'GENERALISTA') THEN 'CLINICA MEDICA'
            ELSE 'OUTROS'
        end as SERVICO,
        DT_ATENDIMENTO,
        DT_HR_TOTEM_RECEP,
        CHAMADA_CLASSIFICACAO,
        INICIO_CLASSIFICACAO,
        DT_HR_CLASSIF_RISCO,
        CLASSIFICACAO,
        replace(COR_CLASSIF, 'AMARELO1', 'AMARELO') as COR_CLASSIF,
        CHAMADA_CAD_RECEP,
        DH_CADASTRO_RECEPCAO,
        FIM_CAD_RECEP,
        DH_ATEND_MEDICO,
        INI_ATD_MEDICO,
        FIM_ATD_MEDICO,
        trim(split(PRESTADOR, ' - ')[offset(1)]) as PRESTADOR,
        ESPECIALIDADE,
        CID,
        DT_HR_ALTA,
        MOTIVO_ALTA
    from tipado
)
select * from transformado
