# src/llm_orchestrator.py
import sqlite3
import pandas as pd

class LLMOrchestrator:
    def __init__(self, db_path="data/kpi.db"):
        self.db_path = db_path
        self.use_real_llm = False
    
    def generate_hypotheses(self, anomaly_event, contribution_result, context=""):
        if not context:
            context = """
            Recent business context:
            - Marketing spend in East region decreased 15% in May.
            - Competitor 'X' launched a discount campaign in June.
            - Support tickets in East region increased 20% last week.
            """
        
        # Simulating LLM response (replace with openai.ChatCompletion.create if needed)
        mock_hypotheses = [
            {
                "id": "h1",
                "description": f"Volume drop in {anomaly_event.get('dimensions', {}).get('region', 'East')} region due to reduced marketing spend in May (15% decrease).",
                "initial_likelihood": "High",
                "validation_query": "SELECT SUM(spend) FROM marketing_spend WHERE region = 'East' AND date BETWEEN '2026-05-01' AND '2026-05-31'",
                "missing_data": "None",
                "validated": False,
                "validation_result": None
            },
            {
                "id": "h2",
                "description": "Competitor discount campaign diverted customers.",
                "initial_likelihood": "Medium",
                "validation_query": "SELECT * FROM competitor_data WHERE region = 'East'",  # Simulates missing table
                "missing_data": "Competitor pricing data is not available.",
                "validated": False,
                "validation_result": None
            },
            {
                "id": "h3",
                "description": "Seasonal downturn affecting East region.",
                "initial_likelihood": "Low",
                "validation_query": "SELECT AVG(units_sold) FROM orders WHERE region IN ('North','South') AND date BETWEEN '2026-06-01' AND '2026-06-15'",
                "missing_data": "None",
                "validated": False,
                "validation_result": None
            }
        ]
        
        if anomaly_event.get('is_sparse_history', False):
            mock_hypotheses.append({
                "id": "h4",
                "description": "New product (C) performance is unstable due to insufficient historical data.",
                "initial_likelihood": "Unknown",
                "validation_query": "SELECT units_sold FROM orders WHERE product_line = 'C'",
                "missing_data": "Only 7 days of history available. Need 14+ days.",
                "validated": False,
                "validation_result": None,
                "low_confidence": True
            })
        
        return mock_hypotheses
    
    def validate_hypotheses(self, hypotheses):
        conn = sqlite3.connect(self.db_path)
        validated = []
        for hyp in hypotheses:
            if "missing" in hyp.get('missing_data', '').lower() and "not available" in hyp.get('missing_data', '').lower():
                hyp['validation_result'] = "Cannot validate - missing data source"
                hyp['validated'] = False
                hyp['evidence_confidence'] = 0.0
                hyp['status'] = "BLOCKED"
                validated.append(hyp)
                continue
            
            try:
                query = hyp.get('validation_query', '')
                if query:
                    df = pd.read_sql_query(query, conn)
                    if not df.empty:
                        # Fixed bug: always take the first value of the first column
                        val = df.iloc[0, 0] 
                        if isinstance(val, (int, float)):
                            if val > 1000:
                                evidence = "Strong support"
                                confidence = 0.85
                            elif val > 500:
                                evidence = "Moderate support"
                                confidence = 0.60
                            else:
                                evidence = "Weak or no support"
                                confidence = 0.30
                        else:
                            evidence = "Inconclusive"
                            confidence = 0.40
                    else:
                        evidence = "No data returned"
                        confidence = 0.0
                else:
                    evidence = "No query provided"
                    confidence = 0.0
            except Exception as e:
                evidence = f"Query error: {str(e)}"
                confidence = 0.0
            
            hyp['validation_result'] = evidence
            hyp['validated'] = True
            hyp['evidence_confidence'] = confidence
            hyp['status'] = "VALIDATED" if confidence > 0.5 else "INCONCLUSIVE"
            validated.append(hyp)
        
        conn.close()
        return validated
    
    def rank_and_abstain(self, hypotheses, anomaly_confidence, min_overall_confidence=0.6):
        ranked = sorted(hypotheses, key=lambda x: x.get('evidence_confidence', 0), reverse=True)
        
        top_evidence_conf = ranked[0].get('evidence_confidence', 0) if ranked else 0
        overall_conf = anomaly_confidence * top_evidence_conf
        
        abstain_reasons = []
        if overall_conf < min_overall_confidence:
            abstain_reasons.append(f"Overall confidence ({overall_conf:.2f}) below threshold")
        
        blocked = [h for h in hypotheses if h.get('status') == 'BLOCKED']
        if blocked:
            abstain_reasons.append(f"Missing critical data: {[h['description'] for h in blocked]}")
        
        if len(ranked) >= 2:
            if ranked[0].get('evidence_confidence', 0) - ranked[1].get('evidence_confidence', 0) < 0.2:
                abstain_reasons.append("Contradictory evidence between top hypotheses")
        
        return {
            "ranked_hypotheses": ranked,
            "overall_confidence": round(overall_conf, 3),
            "top_hypothesis": ranked[0] if ranked else None,
            "abstain": len(abstain_reasons) > 0,
            "abstain_reasons": abstain_reasons,
            "next_steps": "Collect competitor data and extend historical window" if abstain_reasons else None
        }