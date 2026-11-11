"""How well a line reads, measured from the game's own pictures (docs/genius-lines.md, "The second pass").

A line is thirty-one forms. This looks at a plain sheet of them and says three things:

  alike   pairs of forms whose outlines are nearly the same shape (a stranger could not tell them apart
          as black shapes), and forms that are nearly their parent's shape
  dark    forms too dark to read on the game's dark grounds
  colour  whether the three Paths can be told apart by colour alone: each form's colour is put to the
          nearest Path's, and the score is the share that land on their own

    godot --path . --resolution 1600x900 -- --sheet=wolf --plain --shots=DIR/sheet-wolf
    python3 tools/genius-line-check.py DIR                 # every sheet-<base> folder in DIR
    python3 tools/genius-line-check.py DIR wolf fox        # these
    python3 tools/genius-line-check.py DIR --json out.json # and keep the numbers, to compare later
    python3 tools/genius-line-check.py DIR --against before.json

A sheet folder holds 01-sheet.png, mask.png (the forms as white shapes) and sheet.json (--plain writes them).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIKE = 0.80        # two outlines that overlap this much, laid one on the other, are one shape
PARENT = 0.86       # and a form this near its parent has not changed
DARK = 0.165        # a form whose lit surface is this dim on average is lost on a dark ground
DIM = 0.6           # or one of which this much is nearly black
SIZE = 56


def order(base):
    """[(form id, name, level, path index or -1, parent id)] in the sheet's order."""
    out = [(base["settled"]["id"], base["settled"]["name"], 1, -1, "")]
    for pi, p in enumerate(base["paths"]):
        out.append((p["id"], p["name"], 2, pi, base["settled"]["id"]))
        for q in p["prongs"]:
            out.append((q["id"], q["name"], 3, pi, p["id"]))
            for f in q["finishes"]:
                out.append((f["id"], f["name"], 4, pi, q["id"]))
    return out


def lab(rgb):
    """sRGB 0..1 (n, 3) -> CIE Lab."""
    c = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    return np.stack([116.0 * f[:, 1] - 16.0, 500.0 * (f[:, 0] - f[:, 1]), 200.0 * (f[:, 1] - f[:, 2])], axis=1)


