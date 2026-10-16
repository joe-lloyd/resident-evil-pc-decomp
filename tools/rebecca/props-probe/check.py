"""Summarise probe JSON: python3 check.py <dir> [slug ...]. Flags props that
moved after the kit placed them, bodies not lying on what is under them, and
furniture not standing on its floor."""
import json
import math
import os
import sys

d = sys.argv[1]
slugs = sys.argv[2:] or sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def surface(p):
    """The highest thing under the prop's centre at or below its bottom
    (plus 0.15 m): what it stands or lies on. Things met higher up sit on it
    or cut through it."""
    hits = p.get("under") or []
    z0 = p["box"][2]
    below = [h for h in hits if h[1] <= z0 + 0.15]
    return (below[0] if below else None), [h for h in hits if h[1] > z0 + 0.15]


for slug in slugs:
    data = json.load(open(os.path.join(d, slug + ".json")))
    print(f"== {slug}")
    for p in data["props"]:
        if p.get("gone"):
            print(f"  GONE {p['kind']} {p['name']}")
            continue
        b = p["box"]
        cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
        sup, over = surface(p)
        s = sup[1] if sup else None
        flags = []
        if sup is None and not p.get("hidden"):
            flags.append("NO-SUPPORT")
        if "kit_box" in p:
            k = p["kit_box"]
            kx, ky = (k[0] + k[3]) / 2, (k[1] + k[4]) / 2
            moved = math.hypot(cx - kx, cy - ky)
            dz = b[2] - k[2]
            if moved > 0.02 or abs(dz) > 0.02 or abs((b[5] - b[2]) - (k[5] - k[2])) > 0.02:
                flags.append(f"MOVED xy {moved:.2f} dz {dz:+.2f} h {b[5]-b[2]:.2f}/{k[5]-k[2]:.2f}")
            at = p["args"].get("at")
            if p["kind"] != "body" and at and not p["args"].get("tipped"):
                off = math.hypot(cx - at[0], cy - at[1])
                if off > 0.1:
                    flags.append(f"OFF-AT {off:.2f}")
        if s is not None and not p.get("hidden"):
            if p["kind"] == "body" and p.get("args", {}).get("pose") != "slumped":
                if b[5] - s > 0.4:
                    flags.append(f"HIGH top {b[5]-s:.2f}")
                if b[2] - s < -0.05:
                    flags.append(f"SUNK {b[2]-s:.2f}")
            elif p["kind"] in ("bunk", "chair", "crate"):
                if abs(b[2] - s) > 0.05:
                    flags.append(f"FLOOR {b[2]-s:+.2f}")
        a = p.get("args", {})
        desc = f"at={[round(v, 2) for v in a['at']]}" if "at" in a else ""
        for key in ("heading", "rot", "pose", "tipped", "sheet"):
            if key in a:
                v = a[key]
                desc += f" {key}={round(v, 2) if isinstance(v, float) else v}"
        extra = f" over={over}" if over and flags else ""
        print(f"  {'!!' if flags else 'ok'} {p['kind']:7} {p['name'][:30]:30} c=({cx:.2f},{cy:.2f}) z {b[2]:.2f}..{b[5]:.2f} on={sup} {desc} {' '.join(flags)}{extra}")
