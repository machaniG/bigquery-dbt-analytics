-- models/marts/customer_analytics/marts_customers.sql
-- customer dimension

with transaction_lines as (
    select *
    from {{ ref('int_transformations') }}
    where customer_id is not null
),

customer_metrics as (
    select
        customer_id,
        country,
        min(transaction_date) as first_transaction_date,
        max(transaction_date) as last_transaction_date,
        count(distinct invoice_id) as lifetime_transaction_count,
        sum(signed_line_amount) as lifetime_net_amount
    from transaction_lines
    group by customer_id
)

select *
from customer_metrics