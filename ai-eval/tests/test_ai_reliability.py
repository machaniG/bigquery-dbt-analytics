# ai_eval/tests/test_ai_reliability.py 
"""
(CI/CD Quality Gate)

A fast unit tests (which run in CI/CD without spending cloud credits) plus an integration marker for live Vertex AI evaluation
"""

import pytest
from src.models import DailyCountryBriefing
from src.evaluator import evaluate_briefing_faithfulness
from src.analyst_agent import generate_grounded_briefing


@pytest.fixture
def sample_gold_records() -> list[dict]:
    return [
        {
            "transaction_date": "2010-12-01",
            "country": "Germany",
            "gross_sales": 1000.00,
            "returns_and_cancellations": -200.00,
            "net_revenue": 800.00,
            "net_units_moved": 120,
        },
        {
            "transaction_date": "2010-12-02",
            "country": "Germany",
            "gross_sales": 500.00,
            "returns_and_cancellations": -50.00,
            "net_revenue": 450.00,
            "net_units_moved": 60,
        },
    ]


def test_evaluator_passes_faithful_llm_output(sample_gold_records: list[dict]) -> None:
    """Verify faithful briefing passes all numerical and policy checks."""
    # Expected net_revenue = 1250.00; return_rate = (250 / 1500) * 100 = 16.67% (>15% -> risk_flag=True)
    faithful_output = DailyCountryBriefing(
        country="Germany",
        date_range="2010-12-01 to 2010-12-02",
        total_net_revenue=1250.00,
        return_cancellation_rate_pct=16.67,
        risk_flag=True,
        executive_summary="Germany generated 1250.00 in net revenue with a 16.67% return rate.",
    )

    result = evaluate_briefing_faithfulness(sample_gold_records, faithful_output)
    assert result.passed is True
    assert result.failure_reasons == []


def test_evaluator_catches_hallucinated_revenue(sample_gold_records: list[dict]) -> None:
    """Verify evaluator blocks LLM output when numbers diverge from Gold mart."""
    hallucinated_output = DailyCountryBriefing(
        country="Germany",
        date_range="2010-12-01 to 2010-12-02",
        total_net_revenue=1500.00,  # Wrong: reported gross instead of net!
        return_cancellation_rate_pct=16.67,
        risk_flag=True,
        executive_summary="Germany generated 1500.00 in net revenue.",
    )

    result = evaluate_briefing_faithfulness(sample_gold_records, hallucinated_output)
    assert result.passed is False
    assert any("Hallucinated net_revenue" in msg for msg in result.failure_reasons)


def test_governance_non_response_on_empty_gold_data() -> None:
    """Verify agent refuses to generate when upstream Gold mart returns 0 rows."""
    output = generate_grounded_briefing(records=[], country="Mars", project_id="dummy-project")
    assert output is None
