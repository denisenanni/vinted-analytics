#!/bin/bash

# Start Vinted Analytics - API + Web

cleanup() {
    echo "\nShutting down..."
    kill $API_PID $WEB_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting Vinted Analytics..."
echo ""

# Start API
echo "[API] Starting on http://localhost:8000"
cd api && source venv/bin/activate && uvicorn src.main:app --reload &
API_PID=$!
cd ..

sleep 2

# Start Web
echo "[WEB] Starting on http://localhost:5173"
cd web && yarn dev &
WEB_PID=$!
cd ..

echo ""
echo "Both servers running. Press Ctrl+C to stop."
echo ""

wait
