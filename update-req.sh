#!/usr/bin/env bash
source charts/bin/activate
pip freeze > requirements.txt
echo "Requirements updated"
deactivate
