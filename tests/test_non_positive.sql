-- tests/test_non_positive.sql
-- assert refunds and cancellations are non-positive
-- Returns/cancellations have non-positive signed_line_amount.

select
    transaction_line_id,
    transaction_type,
    signed_line_amount
from {{ ref('int_transformations') }}
where transaction_type in ('return', 'cancellation')
  and signed_line_amount > 0