#!/usr/bin/env bash
# Export the game for the web and package it for an artifact link:
# the engine gzip-compressed and the game data under web-safe names, with a loader shim.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/web
godot --headless --path . --export-release "Web" build/web/index.html
cd build/web
gzip -9 -c index.wasm > engine.gz.wasm
# The game data in parts under 14 MB (the artifact's limit for one binary file); the shim joins them.
rm -f game.pck.wasm game.pck.*.wasm
split -b 14000000 -d -a 2 index.pck game.pck.
for f in game.pck.??; do mv "$f" "$f.wasm"; done
PARTS=$(ls game.pck.??.wasm | wc -l)
PCK_PARTS=$PARTS python3 ../../tools/web_shim.py
echo "Built build/web/page.html (artifact) and build/web/local.html (local test)."
