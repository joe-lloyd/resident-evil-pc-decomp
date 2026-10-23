"""The washout on Forest Road 7, afternoon.

What it tells: last night's storm blocked the culvert where the creek
crosses under the road. The creek came over the top instead and took the
south half of the road down into the gully. The rangers had put out a
barrier; it lies smashed on the gravel. The pickup that cut the chain on
the gate came round here in the dark, through the barrier, and went over
the edge: it is nose-down in the gully, its back wheels still up on the
crumbled lip, ARKLAY TIMBER CO. on the open driver's door. He was a logger
from Camp 4, running from what was happening there. He got out into the
pool at the bottom and never got further: he lies face down under the
water, a slick of blood round him. The creek still runs over the road and
pours off the edge. On the west side the long grass round the rocks is
where the adders lie up; one has left its skin on a flat stone. A path
goes south to the generator hut, whose fuel tank is dry. West, a track
climbs to the fire lookout tower, which stands over the trees.

Metres: the floor is x 1-19, y 3-12.5. The road runs east-west, y 4.5-8.5.
Between x 7 and 13 its south half is gone: the gully drops 3.3 m south of
y 6.3 (a void x 7-13, y 6.3-12.5), with the pickup in it and the pool at
the bottom. The creek comes down from the north at x 10, out of the
blocked culvert at y 3, over the road, and over the edge. The generator
hut is south of the floor, x 1.6-6, y 12.9-16.9, its door at x 3.3-4.3 in
the north wall; the dry tank stands in front of it. Doors: the road east
(x 19), the tower track west (x 1, y 4.6-7.6), the hut's door south.

Moving: the water over the road and down the bank, the pickup's door
creaking, the grass, dust in the low sun, a crow on the tailgate.
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

X0, X1, Y0, Y1 = 1.0, 19.0, 3.0, 12.5
ROAD = (4.5, 8.5)
GULLY = (7.0, 13.0)
EDGE = 6.3
POOL_Z = -3.15
HUT = (1.6, 6.0, 12.9, 16.9)
HUT_DOOR = (3.3, 4.3)
TOWER_AT = (-10.0, 3.5)
CAMS = [(18.4, 12.0, 3.4), (6.0, 5.2, 3.7), (1.6, 3.4, 3.4), (7.0, 12.2, 3.2), (12.6, 3.2, 3.5)]


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


def gully_depth(x, y):
    """How far below the road the gully floor is at (x, y), 0 outside it:
    a rough U, deepest along x 8.4-11.6, its banks up to the road's edge."""
    # The lip bitten back unevenly where the road broke away, and the sides
    # slumped in and out, not cut straight.
    edge = EDGE + 0.3 + 0.25 * noise.noise(Vector((x * 0.9, 0.5, 2))) + 0.18 * noise.noise(Vector((x * 2.6, 1.5, 3)))
    if y <= edge:
        return 0.0
    half = min(3.0, 2.7 + 0.8 * noise.noise(Vector((y * 0.6, x > 10.0, 7))) + 0.35 * noise.noise(Vector((y * 2.2, x > 10.0, 8))))  # never past the void (room.void)
    t = max(0.0, min(1.0, (half - abs(x - 10.0)) / 1.4))
    lat = t * t * (3 - 2 * t)
    u = min(1.0, (y - edge) / 1.5)
    down = u * u * (3 - 2 * u)
    rough = 0.3 * noise.noise(Vector((x * 1.3, y * 1.3, 5))) * lat * (1 - lat) * 4
    return max(0.0, lat * (3.4 * down + max(0.0, y - 14.5) * 0.4) + rough * down)


def height(x, y):
    g = gully_depth(x, y)
    if X0 - 0.3 < x < X1 + 0.3 and Y0 - 0.3 < y < Y1 + 0.3:
        return -g
    h = 0.35 * noise.noise(Vector((x * 0.12, y * 0.12, 4)))
    if y < Y0 - 0.3:
        h += (Y0 - 0.3 - y) * 0.5
        h -= 0.6 * math.exp(-((x - 10.0) ** 2) / 0.6)
    if x < X0 - 0.3:
        h += (X0 - 0.3 - x) * 0.17
    if y > Y1 + 0.3 and not (HUT[0] - 0.5 < x < HUT[1] + 0.5 and y < HUT[3] + 0.5):
        h -= (y - Y1 - 0.3) * 0.25
    if HUT[0] - 0.5 < x < HUT[1] + 0.5 and Y1 < y < HUT[3] + 0.5:
        h = min(h, 0.0)
    return h - g


