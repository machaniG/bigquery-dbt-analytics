-- macros/normalize_timestamp.sql
-- normalize timestamp columns so downstream models do not each have to guess whether transaction_at is a string, date, or timestamp

{% macro normalize_timestamp(column_name, source_timezone='UTC') %}

    timestamp(
        {% if target.type == 'bigquery' %}
            timestamp({{ column_name }}, '{{ source_timezone }}')
        {% else %}
            convert_timezone(
                '{{ source_timezone }}',
                'UTC',
                {{ column_name }}
            )
        {% endif %}
    )

{% endmacro %}