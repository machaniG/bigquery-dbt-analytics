-- models/intermediate/transactions/int_transformations.sql
-- prepares the fact grain: turns classified staging lines into a stable, fincance-, inventory etc ready transactions
{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='transaction_line_id'
) }}

with transaction_lines as (
    select *
    from {{ ref('stg_raw_transactions') }}

    {% if is_incremental() %}
    where ingested_at >= (
        select coalesce(max(ingested_at), timestamp '2010-01-01')
        from {{ this }}
    )
    {% endif %}
),

line_numbers as (
    select
        *,
        row_number() over (
            partition by invoice_id, product_id
            order by transaction_at, quantity, unit_price
        ) as line_occurrence
    from transaction_lines
),

keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(
            ['invoice_id', 'product_id', 'line_occurrence']
        ) }} as transaction_line_id,

        invoice_id,
        product_id,
        product_description,
        transaction_at,
        date(transaction_at) as transaction_date,
        customer_id,
        country,
        quantity,
        unit_price,
        quantity * unit_price as gross_line_amount,
        transaction_type,
        ingested_at,
        ingest_date
    from line_numbers
),

signed as (
    select
        *,
        case
            when transaction_type in ('cancellation', 'return')
                then -abs(gross_line_amount)
            else gross_line_amount
        end as signed_line_amount,

        case
            when transaction_type in ('cancellation', 'return')
                then -abs(quantity)
            else quantity
        end as signed_quantity
    from keyed
)

select *
from signed