def low_sun(heading, elevation, energy, rgb=(1.0, 0.7, 0.42)):
    """The afternoon sun low in the south-west: long shadows, warm light."""
    sun = kit.time_light("afternoon", sun_heading=heading, sun_energy=energy,
                         mist=((10, 7, 2), (70, 50, 14), 0.005))
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


def clear_water(name, tint, scale=1.6, see=0.7, shine=(0.85, 0.88, 0.9)):
    """Water you can see into, a body under it showing: tinted and see-through
    looking down, a mirror at a low angle (Fresnel), with ripples that move
    (Anim.ripple). Turn visible_shadow off on what uses it."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    nodes.remove(bsdf)
    tc = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.name = "Ripples"
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 6
    wave.inputs["Detail"].default_value = 4
    links.new(tc.outputs["Object"], wave.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.02
    links.new(wave.outputs["Fac"], bump.inputs["Height"])
    gloss = nodes.new("ShaderNodeBsdfGlossy")
    gloss.inputs["Roughness"].default_value = 0.06
    gloss.inputs["Color"].default_value = (*shine, 1)
    links.new(bump.outputs["Normal"], gloss.inputs["Normal"])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    clear.inputs["Color"].default_value = (*(c * see + (1 - see) * 0.1 for c in tint), 1)
    fres = nodes.new("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = 1.33
    links.new(bump.outputs["Normal"], fres.inputs["Normal"])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(fres.outputs["Fac"], mix.inputs["Fac"])
    links.new(clear.outputs["BSDF"], mix.inputs[1])
    links.new(gloss.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["Material Output"].inputs["Surface"])
    return m


def ribbon(name, m, path, width, z_of, step=0.25):
    """A strip along `path` [(x, y), ...], `width` wide, at height z_of(x, y)."""
    pts = [Vector(p) for p in path]
    samples = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / step))
        for i in range(n):
            samples.append(a.lerp(b, i / n))
    samples.append(pts[-1])
    v, f = [], []
    for i, p in enumerate(samples):
        q = samples[min(i + 1, len(samples) - 1)] - samples[max(i - 1, 0)]
        s = Vector((-q.y, q.x)).normalized() * width / 2
        for c in (p - s, p + s):
            v.append((c.x, c.y, z_of(c.x, c.y)))
        if i:
            k = 2 * i
            f.append((k - 2, k - 1, k + 1, k))
    return reb.mesh_object(name, v, f, m)


def pickup(name, paint, door_open=1.2):
    """The logging company's pickup (kit.pickup), its words on the driver's
    door. Returns (body, driver's door hinge)."""
    body, hinge = kit.pickup(name, paint, door_open=door_open)
    kit.text(f"{name} door words", "ARKLAY TIMBER CO.", mat("white paint"), (-0.68, 0.035, 0.0), size=0.1, rot=(math.pi / 2, 0, math.pi)).parent = hinge
    kit.text(f"{name} door words 2", "CAMP 4", mat("white paint"), (-0.68, 0.035, -0.17), size=0.1, rot=(math.pi / 2, 0, math.pi)).parent = hinge
    return body, hinge


def build():
    rng = random.Random(19)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # grass
    room.floor((8.7, Y0, 10.9, 6.3), "water")  # the water over the road
    room.floor((X0, ROAD[0], X1, ROAD[1]), "gravel")  # the road
    room.camera(CAMS[0], (8.0, 6.0, -0.6), 200, "from the south-east corner: the road coming in, the barrier, the gully and the pickup, the tower over the trees")
    room.camera(CAMS[1], (11.0, 10.4, -2.9), 205, "from the west lip: down into the gully, the pickup nose-down with its door open, the body in the pool")
    room.camera(CAMS[2], (9.0, 10.0, -0.8), 200, "from the north-west: the path to the generator hut, the adders' rocks, the gully's west bank")
    room.camera(CAMS[4], (19.5, 8.6, -0.2), 200, "from the north lip, east: the road coming in, the smashed barrier, the tracks")
    room.camera(CAMS[3], (-1.0, 5.0, 1.2), 200, "from in front of the hut: the track west to the tower, the road east")

    gravel = reb.mat_surface("Road gravel", [(0.0, (0.1, 0.085, 0.065)), (0.45, (0.2, 0.18, 0.15)), (0.75, (0.27, 0.24, 0.2)), (1.0, (0.17, 0.13, 0.09))], scale=14, bump=1.0)
    gravel = kit.dirtied(gravel, 0.6, scale=0.5)
    rut = reb.mat_surface("Ruts", [(0.0, (0.07, 0.055, 0.04)), (1.0, (0.14, 0.11, 0.08))], scale=10, rough=0.7, bump=0.6)
    tyre = reb.mat_surface("Tyre tracks", [(0.0, (0.03, 0.022, 0.015)), (1.0, (0.07, 0.05, 0.035))], scale=30, rough=0.6, bump=0.8)
    bank = reb.mat_surface("Gully bank", [(0.0, (0.07, 0.05, 0.03)), (0.5, (0.16, 0.12, 0.08)), (1.0, (0.24, 0.2, 0.15))], scale=3, bump=1.0)
    water = clear_water("Creek water", (0.8, 0.82, 0.74), see=0.82, shine=(0.32, 0.34, 0.33))
    pool = clear_water("Pool water", (0.5, 0.52, 0.4), scale=0.9, see=0.6)
    paint = reb.mat_surface("Pickup paint", [(0.0, (0.05, 0.08, 0.16)), (0.75, (0.08, 0.13, 0.24)), (1.0, (0.16, 0.08, 0.04))], scale=5, rough=0.5, bump=0.15)
    block = reb.mat_surface("Concrete block", [(0.0, (0.2, 0.2, 0.19)), (0.6, (0.32, 0.31, 0.29)), (1.0, (0.18, 0.15, 0.12))], scale=3, bump=0.5)
    stripes = reb.mat_stripes("Barrier stripes", [(0.45, 0.04, 0.03), (0.6, 0.6, 0.56)], across=4, axis="X")

    # ---- Ground, road, the gully's raw banks.
    reb.terrain("Ground", mat("grass"), (-32, 70), (-22, 36), height, step=0.4)
    v, f = [], []
    for gx in range(-60, 340):
        for gy in range(int((ROAD[1] - ROAD[0]) / 0.25)):
            xa, xb = gx * 0.25 - 15, gx * 0.25 - 14.75
            ya, yb = ROAD[0] + gy * 0.25, ROAD[0] + gy * 0.25 + 0.25
            cs = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
            if any(gully_depth(x, y) > 0.0 for x, y in cs):
                continue
            k = len(v)
            v += [(x, y, height(x, y) + 0.012) for x, y in cs]
            f.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Gravel road", v, f, gravel)
    # The raw earth of the banks, over the grass where the gully is.
    bv, bf = [], []
    for gx in range(int((GULLY[1] - GULLY[0] + 2) / 0.3)):
        for gy in range(int((Y1 + 8 - EDGE) / 0.3)):
            xa = GULLY[0] - 1 + gx * 0.3
            ya = EDGE - 0.2 + gy * 0.3
            cs = [(xa, ya), (xa + 0.3, ya), (xa + 0.3, ya + 0.3), (xa, ya + 0.3)]
            if all(gully_depth(x, y) < 0.05 for x, y in cs):
                continue
            k = len(bv)
            bv += [(x, y, height(x, y) + 0.02) for x, y in cs]
            bf.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Gully earth", bv, bf, bank)
    kit.path_strip("Old rut", rut, [(X0 - 15, 5.6), (X1 + 50, 5.6)], height, width=0.22, wobble=0.25, lift=0.02)
    for xa, xb in ((X0 - 15, GULLY[0] - 0.6), (GULLY[1] + 0.6, X1 + 50)):
        kit.path_strip("Old rut", rut, [(xa, 7.4), (xb, 7.4)], height, width=0.22, wobble=0.25, lift=0.02)
    # The pickup's tracks off the road and over the edge.
    for dy in (-0.8, 0.8):
        kit.path_strip("Fresh tyre track", tyre, [(X1 + 40, 6.6 + dy), (16.0, 6.5 + dy), (13.6, 6.0 + dy * 0.5)], height, width=0.08, wobble=0.1, lift=0.03)
    # Chunks of the road's edge, broken off down the bank.
    rv, rf = [], []
    for i in range(16):
        x = rng.uniform(GULLY[0] + 0.3, GULLY[1] - 0.3)
        y = EDGE + rng.uniform(0.2, 2.6)
        reb.boulder(rng, (x, y, height(x, y) + 0.05), rng.uniform(0.15, 0.35), rv, rf, squash=0.5)
    reb.mesh_object("Road chunks", rv, rf, gravel)
    rv, rf = [], []
    for (x, y, r) in ((2.0, 10.2, 0.6), (1.4, 11.4, 0.45), (6.2, 9.8, 0.55), (-0.5, 8.0, 0.9), (17.8, 2.4, 0.8), (13.6, 2.2, 0.7)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Rocks", rv, rf, mat("rock"))
    rv, rf = [], []
    for (x, y, r) in ((7.9, 10.6, 0.5), (12.3, 9.4, 0.45), (8.4, 12.8, 0.55), (11.9, 13.2, 0.6), (8.8, 8.0, 0.3), (11.0, 12.4, 0.3), (9.2, 13.6, 0.35)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Gully rocks", rv, rf, mat("wet rock"))

    # ---- The creek: out of the blocked culvert, over the road, off the edge, into the pool.
    culvert = kit.rod("Culvert", mat("rust"), (10.0, 1.2, -0.25), (10.0, 3.1, -0.25), 0.45, 16)
    reb.prim("cyl", "Culvert mouth", mat("black"), (10.0, 3.08, -0.25), (0.82, 0.82, 0.04), rot=(math.pi / 2, 0, 0), segments=16)
    branches = []
    for i in range(7):
        a = Vector((10.0 + rng.uniform(-0.6, 0.6), 2.9 + rng.uniform(-0.2, 0.2), rng.uniform(-0.4, 0.2)))
        d = Vector((rng.uniform(-1, 1), rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.4))).normalized() * rng.uniform(0.6, 1.2)
        branches.append(kit.rod("Branch", mat("bark"), a, a + d, rng.uniform(0.03, 0.06), 6))
    kit.join("Branches in the culvert", branches)
    wet = []
    wet.append(ribbon("Creek above the road", water, [(10.0, -14.0), (10.05, -6.0), (9.95, 0.0), (10.0, 2.7)], 0.8, lambda x, y: height(10.0, y) + 0.12))
    sheet = kit.splat("Water over the road", water, (9.8, 4.9, 0.022), 1.0, seed=21, stretch=(1.1, 1.9), lumps=0.7, points=48)
    wet.append(sheet)
    wet.append(ribbon("Water down the bank", water, [(9.3, EDGE + 0.05), (9.1, EDGE + 0.6), (9.0, EDGE + 1.4), (8.9, EDGE + 2.9)], 1.4, lambda x, y: height(x, y) + 0.05, step=0.12))
    wet.append(reb.prim("cube", "Pool", pool, (10.0, 11.5, POOL_Z), (6.4, 7.0, 0.02)))
    for ob in wet:
        ob.visible_shadow = False
    kit.splat("Foam", reb.mat_plain("Foam", (0.5, 0.48, 0.42), 0.8), (8.9, EDGE + 2.6, POOL_Z + 0.005), 0.4, seed=4, stretch=(1.4, 0.6), lumps=0.6)

    # ---- The pickup, nose-down in the gully, door open; the driver under the water.
    rear, nose = Vector((11.3, EDGE + 0.25, -0.25)), Vector((10.8, 9.9, POOL_Z - 0.1))
    d = nose - rear
    truck, door_pivot = pickup("Pickup", paint, door_open=1.15)
    truck.location = (rear + nose) / 2 + Vector((0, 0, 0.1))
    truck.rotation_euler = (0.06, math.atan2(-d.z, d.xy.length), math.atan2(d.y, d.x))
    kit.splat("Blood on the door", mat("blood"), (-0.4, 0.04, 0.1), 0.1, rot=(math.pi / 2, 0, 0), seed=12).parent = door_pivot
    b, w = kit.crow("Crow on the lip", (12.3, 5.9, 0.0), heading=1.2)
    reb.cloth("Tarp blown out of the bed", mat("canvas"), (12.4, EDGE - 0.1, 0.03), (1.0, 0.7), rot=(0, 0, 0.4), lumps=0.05, seed=3)
    # West of the pickup's nose, his back just breaking the water, so the
    # camera on the west lip sees him past the cab.
    driver = kit.body("Logger", (9.0, 11.3, POOL_Z - 0.08), 1.2, pose="front", top=reb.mat_plain("Hi-vis vest", (0.6, 0.2, 0.02), 0.7), legs=mat("denim"), seed=4)
    kit.splat("Blood in the water", reb.mat_plain("Blood in water", (0.12, 0.01, 0.006), 0.2), (9.0, 11.7, POOL_Z + 0.004), 0.75, seed=9, stretch=(1.5, 0.9), lumps=0.6)
    reb.prim("cube", "Cap floating", reb.mat_plain("Cap orange", (0.45, 0.13, 0.03), 0.7), (11.4, 11.6, POOL_Z + 0.03), (0.22, 0.18, 0.06), rot=(0, 0, 0.5), bevel=0.03)
    cone = reb.prim("cone", "Traffic cone", reb.mat_plain("Cone orange", (0.6, 0.15, 0.02), 0.6), (16.4, 10.4, 0.18), (0.36, 0.36, 0.7), rot=(1.45, 0, 0.7), segments=14, top=0.15)
    kit.shards("Windscreen glass", (11.6, EDGE - 0.3, 0.0), spread=0.6, count=10, seed=2)

    # ---- The rangers' barrier, smashed across the road east of the gap.
    for i, (x, y, rot) in enumerate(((15.4, 5.1, 0.5), (14.2, 7.9, 2.0))):
        legs = [kit.rod("Sawhorse leg", mat("planks"), (x - 0.35, y - 0.25, 0), (x - 0.2, y, 0.9), 0.04, 6),
                kit.rod("Sawhorse leg", mat("planks"), (x - 0.35, y + 0.25, 0), (x - 0.2, y, 0.9), 0.04, 6),
                kit.rod("Sawhorse leg", mat("planks"), (x + 0.35, y - 0.25, 0), (x + 0.2, y, 0.9), 0.04, 6),
                kit.rod("Sawhorse leg", mat("planks"), (x + 0.35, y + 0.25, 0), (x + 0.2, y, 0.9), 0.04, 6)]
        horse = kit.join(f"Sawhorse {i}", legs)
        horse.rotation_euler = (0, 0, rot) if i == 0 else (math.pi / 2 - 0.1, 0, rot)
        if i:
            horse.location = (x, y, 0.25)
    reb.prim("cube", "Barrier board", stripes, (14.9, 6.2, 0.05), (1.6, 0.25, 0.04), rot=(0, 0.06, 0.3))
    reb.prim("cube", "Barrier board, broken off", stripes, (13.7, 6.9, 0.05), (0.9, 0.25, 0.04), rot=(0, -0.08, 1.6))
    reb.prim("cube", "Barrier plate", mat("white paint"), (15.9, 6.9, 0.03), (0.7, 0.45, 0.02), rot=(0.05, 0, -0.4))
    kit.text("Barrier words", "ROAD CLOSED", mat("red paint"), (15.9, 6.9, 0.045), size=0.1, rot=(0, 0, -0.4 + math.pi / 2))

    # ---- The path south to the generator hut; the dry tank in front of it.
    ribbon("Hut path", reb.mat_surface("Path dirt", [(0.0, (0.09, 0.07, 0.045)), (1.0, (0.17, 0.13, 0.09))], scale=6, bump=0.6),
           [(4.4, ROAD[1] - 0.2), (4.0, 10.0), (3.8, 11.6), (3.8, 12.9)], 1.0, lambda x, y: 0.015)
    hx0, hx1, hy0, hy1 = HUT
    for ob in kit.walls(hx0 + 0.12, hy0 + 0.12, hx1 - 0.12, hy1 - 0.12, 2.9, block, openings=[("n", HUT_DOOR[0], HUT_DOOR[1], 0.0, 2.1)], name="Hut wall"):
        reb.wall(ob)
    reb.prim("cube", "Hut footing", block, ((hx0 + hx1) / 2, (hy0 + hy1) / 2, -0.8), (hx1 - hx0, hy1 - hy0, 1.6))
    reb.prim("cube", "Hut roof", mat("concrete"), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 2.98), (hx1 - hx0 + 0.4, hy1 - hy0 + 0.4, 0.16))
    reb.prim("cube", "Hut door", mat("green paint"), ((HUT_DOOR[0] + HUT_DOOR[1]) / 2, hy0 + 0.1, 1.05), (HUT_DOOR[1] - HUT_DOOR[0], 0.06, 2.1), bevel=0.01)
    reb.prim("cube", "Hut door handle", mat("steel"), (HUT_DOOR[1] - 0.12, hy0 + 0.05, 1.0), (0.04, 0.06, 0.16))
    reb.prim("cube", "Hut sign", mat("yellow paint"), (5.0, hy0 - 0.01, 1.7), (0.7, 0.02, 0.45))
    kit.text("Hut sign words", "DANGER", mat("black"), (5.0, hy0 - 0.025, 1.8), size=0.1)
    kit.text("Hut sign words 2", "GENERATOR", mat("black"), (5.0, hy0 - 0.025, 1.62), size=0.08)
    kit.rod("Exhaust stack", mat("rust"), (2.4, 14.4, 2.9), (2.4, 14.4, 4.4), 0.08, 10)
    reb.prim("cone", "Exhaust cap", mat("rust"), (2.4, 14.4, 4.48), (0.28, 0.28, 0.12), segments=10, top=0.2)
    for i in range(3):
        reb.prim("cube", f"Vent slat {i}", mat("iron"), (hx1 + 0.01, 14.5, 1.9 + i * 0.12), (0.03, 0.8, 0.05), rot=(0, 0.4, 0))
    kit.splat("Soot over the vent", mat("black"), (hx1 + 0.02, 14.5, 2.3), 0.3, rot=(0, math.pi / 2, 0), seed=5, stretch=(0.8, 1.4))
    tank_c = (5.3, 12.1)
    tank = kit.rod("Fuel tank", mat("green paint"), (tank_c[0] - 1.0, tank_c[1], 0.85), (tank_c[0] + 1.0, tank_c[1], 0.85), 0.5, 20)
    reb.mask(reb.wall(tank))
    for dx in (-0.7, 0.7):
        reb.prim("cube", "Tank cradle", mat("iron"), (tank_c[0] + dx, tank_c[1], 0.3), (0.12, 0.9, 0.6))
    kit.text("Tank words", "DIESEL", mat("white paint"), (tank_c[0], tank_c[1] - 0.505, 0.9), size=0.16)
    reb.prim("cyl", "Tank gauge", mat("white paint"), (tank_c[0] + 0.5, tank_c[1], 1.37), (0.16, 0.16, 0.03), segments=14)
    reb.prim("cube", "Gauge needle", mat("red paint"), (tank_c[0] + 0.45, tank_c[1], 1.39), (0.08, 0.008, 0.005), rot=(0, 0, 0.3))
    kit.rod("Fuel line", mat("iron"), (tank_c[0] - 1.0, tank_c[1], 0.5), (tank_c[0] - 1.6, hy0 + 0.05, 0.5), 0.02)
    reb.prim("cyl", "Hand pump", mat("red paint"), (tank_c[0] - 0.2, tank_c[1], 1.45), (0.1, 0.1, 0.25), segments=10)
    kit.drum("Empty drum", mat("rust"), (6.5, 11.5, 0.0), tipped=True, rot=1.0)
    kit.splat("Diesel stain", reb.mat_plain("Diesel stain", (0.03, 0.03, 0.028), 0.3), (5.6, 11.6, 0.0), 0.5, seed=7, stretch=(1.3, 0.8))

    # ---- The adders' rocks on the west side: long grass, a shed skin on a flat stone.
    tall = kit.meadow(rng, 500, lambda r: (r.uniform(0.6, 3.2), r.uniform(9.2, 12.4)), lambda x, y: 0.0, mat("dead grass"))
    tall.scale = (1, 1, 2.4)
    tall2 = kit.meadow(rng, 300, lambda r: (r.uniform(5.4, 7.0), r.uniform(8.8, 10.8)), lambda x, y: 0.0, mat("blades"))
    tall2.scale = (1, 1, 2.0)
    reb.prim("cube", "Flat stone", mat("rock"), (2.6, 9.6, 0.06), (0.8, 0.6, 0.12), rot=(0, 0, 0.3), bevel=0.04)
    skin = []
    for k in range(10):
        t = k / 9
        a = Vector((2.35 + 0.5 * t, 9.5 + 0.12 * math.sin(t * 6), 0.135))
        b2 = Vector((2.35 + 0.5 * (t + 0.11), 9.5 + 0.12 * math.sin((t + 0.11) * 6), 0.135))
        skin.append(kit.rod("Skin", reb.mat_plain("Shed skin", (0.5, 0.46, 0.38), 0.6), a, b2, 0.012 * (1 - 0.6 * t), 6))
    kit.join("Shed snakeskin", skin)

    # ---- The tower over the trees to the west, where the track goes.
    bm = Beams()
    timber = reb.mat_wood("Tower timber", (0.15, 0.13, 0.11))
    glass = reb.mat_glass("Cab glass", (0.5, 0.55, 0.55))
    tz = height(*TOWER_AT)
    tower(bm, timber, TOWER_AT, tz)
    cab_shell(bm, timber, glass, TOWER_AT, tz, roof_m=mat("tin"))
    bm.build("Lookout tower")
    ribbon("Tower track", reb.mat_surface("Track dirt", [(0.0, (0.09, 0.07, 0.045)), (1.0, (0.17, 0.13, 0.09))], scale=6, bump=0.6),
           [(X0 + 1.5, 6.4), (X0 - 1.0, 6.0), (-4.0, 5.0), (-7.0, 4.0), (-10.0, 3.5)], 1.3, lambda x, y: height(x, y) + 0.02)
    kit.rod("Track sign post", mat("dark wood"), (1.5, 8.2, -0.2), (1.5, 8.2, 1.5), 0.05)
    reb.prim("cube", "Track sign", mat("dark wood"), (1.5, 8.2, 1.35), (0.06, 1.0, 0.22))
    kit.text("Track sign words", "FIRE LOOKOUT", mat("white paint"), (1.54, 8.2, 1.35), size=0.1, rot=(math.pi / 2, 0, math.pi / 2))
    reb.wall(reb.prim("cube", "Sign footprint", None, (1.5, 8.2, 0.5), (0.2, 0.2, 1.0))).hide_render = True

    # ---- The forest round it, kept off the floor, the gully, the hut, the track and the cameras.
    def keep_out(x, y):
        if X0 - 1.5 < x < X1 + 1.5 and Y0 - 1.4 < y < Y1 + 0.8:
            return True
        if GULLY[0] - 1 < x < GULLY[1] + 1 and y > EDGE:
            return True
        if HUT[0] - 1.2 < x < HUT[1] + 1.2 and y < HUT[3] + 1.2:
            return True
        if (Vector((x, y)) - Vector(TOWER_AT)).length < 6.0 or (-10 < x < X0 and 2.0 < y < 7.6):
            return True
        if 8.5 < x < 11.5 and y < Y0:
            return True
        if ROAD[0] - 1.0 < y < ROAD[1] + 1.0 and x > X1:
            return True
        return any((Vector((x, y)) - Vector(c[:2])).length < 4.0 for c in CAMS)
    kit.forest(rng, height, keep_out, (-30, -20, 68, 34), count=150, spacing=1.8, ferns=40, needles=900, dead=0.12)

    def verge(r):
        while True:
            x, y = r.uniform(X0 - 10, X1 + 10), r.uniform(Y0 - 4, Y1 + 4)
            if not (ROAD[0] + 0.1 < y < ROAD[1] - 0.1) and gully_depth(x, y) == 0 and not (HUT[0] - 0.3 < x < HUT[1] + 0.3 and y > HUT[2] - 0.3):
                return x, y
    grass = kit.meadow(rng, 2000, verge, height)

    # Wet rocks along the creek where it comes down the hill to the culvert.
    rv, rf = [], []
    for i in range(16):
        y = rng.uniform(-12.0, 2.2)
        x = 10.0 + rng.choice((-1, 1)) * rng.uniform(0.5, 0.9)
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.18, 0.4), rv, rf)
    reb.mesh_object("Creek stones", rv, rf, mat("wet rock"))

    # ---- Light: the low sun from the south-west, dust in it; the sky's light down into the gully.
    low_sun(232, 21, 7.5)
    reb.spot("Sky into the gully", (9.6, 8.6, 7.0), (9.6, 11.2, POOL_Z), 900, (0.75, 0.8, 0.95), 60, 0.9, 2.0)
    motes = dust(rng, (X0, Y0, X1, Y1), 100)

    anim = kit.Anim(16)
    anim.ripple(water, speed=2)
    anim.ripple(pool, speed=1)
    anim.swing(door_pivot, axis=2, degrees=5)
    anim.sway(grass, amount=0.05)
    anim.sway(tall, amount=0.06)
    anim.bob(b, height=0.04, speed=2)
    anim.custom(lambda k: setattr(motes, "location", (0.25 * math.sin(anim.phase(k)), 0.1 * math.cos(anim.phase(k)), 0.06 * math.sin(anim.phase(k, 2)))))

    # ---- What the game needs.
    room.void((GULLY[0], EDGE, GULLY[1], Y1))
    room.door("road", (X1 - 0.6, ROAD[0], X1, ROAD[1]), arrive=(17.4, 6.5), face=(-1, 0))
    room.door("tower-foot", (X0, 4.6, X0 + 0.6, 7.6), arrive=(2.6, 6.1), face=(1, 0))
    room.door("generator", (HUT_DOOR[0] - 0.1, Y1 - 0.8, HUT_DOOR[1] + 0.1, Y1), arrive=(3.8, 11.2), face=(0, -1), walk=False, touch=False)
    room.check((10.4, EDGE - 0.6, 12.6, EDGE), "A pickup, nose-down in the gully. ARKLAY TIMBER CO., CAMP 4.\nHe drove straight through the barrier in the dark.")
    room.check((7.6, EDGE - 0.6, 10.4, EDGE), "Down in the pool, face down. A logger, in his orange vest.\nHe got out of the truck, and no further.")
    room.check((8.8, Y0, 11.2, 4.0), "The culvert's choked with branches. The creek's coming over the road instead.")
    room.check((13.2, 5.0, 16.4, 8.0), "A ROAD CLOSED barrier, smashed to pieces.")
    room.check((tank_c[0] - 1.1, tank_c[1] - 0.9, tank_c[0] + 1.1, tank_c[1] - 0.4), "The generator's fuel tank. The gauge reads empty.\nI knock on it. Hollow.")
    room.check((1.8, 9.1, 3.4, 10.1), "A snake's shed skin, on the warm stone.\nAdders. I'll keep out of the long grass.")
    room.check((X0, 7.7, 2.2, 8.7), "FIRE LOOKOUT. The track climbs west, to the tower.")
    room.export(anim)


build()
