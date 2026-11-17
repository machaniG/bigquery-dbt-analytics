# ai_eval/src/run_live_eval.py

"""Live end-to-end test: Query BigQuery Gold mart -> Generate Gemini Briefing -> Run Hallucination Gate."""

import logging
import os

from src.analyst_agent import fetch_gold_country_metrics, generate_grounded_briefing
from src.evaluator import evaluate_briefing_faithfulness

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)


def main() -> None:
    project_id = os.environ["GCP_PROJECT_ID"]
    gold_dataset = os.getenv("GOLD_DATASET", "dbt_analytics26_finance")  # Update to your exact dataset name
    location = os.getenv("GCP_REGION", "europe-west3")

    for country in ["United Kingdom", "Germany", "France"]:
        LOGGER.info("Fetching Gold mart metrics for %s...", country)
        records = fetch_gold_country_metrics(
            project_id=project_id,
            dataset_id=gold_dataset,
            country=country,
            limit_days=7,
        )

        if not records:
            LOGGER.warning("No Gold records found for %s. Non-response guardrail triggered.", country)
            continue

        LOGGER.info("Generating grounded Gemini briefing for %s (%d days)...", country, len(records))
        briefing = generate_grounded_briefing(
            records=records,
            country=country,
            project_id=project_id,
            location=location,
        )

        eval_result = evaluate_briefing_faithfulness(records=records, output=briefing)

        print(f"\n--- {country} Executive Briefing ---")
        print(briefing.model_dump_json(indent=2))
        print(f"Hallucination Gate Passed: {eval_result.passed} | Failures: {eval_result.failure_reasons}\n")

        if not eval_result.passed:
            raise RuntimeError(f"AI Reliability Gate FAILED for {country}: {eval_result.failure_reasons}")


if __name__ == "__main__":
    main()
