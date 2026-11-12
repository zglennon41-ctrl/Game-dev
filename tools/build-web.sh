#!/usr/bin/env bash
# Export the game for the web and package it for an artifact link:
# the engine gzip-compressed and the game data under web-safe names, with a loader shim.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/web
# People must be imported with a display, or their shape keys are not packed small
# (game/scripts/shapes.gd) and the game data is 140 MB larger than the page can hold.
# A person's .import file is not kept with the repository, and a fresh one names no import
# script: name it, so the keys are packed (game/assets/people/people_import.gd) at the import below.
if grep -q '^import_script/path=""' game/assets/people/*-[fm].glb.import 2>/dev/null; then
	sed -i 's#^import_script/path=""#import_script/path="res://game/assets/people/people_import.gd"#' game/assets/people/*-[fm].glb.import
	again=1
fi
people_mb() { find .godot/imported -name '*-[fm].glb-*.scn' -printf '%s\n' 2>/dev/null | awk '{s+=$1}END{print int(s/1e6)}'; }
if { [ "$(people_mb)" -gt 200 ] || [ -n "${again:-}" ]; } && command -v xvfb-run >/dev/null; then
	for f in game/assets/people/*-[fm].glb; do rm -f ".godot/imported/$(basename "$f")-"*; done
	xvfb-run -a -s "-screen 0 1280x720x24" godot --path . --import >/dev/null 2>&1 || true
fi
[ "$(people_mb)" -le 200 ] || echo "WARNING: people are not packed ($(people_mb) MB); open the project in the Godot editor once, then build again."
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
