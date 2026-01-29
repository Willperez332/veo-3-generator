#!/bin/bash
# Start the VEO 3 Asset Generator

cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Kill any existing Flask processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start Flask
export FLASK_APP=app.py
export FLASK_ENV=production
python -m flask run --host=0.0.0.0 --port=8000
