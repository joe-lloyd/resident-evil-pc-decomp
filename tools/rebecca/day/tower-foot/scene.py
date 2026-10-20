"""The foot of the fire lookout tower, afternoon.

What it tells: ARKLAY FIRE LOOKOUT, built 1953, a timber tower on the bald
top of the hill, its cab 18 m up. Walt, the lookout, rode up the track on
his bicycle for the season; it lies where he dropped it, one wheel still
turning in the wind. Last night he saw smoke in the valley and logged it.
Before dawn he came off the catwalk. He lies crumpled on the rocks at the
east foot of the tower, blood over the stones, his cap thrown off, flies on
him. The stair starts inside a chain-link cage at the west foot; its door
stands open, the padlock hanging off the hasp. The hoist rope he hauled his water up on hangs from the deck and
swings, and the old tower creaks.

Metres: the floor is x 1-19, y 2-12. The tower stands at x 9, y 6.5: four
timber legs on footings at x 5 and 13, y 2.5 and 10.5. The first flight
starts at its west side inside the cage, x 6.3-7.7, y 6.55-7.55, whose door
is in the cage's west side. Walt lies at x 13-15, y 7.5-9. The track comes
in from the washout at the east edge, y 5.5-8.5, past the lookout's sign. The
privy is in the south-west corner; the hill falls away west and south.

Moving: the hoist rope swinging, the bicycle's front wheel turning, flies on
the body, the grass, dust in the low sun.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 1.0, 19.0, 2.0, 12.0
TC = (9.0, 6.5)
CAGE = (6.3, 7.7, 6.55, 7.55)
BODY = (13.7, 8.2)
CAMS = [(19.9, 12.9, 3.6), (1.6, 3.0, 2.7), (20.2, 0.9, 3.0)]


# ---- The fire lookout tower. The same code is in every scene that shows it
# (washout, tower-foot, tower-stairs, tower-top), so it matches. Heights are
# from its own ground: four timber legs from an 8 m square at the ground to a
# 4.8 m square at the cab floor, 18 m up; girts and X bracing at 3, 6, 9, 12
# and 15 m, nothing but the legs below 3 m; zig-zag flights inside the legs,
# east on the south side and west on the north; landings at 3, 6, 9 and 12 m; a deck right across the frame
# at 15 m; the last flight up through a hatch in the cab floor. The cab is
# 4.8 m square with a catwalk round it to 3.3 m from the centre.

TOWER_CAB = 18.0
TOWER_DECK = 15.0
TOWER_LEVELS = (3.0, 6.0, 9.0, 12.0, 15.0)
FLIGHT_X = 1.5
FLIGHT_W = 0.9
CATWALK = 3.3
HATCH = (-1.65, -1.0, 0.45, -0.1)   # x0, y0, x1, y1 of the hatch in the cab floor, from the centre
BROKEN_RAIL = (1.0, 2.1)            # y from the centre: the gap in the catwalk's east top rail


def tower_hw(z):
    """Half the frame's width at height z."""
    return 4.0 - 1.6 * z / TOWER_CAB


def flight_of(i):
    """Flight i climbs from 3i to 3i + 3 m. Returns x0, x1 (from the centre) and y."""
    return (-FLIGHT_X, FLIGHT_X, 0.55) if i % 2 == 0 else (FLIGHT_X, -FLIGHT_X, -0.55)


class Beams:
    """Many boxes in one mesh per material, to keep the object count down."""

    def __init__(self):
        self.parts = {}

    def box(self, m, a, b, w, d=None):
        """A beam from a to b, w across and d deep (d upward where it can be)."""
        a, b = Vector(a), Vector(b)
        ax = b - a
        if ax.length < 1e-6:
            return
        n = ax.normalized()
        ref = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
        s = n.cross(ref).normalized() * (w / 2)
        u = s.cross(n).normalized() * ((d or w) / 2)
        v, f = self.parts.setdefault(m, ([], []))
        k = len(v)
        for p in (a, b):
            for c in (-s - u, s - u, s + u, -s + u):
                v.append(tuple(p + c))
        f += [(k, k + 1, k + 2, k + 3), (k + 4, k + 7, k + 6, k + 5), (k, k + 4, k + 5, k + 1),
              (k + 1, k + 5, k + 6, k + 2), (k + 2, k + 6, k + 7, k + 3), (k + 3, k + 7, k + 4, k)]

    def slab(self, m, x0, y0, x1, y1, z0, z1):
        """An axis-aligned block."""
        self.box(m, (x0, (y0 + y1) / 2, (z0 + z1) / 2), (x1, (y0 + y1) / 2, (z0 + z1) / 2), y1 - y0, z1 - z0)

    def build(self, name):
        """One object per material. Glass casts no shadow, so the sun gets in."""
        obs = [reb.mesh_object(f"{name}, {m.name}", v, f, m, smooth=False) for m, (v, f) in self.parts.items()]
        for ob in obs:
            if "glass" in ob.data.materials[0].name.lower():
                ob.visible_shadow = False
        return obs


