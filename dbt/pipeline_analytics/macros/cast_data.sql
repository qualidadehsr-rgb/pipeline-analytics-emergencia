{% macro cast_data(coluna) %}
    cast({{coluna}} as date)
{% endmacro %}