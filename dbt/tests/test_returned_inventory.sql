-- tests/test_returned_invenotry.sql
-- assert returns increase inventory availability 
select
    transaction_line_id,
    transaction_type,
    signed_quantity
from {{ ref('marts_inventory') }}
where transaction_type = 'return'
  and signed_quantity >= 0