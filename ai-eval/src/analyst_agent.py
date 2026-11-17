#ai_eval/src/analyst_agent.py 
# Grounded Gold Mart Consumer
"""This module pulls verified rows from fct_daily_sales Gold mart in BigQuery 
and asks Gemini 2.5 Flash to synthesize a structured financial briefing for executives. 
The output is strictly validated against a Pydantic schema to ensure reliability and prevent unstructured or malformed responses.
"""

import json
import os
from google import genai
from google.genai import types
from google.cloud import bigquery

from src.models import DailyCountryBriefing


def fetch_gold_country_metrics(
    project_id: str, dataset_id: str, country: str, limit_days: int = 7
) -> list[dict]:
    """Query verified metrics from the contracted Gold mart in BigQuery."""
    client = bigquery.Client(project=project_id)
    query = f"""
        SELECT
            CAST(transaction_date AS STRING) AS transaction_date,
            country,
            CAST(gross_sales AS FLOAT64) AS gross_sales,
            CAST(returns_and_cancellations AS FLOAT64) AS returns_and_cancellations,
            CAST(net_revenue AS FLOAT64) AS net_revenue,
            net_units_moved
        FROM `{project_id}.{dataset_id}.fct_daily_sales`
        WHERE country = @country
        ORDER BY transaction_date DESC
        LIMIT @limit_days
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("country", "STRING", country),
            bigquery.ScalarQueryParameter("limit_days", "INT64", limit_days),
        ]
    )
    rows = client.query(query, job_config=job_config).result()
    return [dict(row) for row in rows]


def generate_grounded_briefing(
    records: list[dict], country: str, project_id: str, location: str = "europe-west3"
) -> DailyCountryBriefing | None:
    """Generate a schema-enforced executive briefing grounded strictly in Gold data."""
    # Governance Non-Response Rule: Refuse to generate if upstream Gold data is empty
    if not records:
        return None

    client = genai.Client(vertexai=True, project=project_id, location=location)

    prompt = f"""
    You are a strict financial reliability analyst. Generate an executive briefing for {country}
    using ONLY the verified Gold mart records below.
    
    Rules:
    1. Calculate total_net_revenue as the exact sum of net_revenue across all provided rows.
    2. Calculate return_cancellation_rate_pct as:
       (ABS(SUM(returns_and_cancellations)) / NULLIF(SUM(gross_sales), 0)) * 100, rounded to 2 decimals.
    3. Set risk_flag to true ONLY if return_cancellation_rate_pct > 15.0.
    4. Do NOT invent or extrapolate any numbers not directly supported by the data.

    Verified Gold Records:
    {json.dumps(records, indent=2)}
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DailyCountryBriefing,
            #temperature=0.0,  # Deterministic output for maximum reliability
        ),
    )

    return DailyCountryBriefing.model_validate_json(response.text)
