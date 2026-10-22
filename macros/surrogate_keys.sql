-- macros/surrogate_keys.sql
-- main purpose is to generate surrogate keys that can be used as unique-keys during incremental loading because the current 
-- dataset does not have a unique key. However, for production i will use dbt utils package.
{% macro generate_transaction_line_key(invoice_id, product_id, line_occurrence) %}

    md5(
        concat(
            coalesce(cast({{ invoice_id }} as string), '__null__'),
            '|',
            coalesce(cast({{ product_id }} as string), '__null__'),
            '|',
            coalesce(cast({{ line_occurrence }} as string), '__null__')
        )
    )

{% endmacro %}