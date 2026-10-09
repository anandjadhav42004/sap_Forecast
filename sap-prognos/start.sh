#!/bin/bash
# SAP Prognos - Single Command Launcher

echo "🚀 Starting SAP Prognos Enterprise Platform..."
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Free up ports if already running
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# 1. Start FastAPI Backend
echo "⚡ Starting FastAPI Backend on port 8000..."
(cd "$BASE_DIR/forecast-api" && uvicorn main:app --port 8000 --reload) &
BACKEND_PID=$!

# 2. Start SAP UI5 Frontend
echo "🌐 Starting UI5 Frontend on port 8080..."
(cd "$BASE_DIR/frontend-ui5" && npx http-server . -p 8080 -c-1) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

sleep 2
echo ""
echo "============================================================"
echo "✅ SAP Prognos is RUNNING!"
echo "👉 Dashboard URL: http://localhost:8080/webapp/index.html"
echo "👉 Backend Docs:  http://localhost:8000/docs"
echo "============================================================"
echo "Press Ctrl+C to stop both servers."

wait
