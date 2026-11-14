-- tests/test_returns_cancellations.sql
-- assert returns and cancellations reduce revenue 

select
    transaction_line_id,
    transaction_type,
    signed_line_amount
from {{ ref('int_transformations') }}
where transaction_type in ('return', 'cancellation')
  and signed_line_amount > 0