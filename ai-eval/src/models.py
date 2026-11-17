# ai_eval/src/models.py (Pydantic Output Contract)

"""Enforcing a strict Pydantic schema ensures the LLM can never return unstructured rambles or malformed JSON"""

from pydantic import BaseModel, Field


class DailyCountryBriefing(BaseModel):
    """Structured executive briefing grounded strictly in Gold mart metrics."""

    country: str = Field(description="Country name exactly as reported in the mart")
    date_range: str = Field(description="Start and end dates covered")
    total_net_revenue: float = Field(description="Exact sum of net_revenue from source data")
    return_cancellation_rate_pct: float = Field(
        description="Calculated return and cancellation rate percentage (0 to 100)"
    )
    risk_flag: bool = Field(
        description="True if return_cancellation_rate_pct exceeds 15.0%, otherwise False"
    )
    executive_summary: str = Field(
        description="Concise 2-sentence summary citing only numbers present in the input table"
    )
