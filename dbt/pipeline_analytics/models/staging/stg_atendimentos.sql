-- referencia tabela de atendimentos
with source as (
    select * from {{source('raw', 'atendimentos')}}
),
transformado as(
    select
        * except(COR_CLASSIF, PRESTADOR, SERVICO),
        replace(COR_CLASSIF, 'AMARELO1', 'AMARELO') as COR_CLASSIF,
        trim(split(PRESTADOR, ' - ')[offset(1)]) as PRESTADOR,
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
        end as SERVICO
    from source
)
select * from transformado
