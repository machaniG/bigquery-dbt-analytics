-- tests/test_sales.sql
-- assert that sales have positive quantities
-- should return bad rows where quantity is either zero or negative yet classified as sale
select
    transaction_line_id,
    quantity,
    transaction_type
from {{ ref('int_transformations') }}
where transaction_type = 'sale'
  and quantity <= 0