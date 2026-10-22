-- tests/assert_return_rate_is_between_zero_and_one.sql
select
    product_id,
    returned_units,
    gross_units_sold,
    return_rate
from {{ ref('fct_prod_performance') }}
where return_rate is not null
  and (return_rate < 0 or return_rate > 1)