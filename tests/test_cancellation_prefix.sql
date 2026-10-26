-- tests/test_cancellation_prefix.sql
-- assert cancellations have 'c'prefix 
-- to test the consequences of my classification rule used to derive transaction_type
-- should catch any row wrongly classified as cancellation yet it doesn't have a 'C' prefix in invoice
select
    transaction_line_id,
    transaction_at,
    transaction_type
from {{ ref('int_transformations') }}
where transaction_type = 'cancellation'
  and upper(left(transaction_id, 1)) != 'C'