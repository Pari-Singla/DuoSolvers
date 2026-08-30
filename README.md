# DuoSolvers: KPI Intelligence-to-Action Engine

##  Problem Statement
Most BI tools show **what** changed. DuoSolver shows **why** and **what to do**—with mathematical proof and cost-aware AI.

##  Key Differentiators (Why we stand out)
1. **LLM as a Clerk, not an Oracle**: LLM generates hypotheses; SQL validates them against raw data. No hallucinations.
2. **Active Abstention**: If confidence < 60%, we say "I don't know" and prescribe the next analysis.
3. **Cost-Aware Gating**: Deterministic contribution runs first; LLM only invoked for the residual (>15%).
4. **Sparse-History Proxy**: New products use cohort averages from similar products.
5. **Role-Based Security & Lineage**: Managers see only their region; analysts see the full SQL audit trail.

##  Architecture
- **Signal Layer**: Rolling Z-score anomaly detection.
- **Diagnosis Layer**: Deterministic decomposition (Volume × Price × Mix) + LLM hypothesis generation + SQL validation.
- **Action Layer**: Persona-specific narratives + structured recommendations + abstention logic.

##  Dependencies
- Python 3.9+
- Libraries: `fastapi`, `uvicorn`, `streamlit`, `pandas`, `numpy`, `requests`
