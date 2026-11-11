#!/usr/bin/env bash
# The soak test: many different characters play the whole game without a window
# (game/tests/soak.gd says what it checks).   npm run soak [-- --count=6 | --only=17 | --debug]
# Fails on a character that does not get through, and on any script error in the log.
set -u
here="$(dirname "$0")"
LOG="${SOAK_LOG:-$(mktemp -t wildline-soak.XXXXXX.log)}"
godot --headless --fixed-fps 30 --path "$here/.." res://game/tests/soak.tscn -- "$@" > "$LOG" 2>&1
code=$?
grep -a '^SOAK' "$LOG"
# (the windowless renderer has no meshes: "Parameter "m" is null" is its, not the game's)
errors=$(grep -a 'SCRIPT ERROR\|^ERROR' "$LOG" | grep -a -v -c 'Parameter "m" is null\|leaked at exit\|still in use at exit')
if [ "$errors" -gt 0 ]; then
  echo "SOAK: $errors errors in the log:"
  grep -a -A2 'SCRIPT ERROR\|^ERROR' "$LOG" | grep -a -v 'Parameter "m" is null\|mesh_get_surface_count\|leaked at exit\|still in use at exit\|^--' | head -60
  code=1
fi
grep -a -q '^SOAK: ' "$LOG" || { echo "SOAK: the run ended before its last line (a crash?). The log's end:"; tail -15 "$LOG"; code=1; }
echo "log: $LOG"
exit $code
