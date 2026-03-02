#!/bin/bash

# MoneyTrack Backend - Run All Tests
# Usage: ./run_tests.sh [-v] [-k keyword] [other pytest args]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  MoneyTrack Backend - Test Runner"
echo "========================================"
echo ""

# Run pytest on app directory
python -m pytest app/ "$@"

echo ""
echo "========================================"
echo "  Tests completed!"
echo "========================================"
