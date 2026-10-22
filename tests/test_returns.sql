-- tests/test_returns.sql
-- assert that returns have negative quantity
-- should return any transaction/row classified as return but has quantity of either zero or more
-- which will indicate wrong classification
select
    transaction_line_id,
    quantity,
    transaction_type
from {{ ref('int_transformations') }}
where transaction_type = 'return'
  and quantity >= 0