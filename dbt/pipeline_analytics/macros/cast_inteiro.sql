{% macro cast_inteiro(coluna)%}
    cast({{coluna}} as INT64)
{% endmacro%}