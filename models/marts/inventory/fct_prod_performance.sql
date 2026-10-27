-- models/marts/inventory/fct_prod_performance.sql
-- product performance mart
-- deeper dig mart: one row per product, with additive measures and a calculated return rate.

with product_movement as (
    select *
    from {{ ref('marts_inventory') }}
),

product_metrics as (
    select
        product_id,
        transaction_date,

        count(distinct invoice_id) as invoice_count,
        
        -- Gross sales units
        sum(
            case
                when transaction_type = 'sale'
                    then quantity
                else 0
            end
        ) as gross_units_sold,

        -- Returned units that represent physical returns
        sum(
            case
                when transaction_type = 'return'
                    then abs(quantity)
                else 0
            end
        ) as returned_units,

        -- include cancellations 
        sum(
            case when transaction_type = 'cancellation' then abs(quantity) else 0 end
        ) as cancelled_units,

        -- sum net units sold from signed_quantity
        -- but exclude adjust transactions
        sum(
            case
                when transaction_type in ('sale', 'return', 'cancellation')
                    then signed_quantity
                else 0
            end
        ) as net_units_moved,
        --sum(signed_quantity) as net_units_moved,

        sum(
            case
                when transaction_type = 'sale'
                    then gross_line_amount
                else 0
            end
        ) as gross_sales,

        sum(signed_line_amount) as net_revenue,

        min(transaction_date) as first_transaction_date,
        max(transaction_date) as last_transaction_date


    from product_movement
    group by product_id, transaction_date
)

select
    product_id,
    invoice_count,
    gross_units_sold,
    returned_units,
    cancelled_units,
    net_units_moved,
    gross_sales,
    net_revenue,
    transaction_date,

    -- Return rate: returned units divided by gross units sold.
    -- Use safe division to avoid errors when a product has no sales.
    safe_divide(
        returned_units,
        gross_units_sold
    ) as raw_return_rate,

    -- Cap it at 1.0 (100%) just in case returns exceed recorded sales
    least(
        safe_divide(returned_units, gross_units_sold),
    1.0
    ) as return_rate,

    first_transaction_date,
    last_transaction_date

from product_metrics