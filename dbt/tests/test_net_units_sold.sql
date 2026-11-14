-- tests/assert_product_performance_reconciles.sql
-- assumes no other product movement types like exchanges, adjustments, or transfers
-- rule should be revised in case of other movement types
select
    product_id,
    gross_units_sold,
    returned_units,
    cancelled_units,
    net_units_moved
from {{ ref('fct_prod_performance') }}
where abs(
    net_units_moved
    - (gross_units_sold - returned_units - cancelled_units)
) > 0
