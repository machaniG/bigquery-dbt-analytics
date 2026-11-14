-- tests/test_net_revenue.sql
-- assert finance net revenue is reconciled 

with daily_sales as (
    select *
    from {{ ref('fct_daily_sales') }}
)

select
    transaction_date,
    country,
    net_revenue,
    gross_sales,
    returns_and_cancellations
from daily_sales
where abs(
    net_revenue - (gross_sales + returns_and_cancellations)
) > 0.01