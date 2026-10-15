"""The fire lookout tower's cab and catwalk, 18 m up, afternoon.

What it tells: this was Walt's summer: a glass box on stilts, an Osborne
fire finder in the middle, a cot, a stool with glass feet for the
lightning, tins and a water jug on the shelf. At 01.20 he saw smoke to the
north-east, in the valley, and wrote it in the log: SMOKE SIGHTED, NE, BRG
047, 01.20, AIRCRAFT? He radioed it in and got nothing back. Through the
night the log falls apart: dogs circling the tower at three, then that he
is burning up, scratching, that he can hear them on the stairs. Before
dawn he went out of the door and over the east rail: the top rail is
broken there, and there is blood on the post. From here you can still see
the smoke rising where Bravo's helicopter came down, and far off down the
valley the roof of a big house among the trees. The switch house key hangs
on its nail by the door, with its tag.

Metres: the cab floor is z 0, the ground 18 m below. The tower's centre is
at x 6, y 6. The cab is x 3.7-8.3, y 3.7-8.3; its door is in the south
wall at x 6.3-7.1. The catwalk runs round it to x 2.7-9.3, y 2.7-9.3. The
hatch is in the cab floor at x 4.35-6.45, y 5.0-5.9, where the last flight
comes up from the deck below. The fire finder stands at x 6.8, y 6.8; the
cot is along the east wall; the desk along the north wall.

Moving: the smoke column climbing out of the valley, the hatch's rope pull
swinging, a page of the log lifting, a crow on the catwalk rail.
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

C = (6.0, 6.0)
GROUND = -18.0


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


X0, X1, Y0, Y1 = C[0] - CATWALK, C[0] + CATWALK, C[1] - CATWALK, C[1] + CATWALK
CW = tower_hw(TOWER_CAB) - 0.1          # the cab wall, from the centre
DOOR = (0.3, 1.1)
SMOKE_DIR = Vector((0.72, -0.69, 0.0)).normalized()
MANSION_DIR = Vector((0.95, 0.3, 0.0)).normalized()
CAMS = [(C[0] - 2.05, C[1] - 2.05, 2.15), (C[0] + 2.05, C[1] + 2.05, 2.15), (C[0] - 4.6, C[1] + 4.4, 2.3), (C[0] - 4.2, C[1] - 3.9, 2.3)]


def P(x, y, z=0.0):
    return (C[0] + x, C[1] + y, z)


def height(x, y):
    r = max(abs(x - C[0] - 3.0), abs(y - C[1] + 0.5))
    h = GROUND + 0.4 * noise.noise(Vector((x * 0.12, y * 0.12, 6)))
    if r > 10:
        h -= (r - 10) * 0.35
    return h


def low_sun(heading, elevation, energy, rgb=(1.0, 0.7, 0.42)):
    """The afternoon sun low in the south-west: long shadows, warm light."""
    sun = kit.time_light("afternoon", sun_heading=heading, sun_energy=energy,
                         mist=((6, 6, -20), (700, 700, 140), 0.0012))
    sun.rotation_euler[0] = math.radians(90 - elevation)
    sun.data.color = rgb
    bpy.context.view_layer.update()
    kit._sky((0.86, 0.64, 0.44), (0.3, 0.38, 0.56), 0.8, sun)
    return sun


def smoke_column(base, puffs=14, rise=150.0, lean=Vector((40.0, 10.0, 0.0))):
    """Smoke climbing out of the trees: puffs that rise and swell and loop.
    Returns the pose function for Anim.custom."""
    m, nodes, links, bsdf = reb.nodes_material("Smoke")
    bsdf.inputs["Base Color"].default_value = (0.16, 0.15, 0.14, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, 0.08, 4, 0.6)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.3, (0.35, 0.35, 0.35)), (0.7, (0.75, 0.75, 0.75))])
    links.new(r.outputs["Color"], mix.inputs["Fac"])
    links.new(clear.outputs["BSDF"], mix.inputs[1])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["Material Output"].inputs["Surface"])
    jr = random.Random(12)
    jit = [Vector((jr.uniform(-1, 1), jr.uniform(-1, 1), jr.uniform(-0.3, 0.3))) for _ in range(puffs)]
    obs = []
    for i in range(puffs):
        ob = reb.prim("sphere", f"Smoke puff {i}", m, base, (1, 1, 1), segments=12)
        ob.visible_shadow = False
        obs.append(ob)
    glow = reb.prim("sphere", "Fire glow", reb.mat_emit("Embers", (1.0, 0.35, 0.08), 6), base, (14, 14, 5), segments=10)
    glow.visible_shadow = False

    def pose(k, frames=16):
        for i, ob in enumerate(obs):
            u = ((i + k / frames) / puffs) % 1.0
            ob.location = Vector(base) + lean * (u ** 1.6) + Vector((0, 0, rise * u)) + jit[i] * (3 + 14 * u)
            s = 9 + 34 * u
            ob.scale = (s, s * 0.9, s * 0.8)
    pose(0)
    return pose


def mansion(at, facing):
    """The Spencer mansion far down the valley: a dark block with a hip roof,
    two wings, chimneys, a small tower: a silhouette among the trees."""
    stone = reb.mat_plain("Mansion stone", (0.09, 0.085, 0.08), 0.9)
    roof = reb.mat_plain("Mansion roof", (0.05, 0.055, 0.06), 0.6)
    lit = reb.mat_emit("Mansion window", (1.0, 0.7, 0.4), 1.5)
    parts = []
    def block(cx, cy, w, d, h, roof_h):
        parts.append(reb.prim("cube", "block", stone, (cx, cy, h / 2), (w, d, h)))
        v = [(cx - w / 2 - 1, cy - d / 2 - 1, h), (cx + w / 2 + 1, cy - d / 2 - 1, h), (cx + w / 2 + 1, cy + d / 2 + 1, h), (cx - w / 2 - 1, cy + d / 2 + 1, h), (cx - w / 4, cy, h + roof_h), (cx + w / 4, cy, h + roof_h)]
        parts.append(reb.mesh_object("roof", v, [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)], roof, smooth=False))
    block(0, 0, 44, 16, 14, 8)
    block(-30, 6, 18, 26, 11, 6)
    block(30, 6, 18, 26, 11, 6)
    parts.append(reb.prim("cube", "tower", stone, (8, -4, 12), (7, 7, 24)))
    parts.append(reb.prim("cone", "spire", roof, (8, -4, 27), (9, 9, 7), segments=4, rot=(0, 0, math.pi / 4)))
    for x in (-14, -4, 14, -32, 32):
        parts.append(reb.prim("cube", "chimney", stone, (x, 2, 22), (2, 2, 8)))
    for x in (-12, 2, 18):
        parts.append(reb.prim("cube", "window", lit, (x, -8.1, 8), (2.2, 0.3, 3.0)))
    ob = kit.join("Spencer mansion", parts)
    ob.location = Vector(at) + Vector((0, 0, 7))
    ob.rotation_euler = (0, 0, facing)
    return ob


def flat_join(name, parts):
    """kit.join, with each part's own turn and place baked into its mesh
    first, so the joined object sits at the origin unturned and can be
    placed and turned as a whole."""
    for p in parts:
        p.data.transform(p.matrix_basis)
        p.matrix_basis = Matrix.Identity(4)
    return kit.join(name, parts)


def build():
    rng = random.Random(71)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera(CAMS[0], P(1.5, 1.6, 0.5), 200, "inside, high in the north-west corner: the fire finder, the cot, the door, the valley through the glass")
    room.camera(CAMS[1], P(-1.4, -1.4, 0.4), 200, "inside, high in the south-east corner: the hatch, the desk and the log, the west windows")
    room.camera(CAMS[2], P(3.5, 1.8, -1.0), 200, "out past the south-west corner: the catwalk to the open door, the broken east rail")
    room.camera(CAMS[3], P(8.0, -7.0, -2.8), 200, "out past the north-west corner, along the north catwalk: the smoke in the valley, the mansion far off")

    timber = reb.mat_wood("Tower timber", (0.15, 0.13, 0.11))
    glass = reb.mat_glass("Cab glass", (0.6, 0.64, 0.62))
    rough = reb.mat_surface("Hilltop", [(0.0, (0.07, 0.07, 0.04)), (0.45, (0.15, 0.15, 0.07)), (0.8, (0.22, 0.19, 0.12)), (1.0, (0.28, 0.27, 0.24))], scale=1.2, bump=0.6)
    lino = reb.mat_surface("Cab floor", [(0.0, (0.12, 0.09, 0.06)), (0.6, (0.22, 0.17, 0.11)), (1.0, (0.16, 0.12, 0.08))], scale=5, rough=0.6, bump=0.2)
    brass = reb.mat_metal("Brass", (0.45, 0.33, 0.12), 0.3)
    mapm = reb.mat_surface("Map", [(0.0, (0.55, 0.52, 0.4)), (0.6, (0.42, 0.48, 0.32)), (1.0, (0.6, 0.57, 0.46))], scale=12, bump=0.05)

    # ---- The tower: frame and cab a mask; the cab floor and catwalk a floor; the hatch.
    bm, fbm = Beams(), Beams()
    tower(bm, timber, C, GROUND, floor_bm=fbm)
    roof = cab_shell(bm, timber, glass, C, GROUND, door=DOOR, roof_m=mat("tin"))
    for ob in bm.build("Lookout tower"):
        if ob.data.materials[0] is timber:
            reb.mask(ob)
    fbm.build("Lookout tower floors")
    hx0, hy0, hx1, hy1 = HATCH
    reb.prim("cube", "Cab lino", lino, P((-CW + CW) / 2, (hy0 - CW) / 2, 0.002), (2 * CW, hy0 + CW, 0.004))
    reb.prim("cube", "Cab lino", lino, P(0.0, (hy1 + CW) / 2, 0.002), (2 * CW, CW - hy1, 0.004))
    reb.prim("cube", "Cab lino", lino, P((-CW + hx0) / 2, (hy0 + hy1) / 2, 0.002), (hx0 + CW, hy1 - hy0, 0.004))
    reb.prim("cube", "Cab lino", lino, P((hx1 + CW) / 2, (hy0 + hy1) / 2, 0.002), (CW - hx1, hy1 - hy0, 0.004))
    reb.prim("cube", "Ceiling boards", kit.boards("Cab ceiling", (0.2, 0.15, 0.1), width=0.12), P(0, 0, 2.47), (2 * CW, 2 * CW, 0.04))
    # The hatch lid, propped open against its stop; a guard rail; the rope pull.
    lid_pivot = reb.prim("cube", "Hatch hinge", mat("iron"), P(hx0 + (hx1 - hx0) / 2, hy0, 0.02), (hx1 - hx0, 0.03, 0.03))
    reb.prim("cube", "Hatch lid", timber, (0.0, 0.0, 0.45), (hx1 - hx0, 0.05, 0.9)).parent = lid_pivot
    lid_pivot.rotation_euler = (math.pi / 2 - 0.06, 0, 0)
    for xa, ya, xb, yb in ((hx1, hy0, hx1, hy1), (hx0 + 0.6, hy1, hx1, hy1)):
        kit.rod("Hatch rail", timber, P(xa, ya, 0.95), P(xb, yb, 0.95), 0.03, 6)
        kit.rod("Hatch rail post", timber, P(xb, yb, 0.0), P(xb, yb, 0.95), 0.03, 6)
    rpivot = reb.prim("sphere", "Pull hook", mat("iron"), P(hx0 + 0.4, hy0 + 0.05, 2.4), (0.03, 0.03, 0.03))
    kit.rod("Rope pull", reb.mat_plain("Rope", (0.35, 0.3, 0.2), 0.9), (0, 0, 0), (0, 0, -0.9), 0.012, 6).parent = rpivot
    reb.prim("sphere", "Pull knot", reb.mat_plain("Rope", (0.35, 0.3, 0.2), 0.9), (0, 0, -0.92), (0.05, 0.05, 0.06), segments=8).parent = rpivot
    # Collision: the cab's walls with the door gap, the hatch's rail.
    for (x, y, sx, sy) in ((0.0, -CW, 2 * CW, 0.12), (-CW, 0.0, 0.12, 2 * CW), (CW, 0.0, 0.12, 2 * CW), ((-CW + DOOR[0]) / 2, CW, DOOR[0] + CW, 0.12), ((DOOR[1] + CW) / 2, CW, CW - DOOR[1], 0.12)):
        reb.wall(reb.prim("cube", "Cab wall footprint", None, P(x, y, 0.5), (sx, sy, 1.0))).hide_render = True
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = tower_hw(TOWER_CAB)
            reb.wall(reb.prim("cube", "Leg footprint", None, P(sx * h, sy * h, 0.5), (0.4, 0.4, 1.0))).hide_render = True

    # ---- The Osborne fire finder on its pedestal; the glass-footed stool.
    fx, fy = 0.8, 0.8
    reb.prim("cyl", "Finder pedestal", timber, P(fx, fy, 0.5), (0.35, 0.35, 1.0), segments=12)
    reb.mask(reb.prim("cyl", "Finder table", timber, P(fx, fy, 1.03), (0.95, 0.95, 0.06), segments=24))
    reb.prim("cyl", "Finder map", mapm, P(fx, fy, 1.07), (0.78, 0.78, 0.01), segments=24)
    reb.prim("cyl", "Finder ring", brass, P(fx, fy, 1.09), (0.84, 0.84, 0.03), segments=32)
    for i in range(12):
        a = 2 * math.pi * i / 12
        reb.prim("cube", f"Bearing tick {i}", mat("black"), P(fx + 0.42 * math.cos(a), fy + 0.42 * math.sin(a), 1.105), (0.03, 0.006, 0.004), rot=(0, 0, a))
    sa = math.atan2(SMOKE_DIR.y, SMOKE_DIR.x)
    for d in (-1, 1):
        reb.prim("cube", "Sight", brass, P(fx + d * 0.42 * math.cos(sa), fy + d * 0.42 * math.sin(sa), 1.2), (0.02, 0.06, 0.2), rot=(0, 0, sa))
    kit.rod("Sight hair", mat("black"), P(fx + 0.42 * math.cos(sa), fy + 0.42 * math.sin(sa), 1.28), P(fx - 0.42 * math.cos(sa), fy - 0.42 * math.sin(sa), 1.28), 0.002, 4)
    reb.wall(reb.prim("cube", "Finder footprint", None, P(fx, fy, 0.5), (0.95, 0.95, 1.0))).hide_render = True
    stool = [reb.prim("cube", "seat", timber, (0, 0, 0.62), (0.36, 0.36, 0.04))]
    for dx in (-0.14, 0.14):
        for dy in (-0.14, 0.14):
            stool.append(reb.prim("cube", "leg", timber, (dx, dy, 0.38), (0.04, 0.04, 0.46)))
            stool.append(reb.prim("cyl", "insulator", mat("glass"), (dx, dy, 0.07), (0.1, 0.1, 0.14), segments=10))
    st = flat_join("Lightning stool", stool)
    st.location = P(-0.1, 1.6, 0.0)
    st.rotation_euler = (0, 0, 0.3)

    # ---- The desk along the north wall: the log, the binoculars, the dead radio, a lamp.
    desk = kit.table("Desk", reb.mat_wood("Desk", (0.2, 0.14, 0.08)), P(1.0, -CW + 0.3, 0.0), size=(2.2, 0.55, 0.85))
    reb.wall(desk)
    # The switch house key, on the desk by the log (switch-key).
    room.item("switch-key", P(0.5, -CW + 0.3, 0.86))
    reb.prim("cube", "Logbook", mat("paper"), P(0.7, -CW + 0.32, 0.855), (0.42, 0.3, 0.012), rot=(0, 0, 0.08))
    reb.prim("cube", "Logbook cover", reb.mat_plain("Ledger green", (0.06, 0.12, 0.08), 0.6), P(0.7, -CW + 0.32, 0.848), (0.44, 0.32, 0.006), rot=(0, 0, 0.08))
    for i in range(6):
        reb.prim("cube", f"Log line {i}", mat("black"), P(0.62, -CW + 0.22 + i * 0.035, 0.862), (0.22 - 0.02 * (i % 3), 0.006, 0.001), rot=(0, 0, 0.08))
    page_pivot = reb.prim("cube", "Page spine", mat("paper"), P(0.92, -CW + 0.32, 0.862), (0.005, 0.28, 0.005))
    reb.prim("cube", "Lifting page", mat("paper"), (-0.1, 0.0, 0.0), (0.2, 0.28, 0.002)).parent = page_pivot
    kit.rod("Pencil", mat("yellow paint"), P(0.3, -CW + 0.45, 0.865), P(0.45, -CW + 0.5, 0.865), 0.006, 6)
    bino = flat_join("Binoculars", [kit.rod("barrel", mat("black"), (0, -0.04, 0), (0.17, -0.04, 0), 0.04, 10), kit.rod("barrel", mat("black"), (0, 0.04, 0), (0.17, 0.04, 0), 0.04, 10)])
    bino.location = P(1.35, -CW + 0.3, 0.9)
    bino.rotation_euler = (0, 0, 2.6)
    reb.prim("cube", "Radio set", reb.mat_plain("Radio grey", (0.15, 0.16, 0.15), 0.5), P(1.85, -CW + 0.25, 1.0), (0.45, 0.3, 0.3), bevel=0.01)
    reb.prim("cube", "Radio dial", mat("black"), P(1.85, -CW + 0.4, 1.02), (0.3, 0.005, 0.1))
    kit.rod("Handset cord", mat("black"), P(1.65, -CW + 0.42, 0.95), P(1.4, -CW + 0.6, 0.02), 0.006, 5)
    reb.prim("cube", "Handset", mat("black"), P(1.3, -CW + 0.75, 0.03), (0.2, 0.06, 0.05), rot=(0, 0, 0.7))
    lamp, lamp_light, flame = kit.lantern("Lantern", P(-0.1, -CW + 0.3, 0.85), energy=0.0)
    kit.splat("Blood on the desk", mat("old blood"), P(0.2, -CW + 0.35, 0.858), 0.05, seed=4, lumps=0.6)
    # The shelf on the west wall: tins, a water jug, a first aid tin raided.
    shelf = reb.prim("cube", "Shelf", timber, P(-CW + 0.15, 1.2, 0.9), (0.3, 1.6, 0.03))
    for i in range(7):
        y = 0.55 + i * 0.2
        reb.prim("cyl", f"Tin {i}", mat("steel") if i % 3 else mat("rust"), P(-CW + 0.15, y, 0.97), (0.09, 0.09, 0.12), segments=10)
    reb.prim("cyl", "Water jug", reb.mat_glass("Jug glass", (0.6, 0.65, 0.6)), P(-CW + 0.15, 2.0, 1.04), (0.16, 0.16, 0.26), segments=12)
    for i in range(4):
        reb.prim("cyl", f"Empty tin {i}", mat("steel"), P(-1.2 + rng.uniform(-0.4, 0.4), 1.7 + rng.uniform(-0.3, 0.3), 0.05), (0.09, 0.09, 0.12), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=10)
    # The cot along the east wall, the blanket clawed off it; scratches on the wall.
    cot = kit.join("Cot", [
        kit.rod("rail", mat("iron"), (CW - 0.7, -1.6, 0.42), (CW - 0.7, 0.3, 0.42), 0.02),
        kit.rod("rail", mat("iron"), (CW - 0.1, -1.6, 0.42), (CW - 0.1, 0.3, 0.42), 0.02),
        reb.prim("cube", "canvas", mat("canvas"), (CW - 0.4, -0.65, 0.42), (0.6, 1.9, 0.02)),
    ] + [kit.rod("leg", mat("iron"), (CW - 0.7 + 0.6 * a, y0, 0.0), (CW - 0.1 - 0.6 * a, y0 + 0.2, 0.42), 0.015) for a in (0, 1) for y0 in (-1.6, 0.1)])
    cot.location += Vector((C[0], C[1], 0.0))
    reb.wall(reb.prim("cube", "Cot footprint", None, P(CW - 0.4, -0.65, 0.3), (0.65, 1.9, 0.6))).hide_render = True
    reb.cloth("Blanket on the floor", reb.mat_stripes("Grey blanket", [(0.12, 0.12, 0.11), (0.2, 0.2, 0.18), (0.3, 0.06, 0.04)], across=8, axis="Y"), P(CW - 1.1, -0.9, 0.04), (0.9, 1.1), rot=(0, 0, 0.5), lumps=0.06, seed=3)
    kit.splat("Blood on the canvas", mat("old blood"), P(CW - 0.4, -0.2, 0.435), 0.2, seed=5, stretch=(1.0, 1.4))
    for k in range(3):
        kit.scratches(f"Scratches {k}", mat("old blood"), P(CW - 0.06, -1.2 + k * 0.5, 0.9), (-1, 0), count=4, length=0.35, seed=k)
    # The switch house key on its nail by the door, its tag.
    kx = DOOR[1] + 0.3
    reb.prim("cyl", "Nail", mat("iron"), P(kx, CW - 0.07, 1.55), (0.01, 0.01, 0.06), rot=(math.pi / 2, 0, 0), segments=6)
    reb.prim("cube", "Key", brass, P(kx, CW - 0.09, 1.47), (0.025, 0.006, 0.09))
    reb.prim("cube", "Key tag", reb.mat_plain("Tag red", (0.4, 0.05, 0.03), 0.7), P(kx + 0.02, CW - 0.09, 1.38), (0.06, 0.004, 0.09))
    reb.prim("cube", "Wall board under the key", timber, P(kx, CW - 0.055, 1.45), (0.4, 0.01, 0.3))
    kit.text("Key board words", "KEYS", mat("white paint"), P(kx, CW - 0.062, 1.56), size=0.04)
    # The door, standing open onto the catwalk.
    dpivot = reb.prim("sphere", "Door hinge", mat("iron"), P(DOOR[1], CW, 1.05), (0.02, 0.02, 0.02))
    reb.prim("cube", "Cab door", timber, (-0.4, 0.0, 0.0), (0.8, 0.05, 2.05)).parent = dpivot
    reb.prim("cube", "Door glass", glass, (-0.4, 0.0, 0.45), (0.5, 0.055, 0.7)).parent = dpivot
    dpivot.rotation_euler = (0, 0, -(math.pi - 0.12))

    # ---- The catwalk: the broken east rail and the blood where he went over; a crow.
    bx = CATWALK
    g0, g1 = BROKEN_RAIL
    kit.rod("Splintered rail end", timber, P(bx, g0, 1.05), P(bx + 0.12, g0 + 0.3, 0.9), 0.035, 5)
    kit.rod("Splintered rail end", timber, P(bx, g1, 1.05), P(bx + 0.1, g1 - 0.25, 0.85), 0.035, 5)
    kit.splat("Blood on the rail post", mat("blood"), P(bx - 0.045, 0.82, 0.8), 0.07, rot=(0, math.pi / 2, 0), seed=9, lumps=0.6)
    kit.splat("Blood on the catwalk", mat("old blood"), P(bx - 0.4, 1.3, 0.003), 0.25, seed=10, stretch=(1.0, 1.6))
    for i in range(6):
        kit.splat(f"Drip {i}", mat("old blood"), P(1.2 + i * 0.35 + rng.uniform(-0.1, 0.1), CW + 0.4 + rng.uniform(-0.15, 0.15), 0.003) if i < 3 else P(CW + 0.45 + rng.uniform(-0.1, 0.1), 2.0 - (i - 3) * 0.3, 0.003), 0.04, seed=20 + i)
    reb.prim("cube", "His other boot", mat("rubber"), P(bx - 0.5, 2.3, 0.07), (0.3, 0.12, 0.14), rot=(0, 0, 1.2), bevel=0.03)
    crow_b, crow_w = kit.crow("Crow on the rail", P(-1.2, -CATWALK, 1.09), heading=1.4)
    kit.crow("Crow on the roof", P(0.3, -1.0, 3.25), heading=4.0)

    # ---- Below and beyond: the hilltop, the forest, the valley, the smoke, the mansion.
    reb.terrain("Ground", rough, (C[0] - 40, C[0] + 50), (C[1] - 40, C[1] + 45), height, step=0.8)
    kit.body("Walt far below", (C[0] + 4.7, C[1] + 1.7, GROUND + 0.05), 2.3, pose="front", top=mat("khaki"), bloody=1.2, seed=7)

    def keep_out(x, y):
        v = Vector((x - C[0], y - C[1], 0.0))
        # A clear line down the slope to the smoke and to the house.
        if 0 < v.length < 80 and any(v.normalized().dot(d) > 0.985 for d in (SMOKE_DIR, MANSION_DIR)):
            return True
        return max(abs(x - C[0] - 3.0), abs(y - C[1] + 0.5)) < 11.5
    kit.forest(rng, height, keep_out, (C[0] - 40, C[1] - 40, C[0] + 50, C[1] + 45), count=120, spacing=2.0, tall=(13, 20), ferns=10, needles=300, dead=0.12)
    kit.vista(rng, (C[0] + 10, C[1]), (1.0, -0.25), below=-130.0, far=(330, 395), spread=260)
    kit.vista(rng, (C[0] - 10, C[1]), (-1.0, 0.3), below=-110.0, far=(250, 390), spread=200)
    base = Vector(C) .to_3d() + SMOKE_DIR * 230 + Vector((0, 0, -128))
    smoke = smoke_column(base)
    mpos = Vector(C).to_3d() + MANSION_DIR * 280 + Vector((0, 0, -131))
    mansion(mpos, math.atan2(MANSION_DIR.y, MANSION_DIR.x) + math.pi / 2)
    tv, tf, bases = [], [], []
    for i in range(60):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(45, 75)
        p = mpos + Vector((math.cos(a) * r, math.sin(a) * r * 0.7, 0))
        bases.append((Vector((p.x, p.y, mpos.z - 1)), rng.uniform(18, 26)))
        reb.box(tv, tf, (p.x, p.y, mpos.z + bases[-1][1] * 0.45), (7, 7, bases[-1][1] * 0.9), rot=a)
    reb.mesh_object("Trees round the mansion", tv, tf, reb.mat_plain("Far trees", (0.025, 0.04, 0.03), 1.0), smooth=False)

    # ---- Light: the low sun through the west glass; the sky over the valley.
    low_sun(232, 21, 5.5)
    reb.point("Cab fill", P(0, 0, 2.0), 6, (1.0, 0.85, 0.7), 0.6)

    anim = kit.Anim(16)
    anim.custom(lambda k: smoke(k))
    anim.custom(lambda k: setattr(rpivot, "rotation_euler", (math.radians(6) * math.sin(anim.phase(k)), math.radians(4) * math.cos(anim.phase(k)), 0)))
    anim.custom(lambda k: setattr(page_pivot, "rotation_euler", (0, -math.radians(25) * max(0.0, math.sin(anim.phase(k))), 0)))
    anim.bob(crow_b, height=0.04, speed=2)

    # ---- What the game needs.
    room.void(P(hx0, hy0)[:2] + P(hx1, hy1)[:2])
    # Down the hatch: action anywhere round its edge (the strip between it and
    # the cab wall alone is too narrow to stand in).
    room.door("tower-stairs", P(hx0 - 0.6, hy0 - 0.5)[:2] + P(hx1, hy1 + 0.5)[:2], arrive=P(-1.9, 0.75)[:2], face=(0, 1), walk=False, touch=False)
    room.check(P(fx - 0.8, fy - 0.8)[:2] + P(fx + 0.8, fy + 0.8)[:2], "The fire finder. Its sights are still set on a bearing: 047.\nNorth-east, down in the valley. Where the smoke is.")
    room.check(P(0.2, -CW)[:2] + P(1.2, -CW + 0.9)[:2], "The log. 01.20, SMOKE SIGHTED, NE, BRG 047. AIRCRAFT? RADIOED, NO ANSWER.\n03.00, DOGS AT THE FOOT OF THE TOWER. 04.40, BURNING UP. CANT STOP SCRATCHING.\nThe last line just says: THEY'RE ON THE STAIRS.")
    room.check(P(1.2, -CW)[:2] + P(2.3, -CW + 0.9)[:2], "The radio set's dead. The handset hangs on its cord.")
    room.check(P(kx - 0.4, CW - 0.7)[:2] + P(kx + 0.4, CW)[:2], "A board of keys by the door. One tag says SWITCH HOUSE.")
    room.check(P(CW - 1.0, -1.6)[:2] + P(CW - 0.7, 0.3)[:2], "His cot. Blood on the canvas, and scratch marks in the wall.\nHe tore at himself.")
    room.check(P(CATWALK - 0.7, 0.8)[:2] + P(CATWALK, 2.2)[:2], "The top rail's broken. Blood on the post.\nThis is where he went over.")
    room.check(P(CW + 0.2, -CATWALK)[:2] + P(CATWALK, -1.0)[:2], "Smoke, rising out of the trees in the valley. Something came down there.\nBravo's helicopter. And far off, a big house among the trees.")
    room.entry = "The lookout. You can see half the mountain from here."
    room.export(anim)


build()
