-- models/marts/inventory/dim_products.sql
-- product dimension. descriptive and does not contain performance metrics that change with reporting period

with product_movement as (
    select *
    from {{ ref('marts_inventory') }}
),

product_attributes as (
    select
        product_id,

        -- Choose the most recent non-null description.
        -- UCI descriptions can be inconsistent for the same StockCode.
        array_agg(
            product_description
            ignore nulls
            order by transaction_date desc
            limit 1
        )[offset(0)] as product_description,

        min(transaction_date) as first_seen_date,
        max(transaction_date) as last_seen_date

    from product_movement
    group by product_id
)

select
    product_id,
    product_description,
    first_seen_date,
    last_seen_date
from product_attributes