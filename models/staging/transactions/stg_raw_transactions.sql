-- models/staging/transactions/stg_raw_transactions.sql
-- prepares a clean version of the raw table

with source as (
    select *
    from {{ source('transaction_events', 'transaction_data') }} -- source name and table name in sources.yml
),

renamed as (
    select
        cast(invoice as string) as invoice_id,
        cast(stock_code as string) as product_id,
        nullif(trim(description), '') as product_description,
        cast(quantity as int64) as quantity,
        timestamp(invoicedate) as transaction_at,
        cast(price as numeric) as unit_price,
        cast(customerid as string) as customer_id,
        initcap(trim(country)) as country,

        -- ingestion metadata added by the daily loader
        ingested_at,
        ingest_date

    from source
),

classified as (
    select
        *,
        case
            when upper(left(invoice_id, 1)) = 'C' then 'cancellation'
            when quantity < 0 then 'return'
            when quantity > 0 then 'sale'
            else 'unknown'
        end as transaction_type
    from renamed
)

select
    *
from classified