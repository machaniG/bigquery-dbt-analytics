-- models/marts/inventory/marts_inventory.sql
-- inventory fact
-- inventory can calculate sum(signed_quantity) as net_units_moved

select
    transaction_line_id,
    transaction_date,
    product_id,
    country,
    transaction_type,
    signed_quantity,
    signed_line_amount
from {{ ref('int_transformations') }}