def tower(bm, timber, c, z0, below=-1.0, above=99.0, flights=range(6), deck=True, cab=True, floor_bm=None):
    """The tower's frame, flights, deck, cab floor and catwalk about centre
    c = (x, y), its ground at z0. Only parts between heights `below` and
    `above` (from its ground) are built. The deck and the cab's floor and
    catwalk go into floor_bm when given (a floor must not be a mask)."""
    cx, cy = c
    fb = floor_bm or bm

    def P(x, y, z):
        return (cx + x, cy + y, z0 + z)

    def corner(i, z):
        sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[i]
        h = tower_hw(z)
        return P(sx * h, sy * h, z)

    def want(za, zb):
        return zb >= below and za <= above

    for i in range(4):
        za, zb = max(-0.5, below - 1.0), min(TOWER_CAB, above + 1.0)
        if zb > za:
            a, b = Vector(corner(i, 0.0)), Vector(corner(i, TOWER_CAB))
            d = b - a
            bm.box(timber, a + d * (za / TOWER_CAB), a + d * (zb / TOWER_CAB), 0.32)
    levels = TOWER_LEVELS + (TOWER_CAB,)    # open below 3 m, so you can walk in under it
    for z in levels:
        if want(z - 0.3, z + 0.3):
            for i in range(4):
                bm.box(timber, corner(i, z), corner((i + 1) % 4, z), 0.2, 0.26)
    for za, zb in zip(levels, levels[1:]):
        if want(za, zb):
            for i in range(4):
                j = (i + 1) % 4
                bm.box(timber, corner(i, za), corner(j, zb), 0.12, 0.2)
                bm.box(timber, corner(j, za), corner(i, zb), 0.12, 0.2)
    for i in flights:
        za, zb = 3.0 * i, 3.0 * i + 3.0
        if not want(za, zb):
            continue
        x0, x1, y = flight_of(i)
        for dy in (-FLIGHT_W / 2, FLIGHT_W / 2):
            bm.box(timber, P(x0, y + dy, za - 0.1), P(x1, y + dy, zb - 0.1), 0.07, 0.26)
            bm.box(timber, P(x0, y + dy, za + 0.95), P(x1, y + dy, zb + 0.95), 0.06, 0.08)
            for t in (0.0, 0.5, 1.0):
                x, z = x0 + (x1 - x0) * t, za + (zb - za) * t
                bm.box(timber, P(x, y + dy, z - 0.1), P(x, y + dy, z + 0.95), 0.06)
        for k in range(1, 12):
            t = k / 12
            x, z = x0 + (x1 - x0) * t, za + (zb - za) * t
            bm.box(timber, P(x, y - FLIGHT_W / 2, z), P(x, y + FLIGHT_W / 2, z), 0.26, 0.04)
    for n, z in enumerate(TOWER_LEVELS[:-1]):
        if want(z - 0.2, z + 1.1):
            side = 1 if n % 2 == 0 else -1
            xa, xb = sorted((side * FLIGHT_X, side * (FLIGHT_X + 1.0)))
            bm.slab(timber, cx + xa, cy - 1.05, cx + xb, cy + 1.05, z0 + z - 0.06, z0 + z)
            xo = side * (FLIGHT_X + 1.0)
            for yy in (-1.05, 1.05):
                bm.box(timber, P(xo, yy, z), P(xo, yy, z + 1.0), 0.06)
            bm.box(timber, P(xo, -1.05, z + 1.0), P(xo, 1.05, z + 1.0), 0.06, 0.08)
    if deck and want(TOWER_DECK - 0.3, TOWER_DECK + 1.2):
        h = tower_hw(TOWER_DECK) + 0.2
        for xa, ya, xb, yb in ((-h, -h, h, 0.1), (-h, 0.1, -0.5, 1.0), (FLIGHT_X, 0.1, h, 1.0), (-h, 1.0, h, h)):
            fb.slab(timber, cx + xa, cy + ya, cx + xb, cy + yb, z0 + TOWER_DECK - 0.08, z0 + TOWER_DECK)
        for yy in (0.1, 1.0):
            bm.box(timber, P(-0.5, yy, TOWER_DECK + 1.0), P(FLIGHT_X, yy, TOWER_DECK + 1.0), 0.06, 0.08)
            bm.box(timber, P(-0.5, yy, TOWER_DECK), P(-0.5, yy, TOWER_DECK + 1.0), 0.06)
        # The deck's rail, with the gap on the west where the outside flight hung.
        for xa, ya, xb, yb in ((-h, -h, h, -h), (h, -h, h, h), (h, h, -h, h), (-h, h, -h, 0.45), (-h, -0.55, -h, -h)):
            for zz in (0.55, 1.05):
                bm.box(timber, P(xa, ya, TOWER_DECK + zz), P(xb, yb, TOWER_DECK + zz), 0.07, 0.1)
            n = max(1, int(round(max(abs(xb - xa), abs(yb - ya)) / 1.4)))
            for k in range(n + 1):
                x, y = xa + (xb - xa) * k / n, ya + (yb - ya) * k / n
                bm.box(timber, P(x, y, TOWER_DECK), P(x, y, TOWER_DECK + 1.05), 0.08)
    if cab and want(TOWER_CAB - 2.0, TOWER_CAB + 4.0):
        h = tower_hw(TOWER_CAB)
        hx0, hy0, hx1, hy1 = HATCH
        for xa, ya, xb, yb in ((-CATWALK, -CATWALK, CATWALK, hy0), (-CATWALK, hy0, hx0, hy1), (hx1, hy0, CATWALK, hy1), (-CATWALK, hy1, CATWALK, CATWALK)):
            fb.slab(timber, cx + xa, cy + ya, cx + xb, cy + yb, z0 + TOWER_CAB - 0.1, z0 + TOWER_CAB)
        for i in range(4):
            sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[i]
            bm.box(timber, P(sx * h, sy * h, TOWER_CAB - 1.6), P(sx * (CATWALK - 0.1), sy * (CATWALK - 0.1), TOWER_CAB - 0.15), 0.12, 0.16)
            bm.box(timber, P(sx * h, sy * h, TOWER_CAB - 0.2), P(sx * CATWALK, sy * CATWALK, TOWER_CAB - 0.2), 0.16, 0.2)
        for xa, ya, xb, yb in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
            a = Vector(P(xa * CATWALK, ya * CATWALK, TOWER_CAB))
            b = Vector(P(xb * CATWALK, yb * CATWALK, TOWER_CAB))
            for zz in (0.5, 1.05):
                if xa == xb == 1 and zz > 1.0:
                    # The east top rail, broken where Walt went over it.
                    g0, g1 = BROKEN_RAIL
                    bm.box(timber, a + Vector((0, 0, zz)), Vector(P(CATWALK, g0, TOWER_CAB + zz)), 0.07, 0.1)
                    bm.box(timber, Vector(P(CATWALK, g1, TOWER_CAB + zz)), b + Vector((0, 0, zz)), 0.07, 0.1)
                    continue
                bm.box(timber, a + Vector((0, 0, zz)), b + Vector((0, 0, zz)), 0.07, 0.1)
            for t in (0.0, 0.25, 0.5, 0.75):
                p = a.lerp(b, t)
                bm.box(timber, p, p + Vector((0, 0, 1.05)), 0.08)
    return P


