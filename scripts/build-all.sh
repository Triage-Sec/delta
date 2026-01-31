#!/bin/bash
# Build all npm packages
#
# Usage: ./scripts/build-all.sh [--release|--debug]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_MODE="${1:-release}"

echo "========================================"
echo "Building all Delta LTSC npm packages"
echo "========================================"

# Build WASM core
echo ""
"$SCRIPT_DIR/build-wasm.sh" "$BUILD_MODE"

# Build SDK
echo ""
"$SCRIPT_DIR/build-sdk.sh"

# Build ML package
echo ""
"$SCRIPT_DIR/build-ml.sh"

echo ""
echo "========================================"
echo "All packages built successfully!"
echo "========================================"
echo ""
echo "Packages:"
echo "  - @delta-ltsc/sdk  (packages/sdk/dist/)"
echo "  - @delta-ltsc/ml   (packages/ml/dist/)"
echo ""
echo "To publish:"
echo "  cd packages/sdk && npm publish --access public"
echo "  cd packages/ml && npm publish --access public"
