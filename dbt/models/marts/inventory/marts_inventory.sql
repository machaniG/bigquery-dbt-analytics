-- models/marts/inventory/marts_inventory.sql
-- inventory fact
-- inventory can calculate sum(signed_quantity) as net_units_moved

select
    transaction_line_id,
    invoice_id,
    transaction_date,
    product_id,
    country,
    transaction_type,
    quantity,
    signed_quantity,
    gross_line_amount,
    signed_line_amount,
    product_description
from {{ ref('int_transformations') }}