def cab_shell(bm, timber, glass, c, z0, door=(0.3, 1.1), roof_m=None):
    """The cab's walls: boards to 1 m, windows all round to 2.1 m, boards to
    2.45 m, a hip roof. The door is in the south wall at x door[0]..door[1]
    from the centre. Returns the roof object."""
    cx, cy = c
    z = z0 + TOWER_CAB
    h = tower_hw(TOWER_CAB) - 0.1
    for side in "nsew":
        spans = ((-h, door[0]), (door[1], h)) if side == "s" else ((-h, h),)
        for a0, a1 in spans:
            for za, zb in ((0.0, 1.0), (2.1, 2.45)):
                if side in "ns":
                    y = cy + (h if side == "s" else -h)
                    bm.slab(timber, cx + a0, y - 0.05, cx + a1, y + 0.05, z + za, z + zb)
                else:
                    x = cx + (h if side == "e" else -h)
                    bm.slab(timber, x - 0.05, cy + a0, x + 0.05, cy + a1, z + za, z + zb)
            for k in range(3):
                t = a0 + (a1 - a0) * k / 2
                if side in "ns":
                    y = cy + (h if side == "s" else -h)
                    bm.box(timber, (cx + t, y, z + 1.0), (cx + t, y, z + 2.1), 0.08, 0.1)
                else:
                    x = cx + (h if side == "e" else -h)
                    bm.box(timber, (x, cy + t, z + 1.0), (x, cy + t, z + 2.1), 0.08, 0.1)
            if side in "ns":
                y = cy + (h if side == "s" else -h)
                bm.slab(glass, cx + a0, y - 0.006, cx + a1, y + 0.006, z + 1.0, z + 2.1)
            else:
                x = cx + (h if side == "e" else -h)
                bm.slab(glass, x - 0.006, cy + a0, x + 0.006, cy + a1, z + 1.0, z + 2.1)
    bm.slab(timber, cx + door[0], cy + h - 0.05, cx + door[1], cy + h + 0.05, z + 2.05, z + 2.45)
    e = h + 0.75
    zr = z + 2.45
    v = [(cx - e, cy - e, zr), (cx + e, cy - e, zr), (cx + e, cy + e, zr), (cx - e, cy + e, zr), (cx, cy, z + 3.6)]
    roof = reb.mesh_object("Cab roof", v, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)], roof_m or timber, smooth=False)
    kit.rod("Lightning rod", mat("iron"), (cx, cy, z + 3.6), (cx, cy, z + 4.6), 0.015, 6)
    return roof


