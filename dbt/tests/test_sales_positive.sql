-- tests/test_sales_positive
-- assert sales have positive signed amount 
select
    transaction_line_id,
    transaction_type,
    signed_line_amount
from {{ ref('int_transformations') }}
where transaction_type = 'sale'
  and signed_line_amount < 0