-- models/marts/finance/marts_finance.sql
-- finance fact
-- finance can calculate "sum(signed_line_amount) as net_revenue"
-- summing positive sales and negative returns will still give the correct net_revenue 

select
    transaction_line_id,
    invoice_id,
    transaction_date,
    customer_id,
    product_id,
    country,
    transaction_type,
    gross_line_amount,
    signed_line_amount
from {{ ref('int_transformations') }}