#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Activate virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Generate demo preset assets if missing
if [ ! -f "static/presets/room_obstacles.jpg" ]; then
    echo "Generating demo preset media..."
    python generate_presets.py
fi

echo "=========================================================="
echo "  🕶️  SCRIBE — GEMINI SMART GLASSES I/O PROTOTYPE"
echo "=========================================================="
echo "  Zero Modes // Push-to-Talk Multimodal Intelligence"
echo "  - Hold or tap Spacebar / Action button"
echo "  - Say: 'Translate this for me', 'Tell me what's in front of me', etc."
echo "=========================================================="
echo "  Starting server on http://localhost:8000"
echo "  Open http://localhost:8000 in your browser to begin!"
echo "=========================================================="

exec python main.py