def measure(folder):
    with open(os.path.join(folder, "sheet.json")) as f:
        sheet = json.load(f)
    shot = np.asarray(Image.open(os.path.join(folder, "01-sheet.png")).convert("RGB"), dtype=np.float32) / 255.0
    mask = np.asarray(Image.open(os.path.join(folder, "mask.png")).convert("L"), dtype=np.float32) / 255.0 > 0.3
    cols, rows = int(sheet["cols"]), int(sheet["rows"])
    H, W = mask.shape
    ch, cw = H / rows, W / cols
    forms = {}
    for i, fid in enumerate(sheet["forms"]):
        y0, y1 = int(round((i // cols) * ch)), int(round((i // cols + 1) * ch))
        x0, x1 = int(round((i % cols) * cw)), int(round((i % cols + 1) * cw))
        m = mask[y0:y1, x0:x1]
        if m.sum() < 30:
            forms[fid] = {"area": 0.0}
            continue
        ys, xs = np.where(m)
        box = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        # its outline, brought to one size whatever its shape: tall things stay tall
        side = max(box.shape)
        sq = np.zeros((side, side), dtype=bool)
        oy, ox = (side - box.shape[0]), (side - box.shape[1]) // 2
        sq[oy:oy + box.shape[0], ox:ox + box.shape[1]] = box
        sil = np.asarray(Image.fromarray((sq * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BILINEAR)) > 96
        px = shot[y0:y1, x0:x1][m]
        lum = px @ np.array([0.2126, 0.7152, 0.0722])
        mx, mn = px.max(axis=1), px.min(axis=1)
        sat = np.where(mx > 0.02, (mx - mn) / np.maximum(mx, 1e-4), 0.0)
        coloured = (sat > 0.28) & (mx > 0.16)
        L = lab(px)
        forms[fid] = {
            "area": float(m.mean()), "sil": sil, "lum": float(lum.mean()), "dim": float((lum < 0.06).mean()),
            "colour": float(coloured.mean()),
            # what colour it is, where it has any: the mean of its coloured surface in a*b*; and of all of it
            "ab": [float(v) for v in (L[coloured][:, 1:].mean(axis=0) if coloured.sum() > 20 else np.zeros(2))],
            "lab": [float(v) for v in L.mean(axis=0)],
        }
    return sheet, forms


def iou(a, b):
    return float((a & b).sum()) / max(1.0, float((a | b).sum()))


def report(base_id, folder, verbose=True):
    with open(os.path.join(ROOT, "data", "genius-bases", base_id + ".json")) as f:
        base = json.load(f)
    rows = order(base)
    sheet, forms = measure(folder)
    name = {r[0]: r[1] for r in rows}
    have = [r for r in rows if r[0] in forms and forms[r[0]].get("area", 0) > 0]
    missing = [r[0] for r in rows if r not in have]
    alike = []
    for i, x in enumerate(have):
        for y in have[i + 1:]:
            v = iou(forms[x[0]]["sil"], forms[y[0]]["sil"])
            if v >= ALIKE:
                alike.append((v, x[0], y[0]))
    alike.sort(reverse=True)
    stale = []
    for r in have:
        if r[4] in forms and forms[r[4]].get("area", 0) > 0:
            v = iou(forms[r[0]]["sil"], forms[r[4]]["sil"])
            if v >= PARENT:
                stale.append((v, r[0], r[4]))
    dark = sorted((forms[r[0]]["lum"], r[0]) for r in have if forms[r[0]]["lum"] < DARK or forms[r[0]]["dim"] > DIM)
    # the three Paths by colour: each form of a Path put to the nearest Path's mean colour
    by = {0: [], 1: [], 2: []}
    for r in have:
        if r[3] >= 0:
            by[r[3]].append(r[0])
    vec = lambda fid: np.array(forms[fid]["lab"][1:] if forms[fid]["colour"] < 0.04 else forms[fid]["ab"]) * (1.0 if forms[fid]["colour"] >= 0.04 else 0.4)
    full = lambda fid: np.concatenate([[forms[fid]["lab"][0] * 0.35], vec(fid)])
    right, total, wrong = 0, 0, []
    for pi in by:
        for fid in by[pi]:
            best, bd = -1, 1e9
            for pj in by:
                others = [full(o) for o in by[pj] if o != fid]
                if not others:
                    continue
                d = float(np.linalg.norm(full(fid) - np.mean(others, axis=0)))
                if d < bd:
                    best, bd = pj, d
            total += 1
            if best == pi:
                right += 1
            else:
                wrong.append((fid, base["paths"][pi]["name"], base["paths"][best]["name"]))
    cents = [np.mean([full(o) for o in by[pi]], axis=0) for pi in by if by[pi]]
    apart = min(float(np.linalg.norm(cents[i] - cents[j])) for i in range(len(cents)) for j in range(i + 1, len(cents))) if len(cents) > 1 else 0.0
    out = {
        "forms": len(have), "missing": missing,
        "alike": len(alike), "stale": len(stale), "dark": len(dark),
        "colour": round(right / max(1, total), 3), "apart": round(apart, 1),
        "coloured": round(float(np.mean([forms[r[0]]["colour"] for r in have])), 3),
        "fill": round(float(np.mean([forms[r[0]]["area"] for r in have])), 3),
        "worst": [(round(v, 2), x, y) for v, x, y in alike[:10]],
        "darkest": [(round(v, 3), x) for v, x in dark[:10]],
        "unchanged": [(round(v, 2), x, y) for v, x, y in sorted(stale, reverse=True)[:10]],
        "miscoloured": wrong[:12],
    }
    if verbose:
        print("%-11s %2d forms   alike %2d   unchanged from parent %2d   dark %2d   Paths told by colour %3d%% (apart %4.1f)   coloured %2d%%"
              % (base["name"], out["forms"], out["alike"], out["stale"], out["dark"], round(out["colour"] * 100), out["apart"], round(out["coloured"] * 100)))
    return out


def main():
    args = sys.argv[1:]
    keep, against, detail = None, None, False
    if "--json" in args:
        i = args.index("--json"); keep = args[i + 1]; del args[i:i + 2]
    if "--against" in args:
        i = args.index("--against"); against = json.load(open(args[i + 1])); del args[i:i + 2]
    if "--detail" in args:
        detail = True; args.remove("--detail")
    root = args[0]
    bases = args[1:] or sorted(d[6:] for d in os.listdir(root) if d.startswith("sheet-") and "+" not in d and d != "sheet-baby"
                               and os.path.exists(os.path.join(root, d, "mask.png")))
    out = {}
    for b in bases:
        out[b] = report(b, os.path.join(root, "sheet-" + b))
        if detail:
            r = out[b]
            for v, x, y in r["worst"]:
                print("      alike %.2f  %s  /  %s" % (v, x, y))
            for v, x, y in r["unchanged"]:
                print("      unchanged %.2f  %s  from  %s" % (v, x, y))
            for v, x in r["darkest"]:
                print("      dark %.3f  %s" % (v, x))
            for fid, own, took in r["miscoloured"]:
                print("      by colour %s reads as %s, not %s" % (fid, took, own))
    tot = lambda k: sum(out[b][k] for b in out)
    print("%d lines, %d forms: alike %d, unchanged %d, dark %d, Paths told by colour %d%% on average"
          % (len(out), tot("forms"), tot("alike"), tot("stale"), tot("dark"), round(100 * sum(out[b]["colour"] for b in out) / max(1, len(out)))))
    if against:
        for b in out:
            if b in against:
                o, n = against[b], out[b]
                print("  %-11s alike %2d -> %2d   unchanged %2d -> %2d   dark %2d -> %2d   colour %3d%% -> %3d%%"
                      % (b, o["alike"], n["alike"], o["stale"], n["stale"], o["dark"], n["dark"], round(o["colour"] * 100), round(n["colour"] * 100)))
    if keep:
        with open(keep, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
