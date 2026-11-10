#!/usr/bin/env python3
"""Cut forms out of a sheet the game made, large and named, to look at them closely.

  godot --path . --resolution 3200x1800 -- --sheet=wolf --shots=DIR
  python3 tools/genius-sheet.py DIR out.png                      # every form, eight to a row
  python3 tools/genius-sheet.py DIR out.png wolf-pup,wolf-caller  # these, four to a row
  python3 tools/genius-sheet.py DIR out.png --line 1              # the line down path 1: starter, path, its prongs and finishes
"""
import json
import sys

from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
sheet = json.load(open(d + '/sheet.json'))
im = Image.open(d + '/01-sheet.png')
forms = sheet['forms']
W, H = im.size[0] // sheet['cols'], im.size[1] // sheet['rows']
want, cols, scale = forms, 8, 0.5
if len(sys.argv) > 4 and sys.argv[3] == '--line':
    # the sheet stands a tree in the order it is walked: the starter, then each path with everything under it
    p = int(sys.argv[4]) - 1
    want = [forms[0]] + forms[1 + 10 * p: 11 + 10 * p]
    cols, scale = 4, 1.0
elif len(sys.argv) > 3:
    want, cols, scale = sys.argv[3].split(','), 4, 1.0
rows = (len(want) + cols - 1) // cols
cw, ch = int(W * scale), int(H * scale)
canvas = Image.new('RGB', (cols * cw, rows * ch))
draw = ImageDraw.Draw(canvas)
for n, fid in enumerate(want):
    i = forms.index(fid)
    cell = im.crop(((i % sheet['cols']) * W, (i // sheet['cols']) * H, (i % sheet['cols'] + 1) * W, (i // sheet['cols'] + 1) * H))
    if scale != 1.0:
        cell = cell.resize((cw, ch), Image.LANCZOS)
    canvas.paste(cell, ((n % cols) * cw, (n // cols) * ch))
    draw.text(((n % cols) * cw + 8, (n // cols) * ch + 6), fid, fill=(255, 220, 140))
canvas.save(out)
print(out, canvas.size)
