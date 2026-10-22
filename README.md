# Data-quality-observability

## 
- Marts contain the prepared data products.
- Semantic models describe their entities, dimensions, and measures.
- Metrics define the governed KPIs.
- Saved queries package those KPIs for a team or dashboard.

- **This gives Finance, Inventory, and Customer Analytics a shared, version-controlled definition of net_revenue, net_units_moved, product_return_rate, and customer_lifetime_value.**

## Staging

Prepares a clean version of the raw table and derives transaction type.

## Intermediate

Prepares fact grain by turning classified staging lines into a stable, finance- and inventory-ready transaction-line grain.

| Responsibility | Example in the project |
| ------------------ | -----------------|
| Create a stable surrogate key | transaction_line_id from invoice, product, and line occurrence |
| Enforce one clear grain  | One row per invoice–product-line occurrence |
| Apply signed business values | Refunds/cancellations become negative revenue and quantity |
| Handle duplicates deliberately | Keep exact duplicate lines only if they are genuine separate lines; otherwise deduplicate with a documented rule |
| Join reference/enrichment data | Product attributes, customer attributes, country mapping, calendar |
| Prepare reusable calculations | gross_line_amount, signed_line_amount, signed_quantity |
| Isolate complex logic | So fct_transaction_lines remains simple and readable |

----

# Tests

## 1. Test derived logic

Testing the classification rule:

    - test_sales
    - test_returns
    - test_cancellations

## 2. Test sign conventions

The intermediate model promises:

- Sales have positive signed_line_amount.
- Returns/cancellations have non-positive signed_line_amount.
- signed_line_amount has the same magnitude as gross_line_amount. 
- These two tests protect Finance from accidentally reporting refunds as revenue.

    - test_non_negative
    - test_non_positive

## 3. Custom business tests

- Should return zero rows when valid.

    - test_net_revenue
    - test_returns_cancellations
    - test_sales_positive
    - test_returned_inventory