def height(x, y):
    """The hilltop flat where she walks, falling away all round, least to the east."""
    if X0 - 0.4 < x < X1 + 0.4 and Y0 - 0.4 < y < Y1 + 0.4:
        return 0.0
    h = 0.4 * noise.noise(Vector((x * 0.12, y * 0.12, 6)))
    dx = max(0.0, X0 - 0.4 - x) * 0.45 + max(0.0, x - X1 - 0.4) * 0.12
    dy = max(0.0, Y0 - 0.4 - y) * 0.3 + max(0.0, y - Y1 - 0.4) * 0.45
    return h - dx - dy


def low_sun(heading, elevation, energy, rgb=(1.0, 0.7, 0.42)):
    """The afternoon sun low in the south-west: long shadows, warm light."""
    sun = kit.time_light("afternoon", sun_heading=heading, sun_energy=energy,
                         mist=((10, 7, 4), (80, 60, 18), 0.004))
    sun.rotation_euler[0] = math.radians(90 - elevation)
    sun.data.color = rgb
    bpy.context.view_layer.update()
    kit._sky((0.86, 0.64, 0.44), (0.3, 0.38, 0.56), 0.8, sun)
    return sun


def dust(rng, area, count, z=(0.4, 2.8), name="Dust"):
    """Motes hanging in the sun: tiny specks in one mesh, which drift. None
    within 4 m of a camera, where they would turn into blobs."""
    m = reb.mat_emit(f"{name} motes", (1.0, 0.82, 0.55), 0.8)
    v, f = [], []
    for _ in range(count * 3):
        if len(f) >= count * 4:
            break
        c = Vector((rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3]), rng.uniform(*z)))
        if any((c - Vector(e)).length < 4.0 for e in CAMS):
            continue
        s = rng.uniform(0.004, 0.007)
        k = len(v)
        v += [tuple(c + Vector((s, 0, 0))), tuple(c + Vector((-s, s, 0))), tuple(c + Vector((-s, -s, 0))), tuple(c + Vector((0, 0, s * 1.5)))]
        f += [(k, k + 1, k + 2), (k, k + 1, k + 3), (k + 1, k + 2, k + 3), (k, k + 2, k + 3)]
    return reb.mesh_object(name, v, f, m, smooth=False)


def flat_join(name, parts):
    """kit.join, with each part's own turn and place baked into its mesh
    first, so the joined object sits at the origin unturned and can be
    placed and turned as a whole."""
    for p in parts:
        p.data.transform(p.matrix_basis)
        p.matrix_basis = Matrix.Identity(4)
    return kit.join(name, parts)


def bicycle(name, at, heading):
    """A bicycle lying on its side. Returns (frame, front wheel) for Anim.spin."""
    frame_m = reb.mat_plain("Bicycle green", (0.05, 0.14, 0.08), 0.4)

    def wheel(wname, centre):
        parts = []
        for k in range(16):
            a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
            parts.append(kit.rod("rim", mat("rubber"), (0.34 * math.cos(a0), 0, 0.34 * math.sin(a0)), (0.34 * math.cos(a1), 0, 0.34 * math.sin(a1)), 0.022, 6))
        for k in range(6):
            a = math.pi * k / 3
            parts.append(kit.rod("spoke", mat("steel"), (0, 0, 0), (0.32 * math.cos(a), 0, 0.32 * math.sin(a)), 0.005, 4))
        parts.append(reb.prim("cyl", "hub", mat("steel"), (0, 0, 0), (0.06, 0.08, 0.06), rot=(math.pi / 2, 0, 0), segments=10))
        w = flat_join(wname, parts)
        w.location = centre
        return w
    pts = {"rear": (-0.52, 0, 0.34), "crank": (0.0, 0, 0.3), "seat": (-0.14, 0, 0.82), "head": (0.42, 0, 0.86), "front": (0.52, 0, 0.34)}
    parts = [kit.rod("tube", frame_m, pts[a], pts[b], 0.018, 8) for a, b in (("rear", "crank"), ("rear", "seat"), ("crank", "seat"), ("seat", "head"), ("crank", "head"), ("head", "front"))]
    parts.append(kit.rod("bars", mat("steel"), (0.38, -0.28, 1.0), (0.38, 0.28, 1.0), 0.012, 6))
    parts.append(kit.rod("stem", mat("steel"), (0.42, 0, 0.86), (0.38, 0, 1.0), 0.012, 6))
    parts.append(reb.prim("cube", "saddle", mat("black"), (-0.16, 0, 0.88), (0.24, 0.12, 0.05), bevel=0.02))
    parts.append(reb.prim("cube", "carrier", mat("steel"), (-0.45, 0, 0.62), (0.4, 0.14, 0.02)))
    fr = flat_join(name, parts)
    back = wheel(f"{name} rear wheel", pts["rear"])
    front = wheel(f"{name} front wheel", pts["front"])
    for w in (back, front):
        w.parent = fr
    fr.location = at
    fr.rotation_euler = (math.pi / 2 - 0.08, 0, heading)
    fr.location.z += 0.05
    return fr, front


