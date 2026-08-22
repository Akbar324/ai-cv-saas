#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/lambda/worker"
ZIP_FILE="$ROOT_DIR/build/lambda/worker.zip"

echo "Cleaning Lambda build directory..."
rm -rf "$BUILD_DIR" "$ZIP_FILE"
mkdir -p "$BUILD_DIR"

echo "Installing Linux Python 3.12 dependencies..."

python -m pip install \
  --requirement "$ROOT_DIR/requirements-worker.txt" \
  --target "$BUILD_DIR" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --abi cp312 \
  --only-binary=:all: \
  --upgrade

echo "Copying backend application..."
cp -R "$ROOT_DIR/backend" "$BUILD_DIR/backend"

echo "Removing development artifacts..."

find "$BUILD_DIR" \
  -type d \
  \( -name "__pycache__" \
     -o -name ".pytest_cache" \
     -o -name "tests" \) \
  -prune \
  -exec rm -rf {} +

echo "Creating deployment ZIP..."

BUILD_DIR="$BUILD_DIR" ZIP_FILE="$ZIP_FILE" python - <<'PY'
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

build_dir = Path(os.environ["BUILD_DIR"])
zip_file = Path(os.environ["ZIP_FILE"])

with ZipFile(zip_file, "w", ZIP_DEFLATED) as archive:
    for path in sorted(build_dir.rglob("*")):
        if path.is_file():
            archive.write(
                path,
                path.relative_to(build_dir),
            )

print(f"Created: {zip_file}")
print(f"Size: {zip_file.stat().st_size / 1024 / 1024:.2f} MB")
PY

echo "Lambda worker package ready."
