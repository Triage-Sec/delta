#!/bin/bash
# Build ML package
#
# Usage: ./scripts/build-ml.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ML_DIR="$ROOT_DIR/packages/ml"
SDK_DIR="$ROOT_DIR/packages/sdk"

echo "Building Small LTSC ML package..."
echo "ML dir: $ML_DIR"

cd "$ML_DIR"

# Link to local SDK for development
if [ ! -d "node_modules/@small-ltsc/sdk" ] && [ -d "$SDK_DIR/dist" ]; then
    echo "Linking local SDK..."
    mkdir -p node_modules/@small-ltsc
    rm -rf node_modules/@small-ltsc/sdk
    ln -sf "$SDK_DIR" node_modules/@small-ltsc/sdk
fi

# Install dev dependencies only (skip peer deps)
if [ ! -d "node_modules/typescript" ]; then
    echo "Installing dev dependencies..."
    npm install --ignore-scripts --no-save typescript vitest 2>/dev/null || true
fi

# Build ESM
echo ""
echo "Building ESM..."
npx tsc -p tsconfig.esm.json

# Build type declarations
echo ""
echo "Building type declarations..."
npx tsc -p tsconfig.types.json

echo ""
echo "ML package build complete!"
echo "Output: $ML_DIR/dist/"
