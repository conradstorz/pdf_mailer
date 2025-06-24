#!/bin/bash
mkdir -p /logs

# Discover path
echo "🧪 Available PATH: $PATH"
echo "🔍 Looking for uvicorn:"
which uvicorn || echo "uvicorn not found in current PATH"

# Execute using full path fallback
exec uvicorn app.main:app --host 0.0.0.0 --port 7632 --app-dir src
