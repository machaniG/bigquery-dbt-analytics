-- tests/test_exclude_fee_lines.sql
-- assert that amazon fee lines are excluded from trade types
-- Returns zero rows when healthy; any misclassification 
--including someone reordering the CASE back later, fails the build
select *
from {{ ref('stg_raw_transactions') }}
where product_id in ('B', 'POST', 'M', 'DOT', 'AMAZONFEE', 'C2', 'BANK CHARGES')
  and transaction_type in ('sale', 'return', 'cancellation')