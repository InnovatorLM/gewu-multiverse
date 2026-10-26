#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
printf '0\n' > /logs/verifier/reward.txt
python3 /tests/grade.py
printf '1\n' > /logs/verifier/reward.txt
