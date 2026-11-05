#!/usr/bin/env bash
# Export the game for the web and package it for an artifact link:
# the engine gzip-compressed and the game data under web-safe names, with a loader shim.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/web
godot --headless --path . --export-release "Web" build/web/index.html
cd build/web
gzip -9 -c index.wasm > engine.gz.wasm
cp index.pck game.pck.wasm
python3 ../../tools/web_shim.py
echo "Built build/web/page.html (artifact) and build/web/local.html (local test)."
