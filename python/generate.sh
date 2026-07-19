#!/usr/bin/env bash
# -----------------------------------------------------------------------------
#  generate.sh — Generate SDK model classes from yds-v1.yaml
#
#  Usage:
#    ./generate.sh [input_yaml] [output_py]
#
#  Defaults:
#    input   = spec/yds/yds-v1.yaml
#    output  = sdk/python/src/y5n/sdk/models.py
# -----------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

INPUT="${1:-$PROJECT_ROOT/spec/yds/yds-v1.yaml}"
OUTPUT="${2:-$PROJECT_ROOT/sdk/python/src/y5n/sdk/models.py}"

# Resolve relative to project root
if [[ "$INPUT" != /* ]]; then
    INPUT="$PROJECT_ROOT/$INPUT"
fi
if [[ "$OUTPUT" != /* ]]; then
    OUTPUT="$PROJECT_ROOT/$OUTPUT"
fi

echo "Generating from: $INPUT"
echo "Writing to:      $OUTPUT"

PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}" \
    python3 -m sdk.gen \
    --input "$INPUT" \
    --output "$OUTPUT"

echo "Done."
