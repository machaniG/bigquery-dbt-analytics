-- models/staging/transactions/stg_raw_transactions.sql
-- prepares a clean version of the raw table
-- test sales have positive signed-line-amount in int-model failed 
-- investigated found reason to be because of rows with positive quantities but negative price
-- updated classification logic to account for this 

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
        timestamp(invoice_date) as transaction_at,
        cast(unit_price as numeric) as unit_price,
        cast(customer_id as string) as customer_id,
        initcap(trim(country)) as country,

        -- ingestion metadata added by the daily loader
        ingested_at,
        date(ingested_at, 'Europe/Berlin') as ingest_date

    from source
),

classified as (
    select
        *,
        case
            when upper(left(invoice_id, 1)) = 'C' AND (quantity >= 0 AND unit_price >= 0) then 'cancellation'
            when quantity < 0 OR unit_price < 0 then 'return' 
            when quantity > 0 AND unit_price > 0 then 'sale'
            else 'unknown'
        end as transaction_type
    from renamed
)

select
    *
from classified