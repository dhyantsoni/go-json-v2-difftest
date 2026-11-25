#!/usr/bin/env bash
# Recall check: v0 single-field round on go1.27.0 with seeds 1-10, then count
# which of the 5 known issues (#81061 #81062 #81373 #82685 #82872) each seed detects.
# Control: GOTOOLCHAIN=go1.27.4 ./recall/run_seeds.sh should show 0 matches for #81061 and #81062.
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT=${OUT:-out/seeds}
export GOTOOLCHAIN=${GOTOOLCHAIN:-go1.27.0}
for s in 1 2 3 4 5 6 7 8 9 10; do SINGLE=1 "$HERE/run.sh" v0 "$s" 0 8 "$OUT/s$s"; done
python3 "$HERE/recall/detect_known.py" "$OUT"
