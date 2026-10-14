"""Research: draft maps of Rebecca's mountain with organic shapes.

Outdoor places are irregular clearings, buildings are rough rectangles, and
the walks between them are winding trails. The proposed path places
(paths.ts) take the place of the links they split, as narrow winding bands
of their own. Three styles to compare: RE1's green, the same over terrain,
and a ranger's ink map.

    node tools/rebecca/plan/research/world.ts > /tmp/world.json
    python3 tools/rebecca/plan/research/world_maps.py /tmp/world.json <outdir>

Writes world-<style>.png (the whole mountain) and <area>-<style>.png
(RE1's 128 x 128 area map, shown at 3x).
"""
import json
import math
import random
import sys
import zlib

from PIL import Image, ImageDraw, ImageFilter

# Rooms underground: rough rock outlines, not walls.
CAVES = {"tunnel", "junction", "gallery", "crawl"}
SX, SY = 1.0, 1.0  # positions are already in metres (layout.ts)
AREA_PX = 128
SHOW = 3


def rng_for(key):
    return random.Random(zlib.crc32(key.encode()))


def wobble(rng, n=3):
    """A smooth random function round a circle, about -1..1."""
    terms = [(rng.uniform(0.6, 1.0) / (k + 1), k + 2, rng.uniform(0, 2 * math.pi)) for k in range(n)]
    return lambda t: sum(a * math.sin(f * t + p) for a, f, p in terms)


def blob(cx, cy, w, h, key, rough=0.22, points=40):
    """An irregular clearing about w x h metres."""
    rng = rng_for(key)
    f = wobble(rng)
    out = []
    for i in range(points):
        t = 2 * math.pi * i / points
        r = 1 + rough * f(t)
        out.append((cx + math.cos(t) * w / 2 * r, cy + math.sin(t) * h / 2 * r))
    return out


def rough_rect(cx, cy, w, h, key, jitter=0.35):
    """A building's floor, its corners a little off true, as if inked by hand."""
    rng = rng_for(key)
    pts = []
    for x, y in ((-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)):
        pts.append((cx + x * w / 2 + rng.uniform(-jitter, jitter), cy + y * h / 2 + rng.uniform(-jitter, jitter)))
    return pts


def trail(a, b, key, wiggle=0.12, steps=36):
    """A winding line from a to b."""
    rng = rng_for(key)
    f = wobble(rng, 3)
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy) or 1
    nx, ny = -dy / length, dx / length
    pts = []
    for i in range(steps + 1):
        s = i / steps
        bend = math.sin(math.pi * s) * wiggle * length * f(s * math.pi * 0.8 + 0.4)
        pts.append((ax + dx * s + nx * bend, ay + dy * s + ny * bend))
    return pts


