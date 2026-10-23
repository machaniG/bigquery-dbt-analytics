-- tests/test_non_negative.sql
-- assert that sales are non_negative
-- Sales should have positive signed_line_amount
select
    transaction_line_id,
    transaction_type,
    signed_line_amount
from {{ ref('int_transformations') }}
where transaction_type = 'sale'
  and signed_line_amount < 0