#!/usr/bin/env bash
# The whole genius tree as a page, with a picture of every form taken from the game.
#   bash tools/genius-tree-page.sh            every base (about twenty minutes without a graphics card)
#   bash tools/genius-tree-page.sh wolf fox   only these bases' pictures again
# The page is build/genius-tree/genius-tree.html, its pictures in build/genius-tree/img.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=build/genius-tree
SHOTS=$OUT/shots
mkdir -p "$SHOTS"
RUN=()
if [ -z "${DISPLAY:-}" ]; then RUN=(xvfb-run -a -s "-screen 0 3200x1800x24"); fi
BASES=("$@")
if [ ${#BASES[@]} -eq 0 ]; then
  for f in data/genius-bases/*.json; do BASES+=("$(basename "$f" .json)"); done
  # the hybrids written by hand, as examples
  while read -r pair; do BASES+=("$pair"); done < <(python3 -c "import json; print('\n'.join(json.load(open('data/genius-hybrids.json'))['pairs']))")
fi
for b in "${BASES[@]}"; do
  mkdir -p "$SHOTS/sheet-$b"
  "${RUN[@]}" godot --path . --resolution 3200x1800 -- --sheet="$b" --shots="$SHOTS/sheet-$b" > "$SHOTS/sheet-$b.log" 2>&1
  case "$b" in *+*) ;; *)
    mkdir -p "$SHOTS/life-$b"
    "${RUN[@]}" godot --path . --resolution 1600x900 -- --lineage="$b" --shots="$SHOTS/life-$b" > "$SHOTS/life-$b.log" 2>&1 ;;
  esac
  echo "$b"
done
# the Baby, everyone's before the rite
mkdir -p "$SHOTS/sheet-baby"
"${RUN[@]}" godot --path . --resolution 3200x1800 -- --sheet=baby --shots="$SHOTS/sheet-baby" > "$SHOTS/sheet-baby.log" 2>&1
python3 tools/genius-tree-page.py --out "$OUT" --shots "$SHOTS"