def edge_point(poly, toward):
    """The point of a shape's outline nearest the direction of `toward` from its centre."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    ang = math.atan2(toward[1] - cy, toward[0] - cx)
    best = min(poly, key=lambda p: abs(math.atan2(math.sin(math.atan2(p[1] - cy, p[0] - cx) - ang), math.cos(math.atan2(p[1] - cy, p[0] - cx) - ang))))
    return best


class World:
    def __init__(self, data):
        self.places = {p["id"]: p for p in data["places"]}
        self.areas = data["areas"]
        self.paths = data["paths"]
        self.shapes = {}
        self.centre = {}
        for p in data["places"]:
            x, y = p["at"][0] * SX, p["at"][1] * SY
            w, h = p["floor"]
            # Places draw larger than life against the trails, as a map does.
            k = 1.5
            w, h = max(4.0, w * k), max(3.5, h * k)
            self.centre[p["id"]] = (x, y)
            if p["id"] in CAVES:
                self.shapes[p["id"]] = blob(x, y, w, h, p["id"], rough=0.38, points=26)
            elif p["inside"]:
                self.shapes[p["id"]] = rough_rect(x, y, w, h, p["id"])
            else:
                self.shapes[p["id"]] = blob(x, y, w, h, p["id"])
        split = {tuple(sorted(pp["between"])): pp for pp in self.paths}
        self.links = []  # (from, to, kind, key)
        self.bands = []  # (id, points, width, area)
        for l in data["links"]:
            pp = split.get(tuple(sorted((l["from"], l["to"]))))
            if pp is None:
                self.links.append((l["from"], l["to"], l["kind"], f'{l["from"]}>{l["to"]}'))
                continue
            # The path place: a band from one end to the other, winding more the longer it is.
            a = edge_point(self.shapes[l["from"]], self.centre[l["to"]])
            b = edge_point(self.shapes[l["to"]], self.centre[l["from"]])
            width = {"trail": 3.2, "ledge": 2.4, "lane": 4.5, "slope": 5.5}[pp["shape"]]
            self.bands.append((pp["id"], trail(a, b, pp["id"], wiggle=0.18), width, self.places[l["from"]]["area"]))

    def area_box(self, area):
        ids = [p for p in self.places if self.places[p]["area"] == area]
        pts = [q for i in ids for q in self.shapes[i]]
        pts += [q for _, band, _, a in self.bands if a == area for q in band]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)


# --- Styles -----------------------------------------------------------------

STYLES = {
    "green": dict(bg=(0, 0, 0), fill=(26, 140, 26), edge=(150, 210, 90), dim=(14, 52, 14), dim_edge=(52, 100, 44), trail=(120, 190, 70), dim_trail=(44, 86, 38), door=(240, 190, 40), here=(230, 60, 70), terrain=False, ink=False),
    "terrain": dict(bg=(4, 10, 6), fill=(30, 140, 30), edge=(160, 215, 100), dim=(16, 56, 16), dim_edge=(56, 104, 48), trail=(170, 200, 90), dim_trail=(60, 90, 44), door=(240, 190, 40), here=(230, 60, 70), terrain=True, ink=False),
    "ink": dict(bg=(214, 202, 170), fill=(232, 222, 192), edge=(70, 50, 30), dim=(214, 202, 170), dim_edge=(140, 120, 90), trail=(90, 60, 30), dim_trail=(150, 130, 100), door=(170, 40, 30), here=(170, 40, 30), terrain=False, ink=True),
}


def terrain(img, to_px, scale, key):
    """Dark forest speckle and a few contour lines behind the map."""
    rng = rng_for(key)
    d = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(int(w * h / 18)):
        x, y = rng.randrange(w), rng.randrange(h)
        g = rng.randrange(14, 34)
        d.point((x, y), fill=(4, g, 8))
    for i in range(6):
        f = wobble(rng_for(f"{key}c{i}"), 3)
        base = h * (i + 0.5) / 6
        pts = [(x, base + 9 * scale * f(x / w * 6)) for x in range(0, w, 2)]
        d.line(pts, fill=(18, 40, 22), width=1)


def render(world, style, box, size, visited=None, here=None, area=None):
    s = STYLES[style]
    x0, y0, x1, y1 = box
    pad = 6
    scale = min((size - 2 * pad) / (x1 - x0), (size - 2 * pad) / (y1 - y0))
    ox = (size - (x1 - x0) * scale) / 2 - x0 * scale
    oy = (size - (y1 - y0) * scale) / 2 - y0 * scale

    def px(p):
        return (p[0] * scale + ox, p[1] * scale + oy)

    img = Image.new("RGB", (size, size), s["bg"])
    if s["terrain"]:
        terrain(img, px, max(1.0, size / 128), "mountain")
    d = ImageDraw.Draw(img)
    seen = (lambda i: True) if visited is None else (lambda i: i in visited)
    shown = (lambda i: True) if area is None else (lambda i: world.places[i]["area"] == area)
    doors = []

    def stroke(points, width_m, colour):
        r = max(1.0, width_m * scale / 2)
        pts = [px(p) for p in points]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay)))
            for k in range(n + 1):
                x, y = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
                d.ellipse((x - r, y - r, x + r, y + r), fill=colour)

    # The outdoor ground is one shape: clearings, trails and path places drawn
    # outline first, then filled, so they join with no seams. Buildings and
    # their doors go on top.
    inside = lambda i: world.places[i]["inside"]
    ground = []  # (kind, data, lit)
    for a, b, kind, key in world.links:
        if not (shown(a) or shown(b)):
            continue
        pa = edge_point(world.shapes[a], world.centre[b])
        pb = edge_point(world.shapes[b], world.centre[a])
        lit = seen(a) or seen(b)
        if kind in ("ride", "lift"):
            ground.append(("cable", (pa, pb), lit))
        elif inside(a) or inside(b):
            ground.append(("door", (pa, pb), lit))
        else:
            ground.append(("trail", trail(pa, pb, key), lit))
        # A way off this map gets a mark where it leaves.
        if area is not None and (shown(a) != shown(b)):
            doors.append(pa if shown(a) else pb)
    for pid, band, width, a in world.bands:
        if area is not None and a != area:
            continue
        ground.append(("band", (band, width), visited is None or pid in visited))
    outdoor = [pid for pid in world.shapes if shown(pid) and not inside(pid)]
    for layer in ("edge", "fill"):
        for kind, data, lit in ground:
            if kind == "trail":
                stroke(data, 2.2 + (1.4 if layer == "edge" else 0), (s["edge"] if lit else s["dim_edge"]) if layer == "edge" else (s["fill"] if lit else s["dim"]))
            elif kind == "band":
                band, width = data
                stroke(band, width + (1.4 if layer == "edge" else 0), (s["edge"] if lit else s["dim_edge"]) if layer == "edge" else (s["fill"] if lit else s["dim"]))
        for pid in outdoor:
            poly = [px(p) for p in world.shapes[pid]]
            lit = seen(pid)
            if layer == "edge":
                d.polygon(poly, fill=s["edge"] if lit else s["dim_edge"])
                d.line(poly + [poly[0]], fill=s["edge"] if lit else s["dim_edge"], width=3)
            else:
                d.polygon(poly, fill=s["here"] if pid == here else (s["fill"] if lit else s["dim"]))
    for kind, data, lit in ground:
        if kind == "cable":
            pts = [px(data[0]), px(data[1])]
            n = int(math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) / 4) or 1
            for k in range(0, n, 2):
                q0 = (pts[0][0] + (pts[1][0] - pts[0][0]) * k / n, pts[0][1] + (pts[1][1] - pts[0][1]) * k / n)
                q1 = (pts[0][0] + (pts[1][0] - pts[0][0]) * (k + 1) / n, pts[0][1] + (pts[1][1] - pts[0][1]) * (k + 1) / n)
                d.line((q0, q1), fill=s["trail"] if lit else s["dim_trail"], width=1)
        elif kind == "door":
            stroke(list(data), 1.2, s["fill"] if lit else s["dim"])
            doors.append(data[0] if any(inside(i) and world.shapes[i] and data[0] in world.shapes[i] for i in world.shapes) else data[1])
    for pid, poly in world.shapes.items():
        if not shown(pid) or not inside(pid):
            continue
        lit = seen(pid)
        fill = s["here"] if pid == here else (s["fill"] if lit else s["dim"])
        d.polygon([px(p) for p in poly], fill=fill, outline=s["edge"] if lit else s["dim_edge"])
        if s["ink"] and pid not in CAVES:
            xs = [px(p)[0] for p in poly]
            ys = [px(p)[1] for p in poly]
            for x in range(int(min(xs)) + 2, int(max(xs)) - 1, 3):
                d.line(((x, min(ys) + 2), (x + 2, max(ys) - 2)), fill=s["dim_edge"])
    r = max(1.0, scale * 0.9)
    for p in doors:
        x, y = px(p)
        d.rectangle((x - r, y - r, x + r, y + r), fill=s["door"])
    return img


def main():
    data = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    world = World(data)
    allx = [p[0] for poly in world.shapes.values() for p in poly]
    ally = [p[1] for poly in world.shapes.values() for p in poly]
    whole = (min(allx), min(ally), max(allx), max(ally))
    for style in STYLES:
        render(world, style, whole, 900).save(f"{out}/world-{style}.png")
    for a in world.areas:
        box = world.area_box(a["id"])
        ids = a["places"]
        half = set(ids[: max(1, (len(ids) + 1) // 2)]) | {b[0] for b in world.bands if b[3] == a["id"]}
        for style in STYLES:
            img = render(world, style, box, AREA_PX, visited=half, here=ids[(len(ids) - 1) // 2], area=a["id"])
            img.resize((AREA_PX * SHOW, AREA_PX * SHOW), Image.NEAREST).save(f"{out}/{a['id']}-{style}.png")
    print(f"{len(world.shapes)} places, {len(world.bands)} path places, {len(world.links)} links")


if __name__ == "__main__":
    main()
