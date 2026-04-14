{% macro cast_time(coluna) %}
    cast(concat({{coluna}}, ':00') as time)
{% endmacro %}