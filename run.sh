#!/usr/bin/env bash
# Differential run: default Go build vs GOEXPERIMENT=nojsonv2 build of the same harness.
# Usage: ./run.sh {v0|v1|embed|mutation} SEED NTYPES NCASES OUTDIR
#   v0, v1, embed: NTYPES generated types, NCASES inputs per type (SINGLE=1 enumerates kinds x tags).
#   mutation: byte-level baseline over 8 fixed types; NTYPES is ignored, NCASES is the number of inputs.
# Set GOTOOLCHAIN (default go1.27.4) to pick the Go version.
set -euo pipefail
GEN=$1 SEED=$2 NT=$3 NC=$4 OUT=$5
HERE=$(cd "$(dirname "$0")" && pwd)
export GOTOOLCHAIN=${GOTOOLCHAIN:-go1.27.4}
mkdir -p "$OUT"
case $GEN in
  v0)       python3 "$HERE/gen/gen.py" "$SEED" "$NT" "$NC" "$OUT"; cp "$HERE/harness/main_v0.go" "$OUT/main.go" ;;
  v1)       python3 "$HERE/gen/gen1.py" "$SEED" "$NT" "$NC" "$OUT"; cp "$HERE/harness/main_v1.go" "$OUT/main.go" ;;
  embed)    python3 "$HERE/gen/gen_embed.py" "$SEED" "$NT" "$NC" "$OUT"; cp "$HERE/harness/main_embed.go" "$OUT/main.go" ;;
  mutation) python3 "$HERE/baselines/mutation/mut.py" "$SEED" "$NC" > "$OUT/cases.tsv"
            cp "$HERE/baselines/mutation/types.go" "$OUT/types.go"; cp "$HERE/harness/main_v0.go" "$OUT/main.go" ;;
  *) echo "unknown generator: $GEN" >&2; exit 2 ;;
esac
printf 'module fz\n\ngo 1.27\n' > "$OUT/go.mod"
cd "$OUT"
go build -o v2bin .
GOEXPERIMENT=nojsonv2 go build -o v1bin .
./v1bin < cases.tsv > v1.out
./v2bin < cases.tsv > v2.out
total=$(wc -l < cases.tsv)
diffs=$(paste v1.out v2.out | awk -F'\t' '$2 != $4' | wc -l)
echo "$GOTOOLCHAIN $GEN seed=$SEED cases=$total differences=$diffs"
