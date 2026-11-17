#ai_eval/src/evaluator.py 

"""
Deterministic Hallucination & Faithfulness Scorer
Rather than relying solely on subjective LLM judges, I used deterministic ground-truth assertions 
alongside LLM checks to guarantee zero numerical hallucination.
"""
from dataclasses import dataclass
from src.models import DailyCountryBriefing


@dataclass
class EvalResult:
    passed: bool
    revenue_error_abs: float
    rate_error_abs: float
    risk_flag_accurate: bool
    failure_reasons: list[str]


def evaluate_briefing_faithfulness(
    records: list[dict], output: DailyCountryBriefing, tolerance: float = 0.05
) -> EvalResult:
    """Deterministically verify that LLM outputs match Gold mart ground-truth math."""
    failures: list[str] = []

    # Ground-truth calculations directly from source records
    expected_net_rev = round(sum(r["net_revenue"] for r in records), 2)
    total_gross = sum(r["gross_sales"] for r in records)
    total_returns = abs(sum(r["returns_and_cancellations"] for r in records))
    expected_rate = round((total_returns / total_gross) * 100, 2) if total_gross > 0 else 0.0
    expected_risk_flag = expected_rate > 15.0

    # Check 1: Numerical Faithfulness (Net Revenue)
    rev_diff = abs(output.total_net_revenue - expected_net_rev)
    if rev_diff > tolerance:
        failures.append(
            f"Hallucinated net_revenue: got {output.total_net_revenue}, expected {expected_net_rev}"
        )

    # Check 2: Derived Metric Faithfulness (Semantic Layer Ratio Formula)
    rate_diff = abs(output.return_cancellation_rate_pct - expected_rate)
    if rate_diff > tolerance:
        failures.append(
            f"Hallucinated return_rate: got {output.return_cancellation_rate_pct}%, expected {expected_rate}%"
        )

    # Check 3: Governance Policy Threshold Accuracy
    flag_ok = output.risk_flag == expected_risk_flag
    if not flag_ok:
        failures.append(
            f"Policy rule violation: risk_flag={output.risk_flag} for rate {expected_rate}%"
        )

    return EvalResult(
        passed=len(failures) == 0,
        revenue_error_abs=round(rev_diff, 4),
        rate_error_abs=round(rate_diff, 4),
        risk_flag_accurate=flag_ok,
        failure_reasons=failures,
    )
