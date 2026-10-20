"""The fire lookout tower's deck, 15 m up among its stairs, afternoon.

What it tells: the zig-zag flights climb inside the timber legs to this
deck, which runs right across the tower three metres under the cab. From
here the last flight goes up through the hatch. The old outside flight on
the west face tore off its top bolts long ago and hangs out over the drop,
swinging; a CLOSED board still hangs on it. Walt's handheld radio lies
smashed on the boards, dropped on his way up and trodden on; its battery
has burst out. Below, on the rocks at the tower's east
foot, he lies small and still. Crows wait on the north rail. The wind
comes through the boards and lifts a loose one.

Metres: the deck is x 2.13-7.87, y 2.13-7.87 (the tower's centre at 5, 5),
the ground 15 m below. The flight up from the 12 m landing comes through
the opening at x 4.5-6.5, y 5.1-6.0 and arrives at its east end; the last
flight up starts at the east end of x 3.5-6.5, y 4.0-4.9 and climbs west to
the hatch. The legs stand at the corners; the rail runs round the edge but
for a gap on the west at y 4.45-5.45 where the outside flight hung.

Moving: the broken flight swinging, a loose deck board lifting, a crow, the
tops of the spruces below.
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
from mathutils import Vector, noise  # noqa: E402

C = (5.0, 5.0)
GROUND = -15.0


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


HD = tower_hw(TOWER_DECK) + 0.2
X0, X1, Y0, Y1 = C[0] - HD, C[0] + HD, C[1] - HD, C[1] + HD
CAMS = [(C[0] - 0.4, C[1] + 2.15, 2.4), (C[0] + 2.0, C[1] - 2.1, 2.4), (C[0] - 2.15, C[1] - 1.9, 2.3)]


def height(x, y):
    """The hilltop 15 m below, falling away all round."""
    r = max(abs(x - C[0] - 3.0), abs(y - C[1] + 0.5))
    h = GROUND + 0.4 * noise.noise(Vector((x * 0.12, y * 0.12, 6)))
    if r > 10:
        h -= (r - 10) * 0.35
    return h


def low_sun(heading, elevation, energy, rgb=(1.0, 0.7, 0.42)):
    """The afternoon sun low in the south-west: long shadows, warm light."""
    sun = kit.time_light("afternoon", sun_heading=heading, sun_energy=energy,
                         mist=((5, 5, -6), (90, 90, 24), 0.004))
    sun.rotation_euler[0] = math.radians(90 - elevation)
    sun.data.color = rgb
    bpy.context.view_layer.update()
    kit._sky((0.86, 0.64, 0.44), (0.3, 0.38, 0.56), 0.8, sun)
    return sun


def P(x, y, z=0.0):
    return (C[0] + x, C[1] + y, z)


def build():
    rng = random.Random(67)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("boards")  # the deck
    room.camera(CAMS[0], P(-2.4, -1.1, -0.7), 200, "under the cab at the south rail, looking north: the deck, the broken flight over the drop, the valley west")
    room.camera(CAMS[1], P(-0.6, 2.1, -0.4), 200, "under the cab in the north-east corner, looking south-west: the smashed radio, the flights, Walt far below on the rocks")
    room.camera(CAMS[2], P(2.0, 1.6, 0.0), 200, "under the cab in the north-west corner, looking south-east: the crows on the north rail, the last flight up to the hatch")

    timber = reb.mat_wood("Tower timber", (0.15, 0.13, 0.11))
    glass = reb.mat_glass("Cab glass", (0.5, 0.55, 0.55))
    rough = reb.mat_surface("Hilltop", [(0.0, (0.07, 0.07, 0.04)), (0.45, (0.15, 0.15, 0.07)), (0.8, (0.22, 0.19, 0.12)), (1.0, (0.28, 0.27, 0.24))], scale=1.2, bump=0.6)

    # ---- The tower: its frame a mask, the deck a floor of its own.
    bm, fbm = Beams(), Beams()
    tower(bm, timber, C, GROUND, floor_bm=fbm)
    cab_shell(bm, timber, glass, C, GROUND, roof_m=mat("tin"))
    bm.build("Lookout tower")
    # What can stand in front of her up here: the legs and the last flight up.
    mbm = Beams()
    tower(mbm, timber, C, GROUND, below=16.0, above=16.0, flights=(5,), deck=False, cab=False)
    for ob in mbm.build("Tower masks"):
        reb.mask(ob)
    fbm.build("Lookout tower floors")
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = tower_hw(TOWER_DECK)
            reb.wall(reb.prim("cube", "Leg footprint", None, P(sx * h, sy * h, 0.5), (0.45, 0.45, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "Last flight footprint", None, P(-0.15, -0.55, 0.5), (2.7, FLIGHT_W + 0.1, 1.0))).hide_render = True
    # A loose deck board, lifting in the wind at its north end.
    lpivot = reb.prim("cube", "Loose board nail", mat("iron"), P(-1.9, 2.4, 0.005), (0.02, 0.02, 0.01))
    reb.prim("cube", "Loose board", timber, (0.0, -0.75, 0.02), (0.16, 1.5, 0.03)).parent = lpivot
    kit.splat("Gap under the board", mat("black"), P(-1.9, 1.6, 0.004), 0.12, seed=3, stretch=(0.6, 4.0), lumps=0.1)

    # ---- The outside flight, torn off at the top, hanging out over the drop.
    bpivot = reb.prim("sphere", "Broken flight bolt", mat("rust"), P(-HD - 0.05, -0.05, -0.05), (0.06, 0.06, 0.06))
    parts = []
    L = 3.6
    for dy in (-0.45, 0.45):
        parts.append(kit.rod("Stringer", timber, (0, dy, 0), (-L, dy, 0), 0.07, 4))
        parts.append(kit.rod("Handrail", timber, (-0.2, dy, 0.9), (-L, dy, 0.9), 0.035, 4))
        for t in (0.1, 0.55, 0.95):
            parts.append(kit.rod("Rail post", timber, (-L * t, dy, 0), (-L * t, dy, 0.9), 0.035, 4))
    for k in range(1, 11):
        parts.append(reb.prim("cube", "Tread", timber, (-L * k / 11, 0, 0.03), (0.24, 0.9, 0.04)))
    parts.append(reb.prim("cube", "Missing tread splinter", timber, (-L * 0.62, 0.3, -0.03), (0.2, 0.25, 0.03), rot=(0.4, 0, 0.3)))
    flight = kit.join("Broken flight", parts)
    flight.parent = bpivot
    board = reb.prim("cube", "Closed board", mat("white paint"), (-0.9, -0.47, 0.6), (0.6, 0.02, 0.3))
    board.parent = bpivot
    kit.text("Closed words", "CLOSED", mat("red paint"), (-0.9, -0.485, 0.6), size=0.12).parent = bpivot
    bpivot.rotation_euler = (0, math.radians(-62), math.radians(8))
    for dy in (-0.45, 0.45):
        reb.prim("cube", "Torn bolt plate", mat("rust"), P(-HD + 0.02, dy, -0.1), (0.04, 0.12, 0.2))
        kit.rod("Sheared bolt", mat("rust"), P(-HD - 0.02, dy, 0.0), P(-HD - 0.12, dy + 0.03, 0.05), 0.012, 6)
    reb.prim("cube", "Chain across the gap", mat("iron"), P(-HD + 0.02, -0.05, 0.75), (0.02, 0.95, 0.02), rot=(0.12, 0, 0))

    # ---- Walt's radio, smashed where it landed; his things below.
    radio = kit.join("Smashed radio", [
        reb.prim("cube", "body", reb.mat_plain("Radio black", (0.03, 0.03, 0.03), 0.5), (0, 0, 0.04), (0.08, 0.2, 0.06), bevel=0.01),
        reb.prim("cube", "face", mat("steel"), (0, 0.03, 0.075), (0.06, 0.08, 0.005)),
    ])
    radio.location = P(-0.9, -1.5, 0.0)
    radio.rotation_euler = (0, 0, 0.8)
    kit.rod("Snapped aerial", mat("black"), P(-0.75, -1.3, 0.02), P(-0.4, -1.1, 0.02), 0.008, 5)
    reb.prim("cube", "Burst battery", reb.mat_plain("Battery", (0.5, 0.35, 0.05), 0.5), P(-1.5, -1.9, 0.02), (0.08, 0.05, 0.03), rot=(0, 0, 2.2))
    kit.shards("Radio splinters", P(-1.0, -1.6, 0.0), spread=0.4, count=8, seed=4, m=mat("black"))
    kit.splat("Scuff where it hit", reb.mat_plain("Scuff", (0.32, 0.25, 0.16), 0.9), P(-0.9, -1.55, 0.003), 0.16, seed=5, lumps=0.6)
    # A water can on the deck, a coil of rope, a jacket snagged on the south rail and flapping.
    reb.prim("cyl", "Water can", mat("tin"), P(-1.9, -2.2, 0.2), (0.3, 0.3, 0.4), segments=14)
    reb.wall(reb.prim("cube", "Water can footprint", None, P(-1.9, -2.2, 0.3), (0.4, 0.4, 0.6))).hide_render = True
    coil = [kit.rod("Rope", reb.mat_plain("Rope", (0.35, 0.3, 0.2), 0.9), P(1.8 + 0.25 * math.cos(a), -2.1 + 0.25 * math.sin(a), 0.03 + 0.02 * k), P(1.8 + 0.25 * math.cos(a + 0.8), -2.1 + 0.25 * math.sin(a + 0.8), 0.03 + 0.02 * k), 0.015, 5) for k in range(3) for a in [i * 0.8 for i in range(8)]]
    kit.join("Rope coil", coil)
    # The hoist davit on the east side, its rope down to the bucket on the ground.
    kit.rod("Hoist davit", timber, P(tower_hw(TOWER_DECK), -2.0, 0.6), P(4.4, -2.0, 0.6), 0.06, 6)
    reb.prim("sphere", "Hoist pulley", mat("iron"), P(4.4, -2.0, 0.5), (0.18, 0.18, 0.18))
    kit.rod("Hoist rope", reb.mat_plain("Rope", (0.35, 0.3, 0.2), 0.9), P(4.4, -2.0, 0.5), P(4.4, -2.0, GROUND + 0.6), 0.012, 6)
    jpivot = reb.prim("sphere", "Snag", mat("iron"), P(0.8, HD, 1.05), (0.02, 0.02, 0.02))
    reb.cloth("Snagged jacket", reb.mat_plain("Jacket", (0.25, 0.22, 0.12), 0.85), (0.0, 0.18, -0.25), (0.4, 0.5), rot=(math.pi / 2 - 0.2, 0, 0), lumps=0.05, seed=6).parent = jpivot
    # Crows along the north rail.
    crows = []
    for i, (x, hd) in enumerate(((-1.6, 1.4), (-0.6, 1.8), (1.2, 4.4))):
        b, w = kit.crow(f"Crow on the rail {i}", P(x, -HD, 1.09), heading=hd)
        crows.append((b, w))
    flier, wings = kit.crow("Crow taking off", P(2.4, -HD - 0.6, 1.6), heading=0.6, perched=False)
    kit.splat("Droppings", mat("white paint"), P(-1.1, -HD + 0.15, 0.003), 0.08, seed=8, lumps=0.8)

    # ---- Below: the hilltop, Walt on the rocks, the bicycle, the forest; the valley beyond.
    reb.terrain("Ground", rough, (C[0] - 40, C[0] + 50), (C[1] - 40, C[1] + 45), height, step=0.8)
    gz = GROUND
    kit.path_strip("Track", reb.mat_surface("Track dirt", [(0.0, (0.09, 0.07, 0.045)), (1.0, (0.17, 0.13, 0.09))], scale=6, bump=0.6), [(C[0] + 25, C[1] + 0.8), (C[0] + 10, C[1] + 0.5), (C[0] + 2.0, C[1] - 0.5), (C[0] - 3.4, C[1] + 0.5)], height, width=0.7)
    kit.body("Walt far below", (C[0] + 4.7, C[1] + 1.7, gz + 0.05), heading=2.3, pose="front", top=mat("khaki"), bloody=1.2, seed=7)
    rv, rf = [], []
    for (x, y, r) in ((5.6, 2.4, 0.6), (4.2, 2.8, 0.45), (6.3, 1.1, 0.4), (8.6, -3.9, 0.9), (9.2, 5.1, 0.6)):
        reb.boulder(rng, P(x, y, gz), r, rv, rf, squash=0.6)
    reb.mesh_object("Rocks below", rv, rf, mat("rock"))
    for x, y in ((5.4, 2.3), (4.3, 2.6)):
        kit.splat("Blood on the rocks below", mat("blood"), P(x, y, gz + 0.35), 0.3, seed=int(x * 10))
    reb.prim("cube", "Bicycle below", reb.mat_plain("Bicycle green", (0.05, 0.14, 0.08), 0.4), P(7.0, 2.9, gz + 0.05), (1.6, 0.1, 0.06), rot=(0, 0, 0.5))
    reb.prim("cube", "Privy below", kit.boards("Privy boards", (0.22, 0.17, 0.11), width=0.14, grime=0.7), P(8.0, -3.5, gz + 1.05), (1.1, 1.1, 2.1))
    reb.prim("cube", "Cage below", reb.mat_surface("Chain link", [(0.0, (0.18, 0.18, 0.17)), (1.0, (0.3, 0.3, 0.28))], scale=60, rough=0.5, bump=0.8), P(-2.0, 0.55, gz + 1.1), (1.4, 1.0, 2.2))

    def keep_out(x, y):
        return max(abs(x - C[0] - 3.0), abs(y - C[1] + 0.5)) < 11.5
    kit.forest(rng, height, keep_out, (C[0] - 40, C[1] - 40, C[0] + 50, C[1] + 45), count=120, spacing=2.0, tall=(13, 20), ferns=20, needles=500, dead=0.12)
    grass = kit.meadow(rng, 900, lambda r: (r.uniform(C[0] - 8, C[0] + 14), r.uniform(C[1] - 11, C[1] + 10)), height, mat("dead grass"))
    kit.vista(rng, (C[0] - 20, C[1]), (-1.0, 0.3), below=-80.0)
    kit.vista(rng, (C[0] + 20, C[1]), (1.0, -0.2), below=-90.0, ridges=2)

    # ---- Light: the low sun from the south-west through the frame.
    low_sun(232, 21, 6.0)

    anim = kit.Anim(16)
    anim.custom(lambda k: setattr(bpivot, "rotation_euler", (math.radians(3) * math.sin(anim.phase(k)), math.radians(-62) + math.radians(2.5) * math.cos(anim.phase(k)), math.radians(8) + math.radians(4) * math.sin(anim.phase(k)))))
    anim.custom(lambda k: setattr(lpivot, "rotation_euler", (math.radians(6) * max(0.0, math.sin(anim.phase(k, 2))), 0, 0)))
    anim.custom(lambda k: setattr(jpivot, "rotation_euler", (math.radians(18) * math.sin(anim.phase(k)), math.radians(6) * math.sin(anim.phase(k, 2)), 0)))
    anim.bob(crows[1][0], height=0.04, speed=2)
    anim.flap(wings, degrees=55)
    anim.custom(lambda k: setattr(flier, "location", Vector(P(2.4, -HD - 0.6, 1.6)) + Vector((0.6 * k / 16, -1.2 * k / 16, 0.5 * math.sin(math.pi * k / 16)))))
    anim.sway(grass, amount=0.05)

    # ---- What the game needs.
    room.void((C[0] - 0.5, C[1] + 0.1, C[0] + FLIGHT_X, C[1] + 1.0))
    room.door("tower-foot", (C[0] + FLIGHT_X, C[1] + 0.1, C[0] + FLIGHT_X + 0.7, C[1] + 1.0), arrive=(C[0] + 2.2, C[1] + 1.9), face=(0, 1), walk=False, touch=False)
    room.door("tower-top", (C[0] + FLIGHT_X, C[1] - 1.0, C[0] + FLIGHT_X + 0.7, C[1] - 0.1), arrive=(C[0] + 2.2, C[1] - 1.9), face=(0, -1), walk=False, touch=False)
    room.check((C[0] - 1.6, C[1] - 2.3, C[0] - 0.3, C[1] - 1.1), "A handheld radio, smashed to bits. Dropped on the way up, and stamped on.\nThe battery's burst out of it.")
    room.check((X0, C[1] - 0.6, X0 + 0.7, C[1] + 0.5), "The outside stair. It's torn off at the top and hanging over the drop.\nCLOSED. No kidding.")
    room.check((X1 - 0.7, C[1] + 1.0, X1, C[1] + 2.6), "Down on the rocks at the foot, a man lying very still.\nThat's a long way down.")
    room.check((X0, Y0, X1, Y0 + 0.6), "Crows on the rail. They don't fly off. They're waiting.")
    room.export(anim)


build()
