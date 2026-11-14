# Pandera Pre-Bronze Structural Quality Gate
"""
Pandera enforces required columns, data types, and invoice rules before data
reaches Bronze. Price and quantity sign patterns are logged separately and do
not reject otherwise valid rows.
"""
import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series

class OnlineRetailBronzeSchema(pa.DataFrameModel):
    """Contract enforced before landing Parquet files in the Bronze zone."""

    # Define the expected columns, data types, and validation rules for the Online Retail dataset
    """
    Add a regex validation rule on invoice that explicitly allows standard 6-digit invoices plus C (cancellations) and A (adjustments), 
    while still blocking truly corrupted invoice strings (like "ERROR" or random symbols)
    """
    invoice: Series[pa.String] = pa.Field(nullable=False, str_matches=r"^[CA]?\d{6}$", str_length={"min_value": 1})

    #stockcode 
    stock_code: Series[pa.String] = pa.Field(nullable=False, str_length={"min_value": 1})
    description: Series[pa.String] = pa.Field(nullable=True)
    quantity: Series[pa.Int64] = pa.Field(nullable=False, ne=0)
    invoice_date: Series[pd.DatetimeTZDtype] = pa.Field(
        dtype_kwargs={"tz": "UTC"}, nullable=False
    )
    unit_price: Series[pa.Float64] = pa.Field(nullable=False)
    customer_id: Series[pa.String] = pa.Field(nullable=True)
    country: Series[pa.String] = pa.Field(nullable=False, str_length={"min_value": 2})

    class Config:
        strict = False  # Allows metadata columns (ingested_at, batch_id) to pass through
        coerce = True

    @pa.dataframe_check
    def check_adjustment_invoice_rules(cls, df: pd.DataFrame) -> Series[bool]:
        """A-prefixed bad debt adjustments always have stock_code 'B' and no customer_id."""
        is_adjustment = df["invoice"].str.startswith("A")
        valid_adjustment = (df["stock_code"] == "B") & (df["customer_id"].isna())
        return (~is_adjustment) | valid_adjustment
