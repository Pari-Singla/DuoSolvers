# src/orchestrator.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import time
from datetime import datetime, timedelta
import pandas as pd

from config import KPI_CONTRACTS, ROLE_LEVELS, ACTION_RULES
from anomaly_detector import AnomalyDetector
from contribution_analysis import ContributionAnalyzer
from llm_orchestrator import LLMOrchestrator
from telemetry import TelemetryLogger

app = FastAPI(title="DuoSolver KPI Intelligence Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = AnomalyDetector()
analyzer = ContributionAnalyzer()
llm = LLMOrchestrator()
telemetry = TelemetryLogger()

EVENTS_STORE = []
FEEDBACK_STORE = []
EVENT_ID_COUNTER = 1

class EventResponse(BaseModel):
    event_id: int
    kpi: str
    dimensions: dict
    date: str
    current_value: float
    expected_value: float
    deviation_percent: float
    confidence: float
    is_sparse: bool = False

class FeedbackRequest(BaseModel):
    event_id: int
    role: str
    feedback_type: str
    comment: Optional[str] = ""

def apply_security(events, role):
    role_config = ROLE_LEVELS.get(role, {})
    if not role_config:
        return events
    filtered = []
    for e in events:
        dims = e.get('dimensions', {})
        if all(dims.get(k) == v for k, v in role_config.items()):
            filtered.append(e)
    return filtered

@app.get("/detect", response_model=List[EventResponse])
async def detect_anomalies(role: str = Query("analyst", enum=["manager", "analyst", "executive"])):
    global EVENT_ID_COUNTER
    start_time = time.time()
    all_events = []
    
    # Scan dimensions for KPI 'revenue'
    kpi_name = "revenue"
    regions = ['North', 'South', 'East']
    products = ['A', 'B', 'C']
    
    for region in regions:
        for product in products:
            filters = {"region": region, "product_line": product}
            events = detector.detect_anomalies(kpi_name, filters, window=14, threshold=2.0)
            
            if events:
                for e in events:
                    e['event_id'] = EVENT_ID_COUNTER
                    e['is_sparse_history'] = (product == 'C')
                    all_events.append(e)
                    EVENTS_STORE.append(e)
                    EVENT_ID_COUNTER += 1
            else:
                # If no anomaly detected but it's Product C, create a synthetic "Sparse History" event for demo
                if product == 'C':
                    # Create a mock event showing abstention due to sparse history
                    mock_event = {
                        "event_id": EVENT_ID_COUNTER,
                        "kpi": kpi_name,
                        "dimensions": {"region": region, "product_line": "C"},
                        "date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                        "current_value": 150.0,
                        "expected_value": 150.0,  # Same because no history
                        "deviation_percent": 0.0,
                        "confidence": 0.1,  # Very low confidence
                        "is_sparse_history": True,
                        "is_mock": True
                    }
                    all_events.append(mock_event)
                    EVENTS_STORE.append(mock_event)
                    EVENT_ID_COUNTER += 1

    filtered = apply_security(all_events, role)
    telemetry.log_request("/detect", (time.time() - start_time) * 1000, 0, 0)
    return filtered

@app.get("/explain/{event_id}")
async def explain_anomaly(event_id: int):
    start_time = time.time()
    event = next((e for e in EVENTS_STORE if e['event_id'] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Sparse history override
    if event.get('is_sparse_history', False):
        return {
            "event_id": event_id,
            "contribution": {},
            "hypotheses": [],
            "top_hypothesis": None,
            "overall_confidence": 0.0,
            "abstain": True,
            "abstain_reasons": ["Sparse history: Product C has less than 14 days of data. Cannot reliably detect anomaly or attribute drivers."],
            "next_steps": "Collect at least 14 days of historical data for Product C, or use a cohort proxy from Product A and B."
        }
    
    dims = event.get('dimensions', {})
    region = dims.get('region')
    current_date = datetime.strptime(event['date'], '%Y-%m-%d')
    baseline_start = (current_date - timedelta(days=30)).strftime('%Y-%m-%d')
    baseline_end = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
    current_start = current_date.strftime('%Y-%m-%d')
    current_end = current_date.strftime('%Y-%m-%d')
    
    contribution = analyzer.analyze_drivers(
        kpi_name=event['kpi'],
        dimension_filters={"region": region},
        current_period_start=current_start,
        current_period_end=current_end,
        baseline_period_start=baseline_start,
        baseline_period_end=baseline_end
    )
    
    hypotheses = llm.generate_hypotheses(event, contribution)
    validated = llm.validate_hypotheses(hypotheses)
    rank_result = llm.rank_and_abstain(validated, anomaly_confidence=event['confidence'])
    
    telemetry.log_request("/explain", (time.time() - start_time) * 1000, 1, 500)
    return {
        "event_id": event_id,
        "contribution": contribution,
        "hypotheses": rank_result['ranked_hypotheses'],
        "top_hypothesis": rank_result['top_hypothesis'],
        "overall_confidence": rank_result['overall_confidence'],
        "abstain": rank_result['abstain'],
        "abstain_reasons": rank_result['abstain_reasons'],
        "next_steps": rank_result.get('next_steps')
    }

@app.get("/insight/{event_id}")
async def get_insight(event_id: int, role: str = Query("manager", enum=["manager", "analyst", "executive"])):
    explanation = await explain_anomaly(event_id)
    event = next((e for e in EVENTS_STORE if e['event_id'] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if explanation['abstain']:
        narrative = f"⚠️ Insufficient confidence. {explanation['next_steps'] or 'Please collect additional data.'}"
        recommended_action = "Gather more data or consult with the data team."
        owner = "Data Team"
        confidence_score = 0.0
    else:
        top = explanation['top_hypothesis']
        if role == "manager":
            narrative = f"🔍 The primary driver is: {top['description']} (Evidence: {top['validation_result']}). Action: {ACTION_RULES[0]['action']}."
            recommended_action = ACTION_RULES[0]['action']
            owner = ACTION_RULES[0]['owner']
        elif role == "analyst":
            narrative = f"Detailed breakdown: {explanation['contribution']['summary']}. Top hypothesis: {top['description']}. Validation SQL: {top.get('validation_query', 'N/A')}."
            recommended_action = "Perform a deeper dive into validation SQL."
            owner = "Data Analyst"
        else:
            narrative = f"Executive summary: {event['kpi']} dropped {event['deviation_percent']:.1f}%. Primary driver is {explanation['contribution']['summary']['primary_driver']}."
            recommended_action = ACTION_RULES[0]['action']
            owner = ACTION_RULES[0]['owner']
        confidence_score = explanation['overall_confidence']
    
    return {
        "event_id": event_id,
        "role": role,
        "narrative": narrative,
        "recommended_action": recommended_action,
        "owner": owner,
        "evidence_trace": [
            f"Data Source: {KPI_CONTRACTS[event['kpi']]['source_table']}",
            f"Refresh: {KPI_CONTRACTS[event['kpi']]['refresh']}",
            "Method: Deterministic Decomposition + LLM Validation"
        ],
        "confidence_score": confidence_score
    }

@app.post("/feedback")
async def submit_feedback(fb: FeedbackRequest):
    FEEDBACK_STORE.append(fb.dict())
    return {"status": "Feedback recorded", "total_feedback": len(FEEDBACK_STORE)}

@app.get("/telemetry")
async def get_telemetry():
    return telemetry.get_summary()