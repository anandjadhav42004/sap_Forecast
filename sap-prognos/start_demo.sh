#!/bin/bash
# ==============================================================================
# SAP Prognos — One-Click Demo & Presentation Launcher
# ==============================================================================
# This script starts the FastAPI backend, UI5 frontend, and opens Chrome.
# Press Ctrl+C at any time to cleanly stop all servers.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/forecast-api"
FRONTEND_DIR="$SCRIPT_DIR/frontend-ui5/webapp"

echo "========================================================"
echo "   🚀 Starting SAP Prognos Enterprise AI Platform"
echo "========================================================"

# Step 1: Clean any existing processes on ports 8000 and 8080
echo "🧹 [1/4] Checking and freeing ports 8000 & 8080..."
lsof -ti :8000 -ti :8080 | xargs kill -9 2>/dev/null || true
sleep 1

# Step 2: Determine Python environment
echo "🐍 [2/4] Initializing Python environment..."
PYTHON_BIN="python3"
if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"
elif [ -f "/opt/anaconda3/bin/python3" ]; then
    PYTHON_BIN="/opt/anaconda3/bin/python3"
fi

# Step 3: Start Backend API
echo "⚙️  [3/4] Starting FastAPI backend on http://localhost:8000..."
cd "$BACKEND_DIR"
$PYTHON_BIN -m uvicorn main:app --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

# Step 4: Start Frontend UI5 Server
echo "🌐 [4/4] Starting UI5 web server on http://localhost:8080..."
cd "$FRONTEND_DIR"
python3 -m http.server 8080 &
FRONTEND_PID=$!

# Cleanup trap on Ctrl+C or kill
cleanup() {
    echo ""
    echo "🛑 Shutting down SAP Prognos servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    lsof -ti :8000 -ti :8080 | xargs kill -9 2>/dev/null || true
    echo "✅ Shutdown complete. Goodbye!"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Wait briefly for startup
sleep 2

echo ""
echo "========================================================"
echo "   ✅ SAP Prognos is RUNNING!"
echo "   - Web Dashboard:  http://localhost:8080/webapp/index.html"
echo "   - API Swagger Docs: http://localhost:8000/docs"
echo "   - Demo Roles: admin/admin or user/user"
echo "========================================================"
echo "Opening browser in 2 seconds (Press Ctrl+C to stop)..."

# Open in default browser or Chrome
if command -v open >/dev/null 2>&1; then
    open "http://localhost:8080/webapp/index.html"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:8080/webapp/index.html"
fi

# Keep script running
wait
