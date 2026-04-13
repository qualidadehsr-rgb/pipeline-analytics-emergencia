{% macro cast_datetime(coluna) %}
    cast({{coluna}} as datetime)
{% endmacro %}