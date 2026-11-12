"""What a person's .glb is made of: bytes by mesh (the base and the shape keys apart), and the animations."""
import json, struct, sys, collections

def load(path):
    f = open(path, "rb")
    magic, ver, total = struct.unpack("<III", f.read(12))
    ln, kind = struct.unpack("<II", f.read(8))
    return json.loads(f.read(ln)), total

for path in sys.argv[1:]:
    g, total = load(path)
    acc, bv = g["accessors"], g["bufferViews"]
    size = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
    comp = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    def nbytes(i):
        a = acc[i]
        return a["count"] * size[a["type"]] * comp[a["componentType"]]
    rows = []
    tb = tk = 0
    for m in g["meshes"]:
        base = keys = verts = 0
        nk = 0
        for p in m["primitives"]:
            for k, i in p["attributes"].items():
                base += nbytes(i)
                if k == "POSITION":
                    verts += acc[i]["count"]
            if "indices" in p:
                base += nbytes(p["indices"])
            for t in p.get("targets", []):
                for k, i in t.items():
                    keys += nbytes(i)
            nk = max(nk, len(p.get("targets", [])))
        rows.append((m["name"], verts, base, keys, nk))
        tb += base
        tk += keys
    anim = 0
    seen = set()
    for a in g.get("animations", []):
        for s in a["samplers"]:
            for i in (s["input"], s["output"]):
                if i not in seen:
                    seen.add(i)
                    anim += nbytes(i)
    print(path.split("/")[-1], "total %.2f MB: meshes %.2f MB, shape keys %.2f MB, animations %.2f MB" % (total / 1e6, tb / 1e6, tk / 1e6, anim / 1e6))
    groups = collections.OrderedDict()
    for name, verts, base, keys, nk in rows:
        kind = name.split("_")[0] if not name.startswith("Dress") else name.split("__")[0]
        if name.startswith("Hair_"):
            kind = "Hair (all styles)"
        if name.startswith("Beard_"):
            kind = "Beards"
        if name.startswith("Mark_"):
            kind = "Marks"
        e = groups.setdefault(kind, [0, 0, 0, 0, 0])
        e[0] += verts; e[1] += base; e[2] += keys; e[3] = max(e[3], nk); e[4] += 1
    for kind, (verts, base, keys, nk, cnt) in groups.items():
        print("   %-22s %2d meshes %6d verts  base %7.1f KB  keys %7.1f KB (%d keys)" % (kind, cnt, verts, base / 1e3, keys / 1e3, nk))
    if "-v" in sys.argv:
        for r in rows:
            print("      ", r)
