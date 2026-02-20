#!/bin/bash
cd "/home/jens/Dokumente/Software Projekte/Geothermietool"

# Check if venv exists, if so activate
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export PYTHONPATH=$PYTHONPATH:.
python3 main.py
