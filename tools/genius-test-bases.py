"""Write the three small bases the engine's tests run on (game/tests/fixtures/bases/*.json).

They are not part of the game: a test of the tree, the Readings and the hybrids must not
depend on what the real bases say, which the designer changes. Each is a whole tree
(a settled form, three paths, three prongs a path, two finishes a prong) that keeps every
rule of docs/genius-tree.md, with plain names so a failing test reads clearly.

    python3 tools/genius-test-bases.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "game", "tests", "fixtures", "bases")


def base(bid, name, cls, expr, sil, adj, gift, nature, calls, feats, paths, pool, own_body=None):
    """paths: the three paths' leans. pool: leans handed out in turn to the prongs and finishes."""
    low = name.lower()
    state = {"li": 0, "fi": 0}

    def lean():
        i = state["li"]
        a, b = pool[i % len(pool)], pool[(i * 2 + 1) % len(pool)]
        state["li"] += 1
        d = {a[0]: {a[1]: 1.0}}
        if b[0] == a[0]:
            if b[1] != a[1]:
                d[a[0]][b[1]] = 0.5
        else:
            d[b[0]] = {b[1]: 0.5}
        return d

    def feat():
        f = feats[state["fi"] % len(feats)]
        state["fi"] += 1
        return [f]

    def form(fid, label, what, level, leans=None):
        n = {"id": fid, "name": "%s %s" % (name, label) if level > 1 else "Small " + low}
        if level > 1:
            n["of"] = "one who is like %s %s" % (name, label)
        n["text"] = "A test %s of the %s, kept for the engine's tests only." % (what, low)
        n["sign"] = "A stranger would notice the mark of %s on it." % n["name"]
        n["habit"] = "When nothing is happening, %s counts to itself." % n["name"]
        if level > 1:
            n["leans"] = leans if leans else lean()
        n["features"] = feats[:2] if level == 1 else feat()
        return n

    tree = []
    for pi, p in enumerate("abc"):
        prongs = []
        for q in "123":
            fins = [form("%s-%s%s%s" % (bid, p, q, r), "Finish %s%s%s" % (p.upper(), q, r.upper()), "finish", 4) for r in "xy"]
            prong = form("%s-%s%s" % (bid, p, q), "Prong %s%s" % (p.upper(), q), "prong", 3)
            if own_body and own_body[0] == p + q:
                prong["silhouette"] = own_body[1]   # its finishes wear it too
            prong["finishes"] = fins
            prongs.append(prong)
        path = form("%s-%s" % (bid, p), "Path %s" % p.upper(), "path", 2, paths[pi])
        path["prongs"] = prongs
        tree.append(path)
    return {
        "id": bid, "name": name, "class": cls, "expression": expr, "silhouette": sil,
        "soul": "The soul of no one: a %s, kept for the engine's tests only." % low,
        "spark": "A test mote, kept for the engine's tests only.",
        "nature": nature, "calls": calls,
        "hybrid": {"adj": adj, "gift": gift, "text": "It is a test of the %s." % low},
        "settled": form(bid + "-small", "", "settled form", 1), "paths": tree,
    }


BASES = [
    base("tedge", "Test Edge", "weapon", "relic", "relic-knife", "Edged", ["edge"],
         {"range": {"close": 1.0}, "fights": {"parries": 0.8}, "shape": {"cast": 0.5}},
         {"seed": {"i-can-hold": 1.0}, "shape": {"cast": 0.6, "read": 0.3}, "blood": {"long-stride": 0.3}},
         ["edge", "grip", "sheath", "pulse", "brass-plate", "far-eyes"],
         [{"range": {"close": 1.0}, "fights": {"parries": 0.6}}, {"shape": {"cast": 1.0}, "pattern": {"fires": 0.6}}, {"company": {"alone": 1.0}, "quests": {"hunt": 0.6}}],
         [("range", "close"), ("fights", "parries"), ("shape", "cast"), ("pattern", "fires"), ("orders", "hunt"), ("fights", "dodges"), ("quests", "hunt"), ("company", "alone"), ("bonds", "named"), ("shape", "read"), ("pattern", "sworn"), ("ground", "ruin"), ("range", "mid")],
         own_body=("b1", "relic-blade")),
    base("tlamp", "Test Lamp", "item", "engine", "engine-lantern", "Lantern", ["lantern"],
         {"orders": {"hold": 1.0}, "ground": {"night": 0.8}, "shape": {"read": 0.6}},
         {"seed": {"never-alive": 1.0, "remembers": 0.4}, "shape": {"read": 0.6, "make": 0.5}, "blood": {"forgeborn": 0.4}},
         ["lantern", "glow", "cold-core", "iron-hide", "ring", "old-eyes"],
         [{"orders": {"hold": 1.0}, "ground": {"night": 0.6}}, {"shape": {"read": 1.0}, "bonds": {"shade": 0.6}}, {"ground": {"line": 1.0}, "quests": {"linework": 0.6}}],
         [("orders", "hold"), ("ground", "night"), ("shape", "read"), ("ground", "line"), ("orders", "guard"), ("quests", "linework"), ("company", "party"), ("bonds", "shade"), ("shape", "make"), ("fights", "blocks"), ("ground", "quiet"), ("quests", "escort"), ("range", "far")]),
    base("trun", "Test Runner", "animal", "beast", "beast-runner", "Running", ["long-legs"],
         {"orders": {"hunt": 1.0}, "ground": {"wild": 0.7}, "company": {"party": 0.5}},
         {"seed": {"stands-between": 1.0, "watches-from-above": 0.5}, "shape": {"anchor": 0.6, "turn": 0.4}, "blood": {"ridgefolk": 0.5}},
         ["long-legs", "fangs", "ruff", "tail", "broad-chest", "ground-claws"],
         [{"orders": {"hunt": 1.0}, "ground": {"wild": 0.6}}, {"fights": {"blocks": 1.0}, "orders": {"guard": 0.6}}, {"bonds": {"classmate": 1.0}, "company": {"party": 0.6}}],
         [("orders", "hunt"), ("ground", "wild"), ("fights", "blocks"), ("orders", "guard"), ("company", "party"), ("bonds", "classmate"), ("range", "close"), ("quests", "escort"), ("ground", "water"), ("fights", "hurts"), ("shape", "anchor"), ("quests", "salvage"), ("orders", "free")]),
]

os.makedirs(OUT, exist_ok=True)
known = {x["id"] for x in json.load(open(os.path.join(ROOT, "data", "features.json")))}
for b in BASES:
    used = set(b["settled"]["features"]) | set(b["hybrid"]["gift"])
    for p in b["paths"]:
        used |= set(p["features"])
        for q in p["prongs"]:
            used |= set(q["features"])
            for f in q["finishes"]:
                used |= set(f["features"])
    assert not used - known, (b["id"], used - known)
    with open(os.path.join(OUT, b["id"] + ".json"), "w") as f:
        json.dump(b, f, indent=1)
        f.write("\n")
print("wrote %d test bases to %s" % (len(BASES), os.path.relpath(OUT, ROOT)))