def build():
    rng = random.Random(61)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")
    room.camera(CAMS[0], (10.0, 6.5, 0.3), 200, "from where the track comes in: the tower, Walt on the rocks, his bicycle")
    room.camera(CAMS[1], (8.5, 10.0, 0.9), 200, "from the north-west: the open cage at the stair's foot, the body beyond")
    room.camera(CAMS[2], (9.0, 9.0, 0.0), 210, "from the north-east by the sign: under the tower to the privy, the woodpile, the body on the rocks")

    rough = reb.mat_surface("Hilltop", [(0.0, (0.07, 0.07, 0.04)), (0.45, (0.15, 0.15, 0.07)), (0.8, (0.22, 0.19, 0.12)), (1.0, (0.28, 0.27, 0.24))], scale=1.2, bump=0.6)
    track_m = reb.mat_surface("Track dirt", [(0.0, (0.09, 0.07, 0.045)), (0.6, (0.17, 0.13, 0.09)), (1.0, (0.21, 0.18, 0.13))], scale=6, bump=0.6)
    link_m = reb.mat_surface("Chain link", [(0.0, (0.18, 0.18, 0.17)), (1.0, (0.3, 0.3, 0.28))], scale=60, rough=0.5, bump=0.8)
    nodes, links = link_m.node_tree.nodes, link_m.node_tree.links
    holes = nodes.new("ShaderNodeBsdfTransparent")
    see = nodes.new("ShaderNodeMixShader")
    see.inputs["Fac"].default_value = 0.35
    links.new(holes.outputs["BSDF"], see.inputs[1])
    links.new(nodes["Principled BSDF"].outputs["BSDF"], see.inputs[2])
    links.new(see.outputs["Shader"], nodes["Material Output"].inputs["Surface"])
    timber = reb.mat_wood("Tower timber", (0.15, 0.13, 0.11))
    glass = reb.mat_glass("Cab glass", (0.5, 0.55, 0.55))
    rope_m = reb.mat_plain("Rope", (0.35, 0.3, 0.2), 0.9)

    # ---- Ground: the bald hilltop, rock showing through, the track in from the east.
    reb.terrain("Ground", rough, (-26, 44), (-22, 36), height, step=0.5)
    kit.path_strip("Track", track_m, [(X1 + 14, 7.4), (X1, 7.0), (14.5, 6.6), (11.0, 6.0), (7.0, 6.2), (5.6, 7.0)], height, width=0.7, wobble=0.25, lift=0.01)
    rv, rf = [], []
    for (x, y, r) in ((14.6, 8.9, 0.6), (13.2, 9.3, 0.45), (15.3, 7.6, 0.4), (12.8, 7.8, 0.3), (2.0, 3.0, 0.8), (1.6, 10.6, 0.7), (18.2, 11.6, 0.6), (6.0, 11.4, 0.5), (11.0, 2.4, 0.45)):
        reb.boulder(rng, (x, y, height(x, y) - 0.05), r, rv, rf, squash=0.6)
    reb.mesh_object("Rocks", rv, rf, mat("rock"))
    for x, y, r in ((14.6, 8.9, 0.6), (13.2, 9.3, 0.45), (15.3, 7.6, 0.4), (6.0, 11.4, 0.5), (11.0, 2.4, 0.45), (18.2, 11.6, 0.6)):
        if X0 < x < X1 and Y0 < y < Y1:
            reb.wall(reb.prim("cube", "Rock footprint", None, (x, y, 0.3), (r * 2.0, r * 1.7, 0.6))).hide_render = True

    # ---- The tower: its frame (a mask), its footings, the cage round the stair's foot.
    bm, fbm = Beams(), Beams()
    tower(bm, timber, TC, 0.0, floor_bm=fbm)
    cab_shell(bm, timber, glass, TC, 0.0, roof_m=mat("tin"))
    frame = bm.build("Lookout tower")
    fbm.build("Lookout tower floors")
    # Only the legs' feet and the cage stand in front of her: masks of their own.
    for sx in (-1, 1):
        for sy in (-1, 1):
            a = Vector((TC[0] + sx * 4.0, TC[1] + sy * 4.0, -0.1))
            b = Vector((TC[0] + sx * tower_hw(5.0), TC[1] + sy * tower_hw(5.0), 5.0))
            reb.mask(kit.rod("Leg foot", timber, a, b, 0.185, 8))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = TC[0] + sx * 4.0, TC[1] + sy * 4.0
            reb.prim("cube", "Footing", mat("concrete"), (x, y, 0.15), (0.8, 0.8, 0.5))
            kit.rod("Anchor strap", mat("rust"), (x - 0.18, y, 0.4), (x - 0.18 + sx * -0.05, y, 0.9), 0.02, 4)
            reb.wall(reb.prim("cube", "Leg footprint", None, (x, y, 0.5), (0.8, 0.8, 1.0))).hide_render = True
    cx0, cx1, cy0, cy1 = CAGE
    for (xa, ya, xb, yb) in ((cx0, cy0, cx1, cy0), (cx0, cy1, cx1, cy1), (cx1, cy0, cx1, cy1)):
        reb.mask(reb.prim("cube", "Cage side", link_m, ((xa + xb) / 2, (ya + yb) / 2, 1.1), (max(0.03, xb - xa), max(0.03, yb - ya), 2.2)))
    reb.prim("cube", "Cage top", link_m, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 2.2), (cx1 - cx0, cy1 - cy0, 0.03))
    for x in (cx0, cx1):
        for y in (cy0, cy1):
            kit.rod("Cage post", mat("rust"), (x, y, 0), (x, y, 2.2), 0.03, 8)
    # The cage door stands open: Walt went up and never locked it behind him.
    reb.prim("cube", "Cage door", link_m, (cx0 - 0.44, cy0 + 0.2, 1.05), (0.03, cy1 - cy0 - 0.06, 2.0), rot=(0, 0, 1.2))
    kit.rod("Cage door frame", mat("rust"), (cx0 - 0.01, cy0 + 0.04, 0.05), (cx0 - 0.01, cy0 + 0.04, 2.05), 0.02, 6)
    kit.rod("Cage door frame", mat("rust"), (cx0 - 0.01, cy1 - 0.04, 0.05), (cx0 - 0.01, cy1 - 0.04, 2.05), 0.02, 6)
    reb.prim("cube", "Cage hasp", mat("steel"), (cx0 - 0.03, cy1 - 0.08, 1.05), (0.03, 0.12, 0.04))
    reb.prim("cube", "Cage padlock", mat("steel"), (cx0 - 0.05, cy1 - 0.1, 0.97), (0.035, 0.06, 0.08), rot=(0.4, 0, 0), bevel=0.01)
    reb.prim("cube", "Cage sign", mat("white paint"), (cx0 - 0.03, (cy0 + cy1) / 2 - 0.1, 1.55), (0.02, 0.5, 0.3))
    kit.text("Cage sign words", "NO ENTRY", mat("red paint"), (cx0 - 0.045, (cy0 + cy1) / 2 - 0.1, 1.6), size=0.08, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.text("Cage sign words 2", "LOOKOUT STAFF", mat("black"), (cx0 - 0.045, (cy0 + cy1) / 2 - 0.1, 1.47), size=0.05, rot=(math.pi / 2, 0, -math.pi / 2))
    cage = reb.wall(reb.prim("cube", "Cage footprint", None, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.5), (cx1 - cx0, cy1 - cy0, 1.0)))
    cage.hide_render = True
    stair_wall = reb.wall(reb.prim("cube", "Stair footprint", None, (TC[0] - 0.35, TC[1] + 0.55, 0.5), (1.9, FLIGHT_W, 1.0)))
    stair_wall.hide_render = True
    # The lookout's sign by the track.
    for dy in (-0.6, 0.6):
        kit.rod("Lookout sign post", mat("dark wood"), (18.6, 4.4 + dy, -0.2), (18.6, 4.4 + dy, 1.9), 0.05)
    reb.prim("cube", "Lookout sign", reb.mat_plain("Sign brown", (0.13, 0.07, 0.035), 0.7), (18.63, 4.4, 1.55), (0.05, 1.6, 0.6))
    kit.text("Lookout sign words", "ARKLAY FIRE LOOKOUT", reb.mat_plain("Sign letters", (0.7, 0.6, 0.35), 0.6), (18.67, 4.4, 1.68), size=0.12, rot=(math.pi / 2, 0, math.pi / 2))
    kit.text("Lookout sign words 2", "ELEV 1610  BUILT 1953", reb.mat_plain("Sign letters", (0.7, 0.6, 0.35), 0.6), (18.67, 4.4, 1.45), size=0.08, rot=(math.pi / 2, 0, math.pi / 2))
    reb.wall(reb.prim("cube", "Sign footprint", None, (18.6, 4.4, 0.5), (0.2, 1.4, 1.0))).hide_render = True

    # ---- Walt, crumpled on the rocks at the east foot, blood over the stones.
    walt = kit.body("Walt", (BODY[0], BODY[1], 0.02), 2.3, pose="front", top=mat("khaki"), legs=reb.mat_plain("Trousers", (0.12, 0.1, 0.07), 0.8), bloody=1.0, seed=7)
    walt.rotation_euler = (0.05, -0.06, 2.3)
    reb.wall(reb.prim("cube", "Body footprint", None, (BODY[0] - 0.4, BODY[1] + 0.3, 0.3), (1.6, 1.2, 0.6))).hide_render = True
    for i, (x, y, z, r) in enumerate(((14.6, 8.8, 0.36, 0.22), (13.25, 9.25, 0.27, 0.16), (15.3, 7.6, 0.24, 0.12))):
        kit.splat(f"Blood on the rock {i}", mat("old blood"), (x, y, z), r, seed=20 + i, lumps=0.5)
    kit.splat("Spatter", mat("old blood"), (14.0, 7.6, 0.003), 0.9, seed=24, stretch=(1.4, 0.6), lumps=0.8)
    reb.prim("cyl", "Walt's cap", mat("khaki"), (15.9, 9.4, 0.06), (0.3, 0.3, 0.1), rot=(0.3, 0.2, 0), segments=14)
    reb.prim("cube", "Lost boot", mat("rubber"), (12.4, 10.2, 0.07), (0.3, 0.12, 0.14), rot=(0.3, 0, 1.1), bevel=0.03)
    kit.splat("Broken rail splinters", reb.mat_plain("Splinters", (0.3, 0.22, 0.13), 0.9), (13.0, 7.0, 0.004), 0.3, seed=26, stretch=(2.0, 0.3), lumps=0.9)

    # ---- His bicycle by the track, a wheel turning; the privy; the hoist rope and its bucket.
    bike, wheel = bicycle("Bicycle", (16.0, 9.4, 0.0), 0.5)
    reb.wall(reb.prim("cube", "Bicycle footprint", None, (16.0, 9.4, 0.3), (1.6, 0.8, 0.6))).hide_render = True
    px, py = 2.0, 11.0
    for ob in kit.walls(px - 0.55, py - 0.55, px + 0.55, py + 0.55, 2.1, kit.boards("Privy boards", (0.22, 0.17, 0.11), width=0.14, grime=0.7), openings=[("e", py - 0.35, py + 0.35, 0.0, 1.9)], thick=0.05, name="Privy wall"):
        reb.wall(ob)
    reb.prim("cube", "Privy roof", mat("tin"), (px, py, 2.18), (1.4, 1.4, 0.05), rot=(0, 0.15, 0))
    phinge = reb.prim("sphere", "Privy hinge", mat("iron"), (px + 0.6, py - 0.35, 0.95), (0.02, 0.02, 0.02))
    reb.prim("cube", "Privy door", kit.boards("Privy door boards", (0.24, 0.18, 0.12), width=0.12, grime=0.6), (0.0, 0.35, 0.0), (0.04, 0.7, 1.9)).parent = phinge
    phinge.rotation_euler = (0, 0, -0.9)
    reb.prim("cube", "Privy dark", mat("black"), (px - 0.05, py, 1.0), (0.9, 0.9, 1.9))
    ppivot = reb.prim("sphere", "Hoist pulley", mat("iron"), (TC[0] + 4.4, TC[1] - 2.0, TOWER_DECK + 0.5), (0.18, 0.18, 0.18))
    kit.rod("Hoist davit", timber, (TC[0] + tower_hw(TOWER_DECK), TC[1] - 2.0, TOWER_DECK + 0.6), (TC[0] + 4.4, TC[1] - 2.0, TOWER_DECK + 0.6), 0.06, 6)
    kit.rod("Hoist rope", rope_m, (0, 0, 0), (0, 0, -TOWER_DECK + 0.6), 0.012, 6).parent = ppivot
    reb.prim("cyl", "Hoist bucket", mat("tin"), (0, 0, -TOWER_DECK + 0.4), (0.3, 0.3, 0.35), segments=14).parent = ppivot
    # Water barrel, firewood, a fire-danger board.
    kit.drum("Water barrel", mat("rust"), (11.4, 11.2, 0.0))
    reb.wall(reb.prim("cube", "Barrel footprint", None, (11.4, 11.2, 0.4), (0.6, 0.6, 0.8))).hide_render = True
    wood = [kit.rod("Split log", mat("logs"), (3.0 + rng.uniform(-0.1, 0.1), 8.0 + k * 0.22, 0.12 + (k % 2) * 0.2), (4.1 + rng.uniform(-0.1, 0.1), 8.0 + k * 0.22, 0.12 + (k % 2) * 0.2), 0.11, 7) for k in range(6)]
    reb.wall(kit.join("Woodpile", wood))
    reb.prim("cube", "Danger board", mat("white paint"), (15.2, 2.3, 1.3), (1.0, 0.04, 0.7))
    kit.text("Danger board words", "FIRE DANGER", mat("black"), (15.2, 2.33, 1.5), size=0.1, rot=(math.pi / 2, 0, math.pi))
    kit.text("Danger board words 2", "TODAY: HIGH", mat("red paint"), (15.2, 2.33, 1.3), size=0.12, rot=(math.pi / 2, 0, math.pi))
    for dx in (-0.45, 0.45):
        kit.rod("Danger board post", mat("dark wood"), (15.2 + dx, 2.27, -0.2), (15.2 + dx, 2.27, 1.7), 0.04, 6)

    # ---- The forest round the hilltop, the valley beyond it to the west.
    def keep_out(x, y):
        if X0 - 2.5 < x < X1 + 2.5 and Y0 - 2.5 < y < Y1 + 2.5:
            return True
        if x > X1 and 5.0 < y < 9.5:
            return True
        if x < X0 and -2.0 < y < 9.0 and rng.random() < 0.7:
            return True
        return any((Vector((x, y)) - Vector(c[:2])).length < 4.5 for c in CAMS)
    kit.forest(rng, height, keep_out, (-26, -22, 44, 36), count=95, spacing=2.0, ferns=30, needles=700, dead=0.15)
    kit.vista(rng, (-8.0, 6.0), (-1.0, 0.35), below=-70.0)

    def patchy(r):
        while True:
            x, y = r.uniform(X0 - 6, X1 + 6), r.uniform(Y0 - 6, Y1 + 6)
            if noise.noise(Vector((x * 0.3, y * 0.3, 2))) > -0.1 and not (CAGE[0] - 0.3 < x < CAGE[1] + 0.3 and CAGE[2] - 0.3 < y < CAGE[3] + 0.3):
                return x, y
    grass = kit.meadow(rng, 1600, patchy, height, mat("dead grass"))
    green = kit.meadow(rng, 900, patchy, height)

    # ---- Light: the low sun from the south-west, the tower's shadow across the hilltop.
    low_sun(232, 21, 6.0)
    motes = dust(rng, (X0, Y0, X1, Y1), 90)

    anim = kit.Anim(16)
    anim.custom(lambda k: setattr(ppivot, "rotation_euler", (math.radians(2.0) * math.sin(anim.phase(k)), math.radians(1.2) * math.cos(anim.phase(k)), 0)))
    anim.spin(wheel, axis=1, turns=1, symmetry=6)
    anim.flies((BODY[0] - 0.3, BODY[1] + 0.2, 0.2), count=10, radius=0.45)
    anim.sway(grass, amount=0.05)
    anim.sway(green, amount=0.05)
    anim.custom(lambda k: setattr(motes, "location", (0.25 * math.sin(anim.phase(k)), 0.1 * math.cos(anim.phase(k)), 0.06 * math.sin(anim.phase(k, 2)))))

    # ---- What the game needs.
    room.door("washout", (X1 - 0.6, 5.5, X1, 8.5), arrive=(17.3, 7.0), face=(-1, 0))
    room.door("tower-stairs", (cx0 - 0.6, cy0, cx0, cy1), arrive=(4.8, 7.05), face=(-1, 0), walk=False, touch=False)
    room.check((BODY[0] - 1.4, BODY[1] - 0.9, BODY[0] + 0.9, BODY[1] + 1.2), "A man in a ranger's shirt, smashed on the rocks.\nHe came off the top. Fell, or jumped.")
    room.check((cx0 - 0.6, cy0 - 0.4, cx0, cy0), "The stair's in a cage. The door's open, the padlock hanging off the hasp.\nHe went up and never locked it behind him.")
    room.check((15.4, 8.8, 16.8, 10.0), "A bicycle. Its front wheel is still turning in the wind.")
    room.check((17.9, 3.6, 18.5, 5.2), "ARKLAY FIRE LOOKOUT. ELEV 1610. BUILT 1953.")
    room.check((14.6, 2.0, 15.8, 2.8), "FIRE DANGER TODAY: HIGH.")
    room.check((px + 0.55, py - 0.5, px + 1.1, py + 0.5), "The privy. Nobody in it. Thank God.")
    room.export(anim)


build()
