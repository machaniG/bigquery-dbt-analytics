with transaction_lines as (
    select
        transaction_date,
        invoice_id,
        customer_id,
        country,
        transaction_type,
        gross_line_amount,
        signed_line_amount,
        signed_quantity
    from {{ ref('int_transformations') }}

    -- Add a partition filter if the model is partitioned
    -- where transaction_date >= date_sub(current_date(), interval 90 day)
)

select
    transaction_date,
    country,

    sum(
        case
            when transaction_type = 'sale'
                then gross_line_amount
            else 0
        end
    ) as gross_sales,

    sum(
        case
            when transaction_type in ('return', 'cancellation')
                then signed_line_amount
            else 0
        end
    ) as returns_and_cancellations,

    -- sum(signed_line_amount) as net_revenue,
    SUM(
        CASE
            WHEN transaction_type IN ('sale', 'return', 'cancellation')
             THEN signed_line_amount
            ELSE 0
        END
    ) AS net_revenue,


    sum(signed_quantity) as net_units_moved,

    -- Line-count metrics should the finance team want to look at the financial impact of returns
    -- here i am using portable sql
    /* commenting this for now
    sum(case when transaction_type = 'sale' then 1 else 0 end) as sale_line_count,
    sum(case when transaction_type = 'return' then 1 else 0 end) as return_line_count,
    sum(case when transaction_type = 'cancellation' then 1 else 0 end) as cancellation_line_count
    */

    /* for bigquerysql
    countif(transaction_type = 'sale') as sale_line_count,
    countif(transaction_type = 'return') as return_line_count,
    countif(transaction_type = 'cancellation') as cancellation_line_count,
    */

    -- Distinct metrics
    count(distinct invoice_id) as invoice_count,
    count(distinct customer_id) as known_customer_count

from transaction_lines
group by
    transaction_date,
    country