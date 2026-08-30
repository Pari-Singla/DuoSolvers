# DuoSolver: Business Intelligence-to-Action Engine

## Problem Framing
Modern companies have real-time dashboards but lack real-time understanding. When a metric changes, finding the root cause takes 2–5 days of manual work.

## Solution
A hybrid deterministic + AI engine that:
1. Detects anomalies with statistical confidence.
2. Breaks down metrics mathematically (Volume × Price × Mix).
3. Generates LLM hypotheses but **validates them with SQL** against raw data.
4. Abstains if confidence < 60% or evidence is contradictory.
5. Delivers persona-specific narratives (Manager/Analyst/Executive).

## Target Users
- **Regional Managers**: Get answers in minutes.
- **Analysts**: Spend less time on repetitive "why" queries.
- **Leadership**: Faster evidence-backed decisions.

## Business Impact
- Cuts root-cause analysis time from 3 days to **< 3 minutes**.
- Saves ~$500K/year in analyst productivity for a mid-sized enterprise.

## Roadmap
- **Phase 1 (Current)**: SQLite + Python prototype.
- **Phase 2**: Connect to Snowflake/Databricks, add Streamlit UI.
- **Phase 3**: Implement persistent feedback loops and scale to 50+ KPIs.

## Risks & Mitigations
- **Hallucination**: SQL validation gate discards unsupported LLM claims.
- **Sparse history**: Cohort proxy from similar established products.
- **Cost**: Residual gating reduces LLM calls by ~60%.