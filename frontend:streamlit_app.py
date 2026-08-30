# frontend/streamlit_app.py
import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="DuoSolver", layout="wide")
st.title("🧠 DuoSolver: KPI Intelligence-to-Action Engine")

role = st.sidebar.selectbox("Select your role", ["manager", "analyst", "executive"])
st.sidebar.info(f"Current role: {role.upper()}")

if "events" not in st.session_state:
    st.session_state.events = []
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "explanation" not in st.session_state:
    st.session_state.explanation = None
if "insight" not in st.session_state:
    st.session_state.insight = None

st.header("1️⃣ Detect KPI Anomalies")
if st.button("🔍 Run Anomaly Detection", type="primary"):
    with st.spinner("Scanning KPIs..."):
        resp = requests.get(f"{API_URL}/detect", params={"role": role})
        if resp.status_code == 200:
            st.session_state.events = resp.json()
            st.success(f"✅ Found {len(st.session_state.events)} events")
        else:
            st.error(f"Error: {resp.text}")

if st.session_state.events:
    df = pd.DataFrame(st.session_state.events)
    # Clean columns for display
    df['dimensions_str'] = df['dimensions'].apply(str)
    st.dataframe(df[['event_id', 'kpi', 'dimensions_str', 'date', 'deviation_percent', 'confidence', 'is_sparse_history']])
    
    event_id = st.selectbox("Select an event", df['event_id'].tolist())
    st.session_state.selected_event = next((e for e in st.session_state.events if e['event_id'] == event_id), None)

if st.session_state.selected_event:
    st.header("2️⃣ Explain the Anomaly")
    if st.button("🧪 Run Explanation Pipeline"):
        with st.spinner("Running analysis..."):
            resp = requests.get(f"{API_URL}/explain/{st.session_state.selected_event['event_id']}")
            if resp.status_code == 200:
                st.session_state.explanation = resp.json()
                st.success("✅ Done")
            else:
                st.error(f"Error: {resp.text}")
    
    if st.session_state.explanation:
        exp = st.session_state.explanation
        
        if exp.get('abstain', False):
            st.warning("⚠️ **System Abstained**")
            for reason in exp.get('abstain_reasons', []):
                st.write(f"- {reason}")
            st.info(f"📌 Next Steps: {exp.get('next_steps', 'N/A')}")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Contribution")
                c = exp['contribution']
                st.metric("Total Change", f"${c['total_change']:.2f}", f"{c['percent_change']:.1f}%")
                st.metric("Volume", f"${c['volume_effect']:.2f}")
                st.metric("Price", f"${c['price_effect']:.2f}")
                st.metric("Mix", f"${c['mix_effect']:.2f}")
            with col2:
                st.subheader("🤖 Hypotheses")
                for h in exp.get('hypotheses', [])[:2]:
                    st.write(f"**{h['description']}**")
                    st.write(f"Evidence: {h.get('validation_result', 'N/A')} (Conf: {h.get('evidence_confidence', 0):.2f})")
            
            st.metric("Overall Confidence", f"{exp['overall_confidence']:.2f}")
        
        st.header("3️⃣ Get Persona Insight")
        if st.button("💡 Generate Insight"):
            resp = requests.get(f"{API_URL}/insight/{st.session_state.selected_event['event_id']}", params={"role": role})
            if resp.status_code == 200:
                st.session_state.insight = resp.json()
                st.success("✅ Insight generated")
        
        if st.session_state.insight:
            ins = st.session_state.insight
            st.subheader("📝 Narrative")
            st.info(ins['narrative'])
            st.subheader("🎯 Action")
            st.success(f"**{ins['recommended_action']}** (Owner: {ins['owner']})")
            st.write(f"Confidence: {ins['confidence_score']:.2f}")
            
            with st.expander("🔗 Evidence Trace"):
                for t in ins['evidence_trace']:
                    st.write(f"- {t}")
            
            # Feedback
            fb = st.radio("Was this useful?", ["Yes", "No"])
            if st.button("Submit Feedback"):
                requests.post(f"{API_URL}/feedback", json={
                    "event_id": st.session_state.selected_event['event_id'],
                    "role": role,
                    "feedback_type": "useful" if fb == "Yes" else "not_useful"
                })
                st.success("Thank you!")

# Telemetry
st.sidebar.header("📊 Telemetry")
if st.sidebar.button("Refresh Telemetry"):
    resp = requests.get(f"{API_URL}/telemetry")
    if resp.status_code == 200:
        t = resp.json()
        st.sidebar.metric("Requests", t['total_requests'])
        st.sidebar.metric("Avg Latency", f"{t['avg_latency_ms']} ms")
        st.sidebar.metric("LLM Calls", t['total_llm_calls'])
        st.sidebar.metric("Est. Cost", f"${t['estimated_cost_usd']}")