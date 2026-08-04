#!/bin/bash

# In das Projektverzeichnis wechseln
cd /home/Gunni/HomeMusic || exit 1

# Virtuelle Python-Umgebung aktivieren
source venv/bin/activate

echo ""
echo "======================================"
echo "      HomeMusic 0.2.0 startet..."
echo "======================================"
echo ""

# FastAPI starten
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
