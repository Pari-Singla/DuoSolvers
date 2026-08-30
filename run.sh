#!/bin/bash
echo "🚀 Starting DuoSolver Engine..."

# Generate data if not exists
if [ ! -f "data/kpi.db" ]; then
    echo "📊 Generating sample data..."
    python -c "from src.data_generator import generate_and_load_sqlite; generate_and_load_sqlite()"
fi

# Start FastAPI backend
echo "🔧 Starting FastAPI backend on http://localhost:8000"
uvicorn src.orchestrator:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend on http://localhost:8501"
streamlit run frontend/streamlit_app.py --server.port 8501

trap "kill $BACKEND_PID" EXIT