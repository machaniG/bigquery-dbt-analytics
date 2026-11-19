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
            -- 1. Business meaning first: what the line IS
            --    (accounting adjustments & non-product fees/carriage)
            when upper(left(invoice_id, 1)) = 'A'
                 or product_id in ('B', 'POST', 'M', 'DOT', 'AMAZONFEE', 'C2', 'BANK CHARGES')
                then 'adjustment'

            -- 2. Booking conventions second: how the line is RECORDED
            when upper(left(invoice_id, 1)) = 'C' then 'cancellation'
            when quantity < 0 then 'return'

            -- 3. Regular trade
            when quantity > 0 and unit_price > 0 then 'sale'
            else 'unknown'
        end as transaction_type
    from renamed
)

select
    *
from classified