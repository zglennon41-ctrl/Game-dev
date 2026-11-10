"""Check the base forms of the genius tree (data/genius-bases/*.json) against docs/genius-tree.md:
the shape of each tree (a settled form, three paths, three prongs a path, two finishes a prong),
ids and names, the vocabulary of leans, features, bodies.

    python3 tools/genius-base-check.py            # every base
    python3 tools/genius-base-check.py wolf hawk  # some
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = os.path.join(ROOT, "data", "genius-bases")
CLASSES = {"animal", "monster", "creature", "item", "weapon", "armor"}
EXPRESSIONS = {"beast", "kith", "engine", "relic", "daemon", "aspect"}
LEANS = {
    "range": {"close", "mid", "far"},
    "orders": {"guard", "hunt", "hold", "free"},
    "shape": {"anchor", "turn", "cast", "read", "bind", "make"},
    "fights": {"parries", "blocks", "hurts", "dodges"},
    "company": {"alone", "party"},
    "ground": {"line", "wild", "water", "ruin", "night", "quiet"},
    "pattern": {"fires", "sworn"},
    "bonds": {"classmate", "shade", "named"},
    "quests": {"linework", "salvage", "hunt", "escort", "writ", "deep-run"},
}
CALLS = {"seed", "shape", "blood"}


def check(path, known_features, seeds, bloods, bodies, all_ids, all_names):
    problems = []
    b = json.load(open(path))
    bid = b.get("id", "")
    say = lambda m: problems.append("%s: %s" % (os.path.basename(path), m))
    if os.path.basename(path) != bid + ".json":
        say("the file is not named for its id")
    for k in ("name", "class", "expression", "silhouette", "spark", "nature", "calls", "hybrid", "settled", "paths"):
        if k not in b:
            say("no %s" % k)
    if problems:
        return problems, 0
    if b["class"] not in CLASSES:
        say("class %s is not one of %s" % (b["class"], sorted(CLASSES)))
    if b["expression"] not in EXPRESSIONS:
        say("expression %s" % b["expression"])
    own = {f["id"] for f in b.get("newFeatures", [])}
    for f in b.get("newFeatures", []):
        for k in ("id", "slot", "label"):
            if k not in f:
                say("newFeatures: %s has no %s" % (f.get("id", "?"), k))

    def leans(where, d, need=True):
        if need and not d:
            say("%s leans on nothing: every form past the settled one must say what play leads to it" % where)
        for line, keys in d.items():
            if line not in LEANS:
                say("%s leans on %s, which is not a line of the Tally (%s)" % (where, line, ", ".join(sorted(LEANS))))
                continue
            for k, w in keys.items():
                if k not in LEANS[line]:
                    say("%s leans on %s.%s; %s has %s" % (where, line, k, line, ", ".join(sorted(LEANS[line]))))
                if not (0 < float(w) <= 1.0):
                    say("%s: %s.%s is %s, not in (0, 1]" % (where, line, k, w))

    def node(nd, level, need_leans=True):
        for k in ("id", "name", "text", "features"):
            if k not in nd:
                say("a level %d form has no %s (%s)" % (level, k, nd.get("id", nd.get("name", "?"))))
                return
        if not nd["id"].startswith(bid + "-"):
            say("%s: an id begins with its base's (%s-)" % (nd["id"], bid))
        if nd["id"] in all_ids:
            say("%s is used twice" % nd["id"])
        all_ids.add(nd["id"])
        if nd["name"] in all_names:
            say("the name %s is used twice (here by %s, before by %s)" % (nd["name"], nd["id"], all_names[nd["name"]]))
        all_names[nd["name"]] = nd["id"]
        if not (20 <= len(nd["text"]) <= 200):
            say("%s: its text is %d characters; one or two plain sentences" % (nd["id"], len(nd["text"])))
        if not (1 <= len(nd["features"]) <= 3):
            say("%s adds %d features; one to three" % (nd["id"], len(nd["features"])))
        for f in nd["features"]:
            if f not in known_features and f not in own:
                say("%s: feature %s is not in data/features.json nor in this base's newFeatures" % (nd["id"], f))
        if "silhouette" in nd and nd["silhouette"] not in bodies:
            say("%s: no body %s in game/assets/genius/bodies" % (nd["id"], nd["silhouette"]))
        if need_leans:
            leans(nd["id"], nd.get("leans", {}))

    if b["silhouette"] not in bodies:
        say("no body %s in game/assets/genius/bodies (a base may name one that is still to be built: list it in toBuild)" % b["silhouette"]) if b["silhouette"] not in b.get("toBuild", []) else None
    leans("nature", b["nature"])
    for line, keys in b["calls"].items():
        if line not in CALLS:
            say("calls.%s: the first Reading reads seed, shape and blood" % line)
        for k in keys:
            if line == "seed" and k not in seeds:
                say("calls.seed.%s is not a Seed" % k)
            if line == "blood" and k not in bloods:
                say("calls.blood.%s is not a blood" % k)
            if line == "shape" and k not in LEANS["shape"]:
                say("calls.shape.%s is not a Shape" % k)
    for k in ("adj", "gift", "text"):
        if k not in b["hybrid"]:
            say("hybrid has no %s" % k)
    for f in b["hybrid"].get("gift", []):
        if f not in known_features and f not in own:
            say("hybrid.gift: feature %s is unknown" % f)
    node(b["settled"], 1, need_leans=False)
    count = 1
    if len(b["paths"]) != 3:
        say("%d paths; three" % len(b["paths"]))
    for p in b["paths"]:
        node(p, 2)
        count += 1
        if len(p.get("prongs", [])) != 3:
            say("%s has %d prongs; three" % (p.get("id"), len(p.get("prongs", []))))
        for q in p.get("prongs", []):
            node(q, 3)
            count += 1
            if len(q.get("finishes", [])) != 2:
                say("%s has %d finishes; two" % (q.get("id"), len(q.get("finishes", []))))
            for f in q.get("finishes", []):
                node(f, 4)
                count += 1
    return problems, count


def main():
    known = {x["id"] for x in json.load(open(os.path.join(ROOT, "data", "features.json")))}
    seeds = {s["id"] for s in (lambda d: d["seeds"] if isinstance(d, dict) else d)(json.load(open(os.path.join(ROOT, "data", "seeds.json"))))}
    bloods = {b["id"] for b in json.load(open(os.path.join(ROOT, "data", "bloods.json")))}
    bodies = {f[:-4] for f in os.listdir(os.path.join(ROOT, "game", "assets", "genius", "bodies")) if f.endswith(".glb")}
    want = sys.argv[1:]
    files = sorted(f for f in os.listdir(BASES) if f.endswith(".json") and (not want or f[:-5] in want))
    ids, names, total, bad = set(), {}, 0, 0
    for f in files:
        problems, count = check(os.path.join(BASES, f), known, seeds, bloods, bodies, ids, names)
        total += count
        for p in problems:
            print("  " + p)
        bad += len(problems)
        print("%-14s %2d forms%s" % (f[:-5], count, "" if count == 31 and not problems else "   <-- " + ("%d problems" % len(problems) if problems else "not 31")))
    print("%d bases, %d forms, %d problems" % (len(files), total, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
