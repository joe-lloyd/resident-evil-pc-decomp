"""The track under the gondola's power line, afternoon.

What it tells: the line runs from the switch house, behind the generator
hut, along a mown strip through the forest to the Arklay Skyway's upper
station. Dale walked it at two in the morning with his torch and his hard
hat, and the dogs were on the track, feeding. They had brought down a deer
under the wires and opened it up; it lies there still, ribs out, crows on
it and on the wires over it, flies. One of them went for him: his hard hat
lies upside down on the track with blood in it, his torch is smashed, and
the grass is flattened where he fought it off, then a trail of blood back
to the switch house. The line is dead. A broken insulator string swings
from the first pylon's crossarm, and a loose jumper wire from the second
sways in the wind. At the east end the chain-link gate into the gondola
station stands open.

Metres: the floor is x 1-19, y 3-11. The track runs east-west along y 6-8.
The switch house is at the west, x -2.6-1.0, y 5.0-8.4, its door in the
east wall at y 6.2-7.1, standing open; the generator hut stands north of
it. The pylons stand south of the track at x 6.5 and 15.5, y 10.2; the
line runs over the track. The deer lies at x 10.5-12, y 8.6-9.6. A wire
fence runs along the north edge. The gate into the gondola station is in
the chain-link fence at the east edge, x 19.6, y 6-8.

Moving: the broken insulator and the loose wire swinging, the long grass,
flies over the deer, a crow on the deer.
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

X0, X1, Y0, Y1 = 1.0, 19.0, 3.0, 11.0
TRACK = (6.0, 8.0)
SWITCH = (-2.6, 1.0, 5.0, 8.4)
SWITCH_DOOR = (6.2, 7.1)
GEN_HUT = (-3.2, 1.2, 0.4, 4.4)
PYLONS = ((6.5, 10.2), (15.5, 10.2))
GATE_X = 19.6
OFF = 17.7       # the platform's x = this room's x - OFF
DEER = (11.2, 9.1)
CAMS = [(2.6, 4.0, 3.6), (18.5, 3.5, 3.4), (11.8, 3.6, 3.8), (4.0, 9.9, 3.2), (14.2, 3.4, 3.3)]


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
        return [reb.mesh_object(f"{name}, {m.name}", v, f, m, smooth=False) for m, (v, f) in self.parts.items()]


def height(x, y):
    if X0 - 0.4 < x < GATE_X + 0.3 and Y0 - 0.4 < y < Y1 + 0.4:
        return 0.0
    h = 0.35 * noise.noise(Vector((x * 0.12, y * 0.12, 3)))
    if y < Y0 - 0.4:
        h += (Y0 - 0.4 - y) * 0.35
    if y > Y1 + 0.4 and x < X1 + 1.2:
        h -= (y - Y1 - 0.4) * 0.3
    if x > GATE_X + 0.3:
        # The gondola station's slab, the mountain rising north and east of
        # it, falling away to the valley south of it.
        if y > 13.4:
            return -0.4 - (y - 13.4) * 1.6
        h = -0.4 + max(0.0, 1.4 - y) * 0.5 + max(0.0, x - 35.2) * 0.3
    return h


def low_sun(heading, elevation, energy, rgb=(1.0, 0.7, 0.42)):
    """The afternoon sun low in the south-west: long shadows, warm light."""
    sun = kit.time_light("afternoon", sun_heading=heading, sun_energy=energy,
                         mist=((10, 7, 3), (80, 50, 16), 0.004))
    sun.rotation_euler[0] = math.radians(90 - elevation)
    sun.data.color = rgb
    bpy.context.view_layer.update()
    kit._sky((0.86, 0.64, 0.44), (0.3, 0.38, 0.56), 0.8, sun)
    return sun


def lattice(bm, steel, c, base=2.6, top=1.0, h=13.0, arm=6.6):
    """A steel lattice pylon at c, its crossarm at h, legs splaying to `base`."""
    cx, cy = c
    def leg(i, z):
        sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[i]
        w = base / 2 + (top / 2 - base / 2) * z / h
        return (cx + sx * w, cy + sy * w, z)
    levels = [0.0, 2.5, 5.0, 7.5, 10.0, h]
    for i in range(4):
        bm.box(steel, leg(i, -0.3), leg(i, h + 0.4), 0.09)
    for za, zb in zip(levels, levels[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.box(steel, leg(i, zb), leg(j, zb), 0.06)
            bm.box(steel, leg(i, za), leg(j, zb), 0.04)
            bm.box(steel, leg(j, za), leg(i, zb), 0.04)
    for dz in (0.0, 0.5):
        bm.box(steel, (cx, cy - arm / 2, h + dz), (cx, cy + arm / 2, h + dz), 0.12)
    for s in (-1, 1):
        bm.box(steel, (cx, cy + s * arm / 2, h), (cx, cy + s * 0.5, h + 0.5), 0.06)
    bm.box(steel, (cx, cy, h + 0.5), (cx, cy, h + 2.2), 0.08)
    bm.box(steel, (cx, cy - 0.8, h + 2.2), (cx, cy + 0.8, h + 2.2), 0.08)


def insulator(name, top, length=0.9):
    """A string of insulator discs hanging from `top`; returns it (one object)."""
    parts = []
    for k in range(6):
        z = -0.1 - k * length / 6
        parts.append(reb.prim("cyl", "disc", reb.mat_plain("Glaze", (0.3, 0.2, 0.12), 0.25), (0, 0, z), (0.22, 0.22, 0.05), segments=12))
    parts.append(kit.rod("pin", mat("iron"), (0, 0, 0), (0, 0, -length - 0.1), 0.015, 6))
    ob = kit.join(name, parts)
    ob.location = top
    return ob


def sag(a, b, drop, n=16):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, drop * 4 * (i / n) * (1 - i / n))) for i in range(n + 1)]


def wire(name, m, pts, r=0.012):
    parts = [kit.rod("w", m, p, q, r, 5) for p, q in zip(pts, pts[1:])]
    return kit.join(name, parts)


def deer(name, at, heading):
    """A dead deer on its side, opened up: one object, and its ribs."""
    hide = reb.mat_surface("Deer hide", [(0.0, (0.12, 0.07, 0.035)), (0.7, (0.22, 0.13, 0.06)), (1.0, (0.3, 0.24, 0.17))], scale=8, bump=0.3)
    belly = reb.mat_plain("Deer belly", (0.35, 0.3, 0.24), 0.9)
    parts = [
        reb.prim("sphere", "body", hide, (0, 0, 0.26), (1.3, 0.5, 0.5), segments=18),
        reb.prim("sphere", "rump", hide, (-0.5, 0, 0.27), (0.6, 0.52, 0.52), segments=14),
        kit.rod("neck", hide, (0.55, 0.0, 0.3), (0.95, -0.1, 0.18), 0.11, 10),
        reb.prim("sphere", "head", hide, (1.08, -0.15, 0.13), (0.34, 0.16, 0.18), segments=12),
        reb.prim("sphere", "ear", hide, (0.98, -0.05, 0.27), (0.12, 0.04, 0.08), segments=8),
        reb.prim("sphere", "muzzle", mat("black"), (1.25, -0.2, 0.1), (0.07, 0.07, 0.07), segments=8),
    ]
    for (x, y, dx, dy) in ((0.35, 0.18, 0.5, 0.45), (0.4, 0.05, 0.75, 0.3), (-0.55, 0.15, -0.3, 0.75), (-0.6, 0.05, -0.9, 0.5)):
        parts.append(kit.rod("leg", hide, (x, y, 0.15), (x + dx * 0.5, y + dy, 0.08), 0.045, 8))
        parts.append(kit.rod("shin", mat("black"), (x + dx * 0.5, y + dy, 0.08), (x + dx * 0.6, y + dy * 1.35, 0.05), 0.03, 6))
    parts.append(reb.prim("sphere", "belly open", mat("old blood"), (0.05, 0.22, 0.24), (0.7, 0.12, 0.3), segments=14))
    ob = kit.join(name, parts)
    ob.location = at
    ob.rotation_euler = (0, 0, heading)
    ribs = []
    for k in range(7):
        x = -0.15 + k * 0.08
        ribs.append(kit.rod("rib", mat("bone"), (x, 0.24, 0.12), (x + 0.03, 0.27, 0.42), 0.012, 5))
    rb = kit.join(f"{name} ribs", ribs)
    rb.parent = ob
    return ob


def build():
    rng = random.Random(53)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera(CAMS[0], (12.0, 8.4, 0.6), 200, "from by the switch house: the track east under the wires, the pylons, the deer")
    room.camera(CAMS[1], (8.0, 8.6, 0.6), 200, "from by the gate: the track west to the switch house, the hat, the long grass")
    room.camera(CAMS[2], (11.2, 9.6, 0.0), 205, "from the north fence: down on the deer and its crows, the second pylon")
    room.camera(CAMS[3], (0.0, 4.6, 1.0), 200, "from between the pole and the first pylon: the switch house door, the generator hut, the blood back to the door")
    room.camera(CAMS[4], (19.8, 7.6, 0.9), 200, "from the north-east: the open gate into the gondola station")

    track_m = reb.mat_surface("Track dirt", [(0.0, (0.09, 0.07, 0.045)), (0.6, (0.17, 0.13, 0.09)), (1.0, (0.21, 0.18, 0.13))], scale=6, bump=0.6)
    rut = reb.mat_surface("Ruts", [(0.0, (0.06, 0.045, 0.03)), (1.0, (0.12, 0.09, 0.06))], scale=10, rough=0.7, bump=0.6)
    brick = kit.dirtied(reb.mat_surface("Painted brick", [(0.0, (0.2, 0.17, 0.13)), (0.55, (0.32, 0.29, 0.23)), (1.0, (0.26, 0.11, 0.07))], scale=7, bump=0.6), 0.6, scale=1.2)
    block = reb.mat_surface("Concrete block", [(0.0, (0.2, 0.2, 0.19)), (0.6, (0.32, 0.31, 0.29)), (1.0, (0.18, 0.15, 0.12))], scale=3, bump=0.5)
    steel = reb.mat_metal("Galvanised", (0.32, 0.33, 0.33), 0.5)
    door_m = reb.mat_surface("Door grey", [(0.0, (0.12, 0.14, 0.12)), (0.8, (0.2, 0.22, 0.2)), (1.0, (0.2, 0.1, 0.05))], scale=5, rough=0.5, bump=0.15)
    link_m = reb.mat_surface("Chain link", [(0.0, (0.18, 0.18, 0.17)), (1.0, (0.3, 0.3, 0.28))], scale=60, rough=0.5, bump=0.8)
    nodes, links = link_m.node_tree.nodes, link_m.node_tree.links
    holes = nodes.new("ShaderNodeBsdfTransparent")
    see = nodes.new("ShaderNodeMixShader")
    see.inputs["Fac"].default_value = 0.35
    links.new(holes.outputs["BSDF"], see.inputs[1])
    links.new(nodes["Principled BSDF"].outputs["BSDF"], see.inputs[2])
    links.new(see.outputs["Shader"], nodes["Material Output"].inputs["Surface"])
    hat_m = reb.mat_plain("Hard hat", (0.6, 0.45, 0.04), 0.4)

    # ---- Ground: the mown strip, the track, the ruts.
    reb.terrain("Ground", mat("grass"), (-24, 62), (-18, 44), height, step=0.5)
    kit.path_strip("Track", track_m, [(SWITCH[1] - 0.2, 6.65), (5.0, 7.0), (12.0, 6.9), (GATE_X + 0.5, 7.0)], height, width=0.9, wobble=0.25, lift=0.01)
    for dy in (-0.55, 0.55):
        kit.path_strip("Rut", rut, [(3.0, 7.0 + dy), (12.0, 6.9 + dy), (GATE_X, 7.0 + dy)], height, width=0.13, wobble=0.2, lift=0.02)

    # ---- The switch house and the generator hut at the west end.
    sx0, sx1, sy0, sy1 = SWITCH
    for ob in kit.walls(sx0 + 0.22, sy0 + 0.22, sx1 - 0.22, sy1 - 0.22, 2.9, brick, openings=[("e", SWITCH_DOOR[0], SWITCH_DOOR[1], 0.0, 2.1), ("s", sx0 + 1.2, sx0 + 2.0, 1.85, 2.4)], thick=0.22, name="Switch house wall"):
        reb.wall(ob)
    reb.prim("cube", "Switch house roof", mat("concrete"), ((sx0 + sx1) / 2, (sy0 + sy1) / 2, 3.0), (sx1 - sx0 + 0.3, sy1 - sy0 + 0.3, 0.16))
    reb.prim("cube", "Switch house dark", mat("black"), ((sx0 + sx1) / 2 - 0.3, (sy0 + sy1) / 2, 1.4), (2.6, 2.6, 2.7))
    hinge = reb.prim("sphere", "Switch door hinge", mat("black"), (sx1, SWITCH_DOOR[1], 1.05), (0.03, 0.03, 0.03))
    reb.prim("cube", "Switch door", door_m, (0.0, -0.45, 0.0), (0.05, 0.9, 2.1), bevel=0.01).parent = hinge
    hinge.rotation_euler = (0, 0, 1.3)
    reb.prim("cube", "Switch house sign", mat("yellow paint"), (sx1 + 0.01, 5.6, 1.6), (0.01, 0.42, 0.42))
    kit.text("Switch sign words", "DANGER", mat("black"), (sx1 + 0.02, 5.6, 1.72), size=0.07, rot=(math.pi / 2, 0, math.pi / 2))
    kit.text("Switch sign words 2", "11 000 V", mat("black"), (sx1 + 0.02, 5.6, 1.5), size=0.07, rot=(math.pi / 2, 0, math.pi / 2))
    kit.splat("Handprint on the door frame", mat("old blood"), (sx1 + 0.005, SWITCH_DOOR[0] - 0.12, 1.15), 0.06, rot=(0, math.pi / 2, 0), seed=5, lumps=0.5)
    gx0, gx1, gy0, gy1 = GEN_HUT
    for ob in kit.walls(gx0 + 0.12, gy0 + 0.12, gx1 - 0.12, gy1 - 0.12, 2.9, block, name="Generator hut wall"):
        reb.wall(ob)
    reb.prim("cube", "Generator hut roof", mat("concrete"), ((gx0 + gx1) / 2, (gy0 + gy1) / 2, 2.98), (gx1 - gx0 + 0.4, gy1 - gy0 + 0.4, 0.16))
    kit.rod("Exhaust stack", mat("rust"), (gx0 + 1.0, 2.0, 2.9), (gx0 + 1.0, 2.0, 4.4), 0.08, 10)
    for i in range(3):
        reb.prim("cube", f"Vent slat {i}", mat("iron"), (gx1 + 0.01, 2.4, 1.9 + i * 0.12), (0.03, 0.8, 0.05), rot=(0, 0.4, 0))
    # The terminal pole by the switch house, the feeders up to the line.
    POLE = (2.0, 12.0)
    for dy in (-0.9, 0.9):
        kit.rod("Terminal pole", mat("dark wood"), (POLE[0], POLE[1] + dy, -0.5), (POLE[0], POLE[1] + dy, 9.5), 0.14, 10)
    kit.rod("Pole crossarm", mat("dark wood"), (POLE[0], POLE[1] - 2.0, 9.0), (POLE[0], POLE[1] + 2.0, 9.0), 0.08, 6)
    pole_y = (POLE[1] - 1.6, POLE[1], POLE[1] + 1.6)
    for y in pole_y:
        insulator("Pole insulator", (POLE[0], y, 9.0), 0.5)
        wire("Feeder down", mat("black"), [Vector((POLE[0], y, 8.4)), Vector((POLE[0] - 0.6, (y + sy1) / 2, 4.5)), Vector((sx1 - 0.3, sy1 + 0.05, 2.75))], 0.015)

    # ---- The pylons and the line: three conductors from the pole east to the station.
    bm = Beams()
    for c in PYLONS:
        lattice(bm, steel, c)
    bm.build("Pylons")
    for c in PYLONS:
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, y = c[0] + sx * 1.3, c[1] + sy * 1.3
            if X0 < x < X1 and Y0 < y < Y1:
                reb.wall(reb.prim("cube", "Pylon leg footprint", None, (x, y, 0.5), (0.35, 0.35, 1.0))).hide_render = True
    hang = []
    for y in (7.0, 10.2, 13.4):
        tops = [(POLE[0], pole_y[(7.0, 10.2, 13.4).index(y)], 8.45)] + [(px, y, 13.0 - 0.95) for px, _ in PYLONS] + [(GATE_X + 4.0, y * 0.5 + 6.0, 4.5)]
        for (px, py, pz) in [(px, y, 13.0) for px, _ in PYLONS]:
            if not (px == PYLONS[0][0] and y == 7.0):
                insulator("Insulator", (px, py, pz))
        for a, b in zip(tops, tops[1:]):
            drop = 0.9 if (Vector(a) - Vector(b)).length > 5 else 0.3
            wire("Conductor", mat("black"), sag(a, b, drop))
    # The broken string on the first pylon: torn off at the bottom, swinging.
    brk = insulator("Broken insulator", (PYLONS[0][0], 7.0, 13.0))
    brk.rotation_euler = (0.35, 0, 0)
    kit.rod("Snapped end", mat("black"), (PYLONS[0][0], 7.0, 12.0), (PYLONS[0][0] - 0.8, 7.2, 11.4), 0.012, 5)
    # The loose jumper on the second pylon, hanging down off the crossarm.
    jpivot = reb.prim("sphere", "Jumper clamp", mat("iron"), (PYLONS[1][0], 7.2, 12.9), (0.06, 0.06, 0.06))
    jpts = [Vector((0.0, 0.0, 0.0)), Vector((0.2, -0.1, -2.0)), Vector((0.4, -0.2, -4.5)), Vector((0.35, -0.15, -7.0)), Vector((0.1, 0.0, -8.6))]
    jw = wire("Loose jumper", mat("black"), jpts, 0.014)
    jw.parent = jpivot
    reb.prim("cube", "Jumper end", mat("steel"), (0.1, 0.0, -8.7), (0.05, 0.05, 0.15)).parent = jpivot

    # ---- The dead deer under the wires, crows on it and on the wire above.
    d = deer("Dead deer", (DEER[0], DEER[1], 0.0), 0.3)
    kit.splat("Deer blood", mat("old blood"), (DEER[0] + 0.2, DEER[1] + 0.3, 0.0), 0.7, seed=4, stretch=(1.5, 1.0), lumps=0.6)
    kit.drag_trail("Deer drag", mat("old blood"), [(13.8, 10.6), (13.0, 10.0), (12.0, 9.5)], width=0.4, seed=6)
    kit.bones("Gnawed bones", (DEER[0] - 1.4, DEER[1] + 0.6, 0.0), spread=0.6, seed=3, skull=False)
    crow_b, crow_w = kit.crow("Crow on the deer", (DEER[0] + 0.1, DEER[1] - 0.1, 0.48), heading=2.0)
    kit.crow("Crow in the grass", (DEER[0] + 0.9, DEER[1] - 0.5, 0.0), heading=3.6)
    wire_z = lambda x: 13.0 - 0.95 - 0.9 * 4 * ((x - PYLONS[0][0]) / 9.0) * (1 - (x - PYLONS[0][0]) / 9.0)
    for i, x in enumerate((10.0, 10.6, 12.6)):
        kit.crow(f"Crow on the wire {i}", (x, 10.2, wire_z(x) + 0.01), heading=1.57 + (0.3 if i % 2 else -0.2))
    reb.wall(reb.prim("cube", "Deer footprint", None, (DEER[0], DEER[1], 0.3), (1.9, 1.0, 0.6))).hide_render = True
    # Dale's fight on the track: the hat with blood in it, the torch smashed, flattened grass, blood back west.
    reb.prim("sphere", "Hard hat", hat_m, (8.6, 6.4, 0.1), (0.3, 0.26, 0.2), rot=(math.pi, 0, 0.4), segments=16)
    reb.prim("cyl", "Hat brim", hat_m, (8.6, 6.4, 0.11), (0.34, 0.3, 0.02), rot=(0, 0, 0.4), segments=16)
    kit.splat("Blood in the hat", mat("blood"), (8.6, 6.4, 0.115), 0.08, seed=8)
    kit.text("Hat words", "ARKLAY POWER", mat("black"), (8.6, 6.4, 0.003), size=0.04, rot=(0, 0, 0.4))
    reb.prim("cyl", "Torch", mat("black"), (9.4, 7.3, 0.04), (0.07, 0.07, 0.3), rot=(math.pi / 2, 0, 1.9), segments=12)
    kit.shards("Torch glass", (9.55, 7.0, 0.0), spread=0.25, count=8, seed=5)
    kit.splat("Where he fought", reb.mat_plain("Flattened grass", (0.13, 0.12, 0.05), 0.9), (9.0, 6.8, 0.002), 0.9, seed=9, stretch=(1.4, 1.0), lumps=0.5)
    kit.drag_trail("Blood back to the door", mat("old blood"), [(8.8, 6.7), (6.5, 6.8), (4.2, 6.7), (2.0, 6.65)], width=0.18, seed=11)
    for i in range(12):
        t = i / 11
        x, y = 13.5 - 4.0 * t, 4.0 + 2.3 * t + 0.2 * math.sin(i)
        kit.splat(f"Paw print {i}", mat("mud"), (x + (0.1 if i % 2 else -0.1), y, 0.025), 0.05, seed=70 + i, stretch=(1.0, 1.2), lumps=0.3)

    # ---- The north fence, the chain-link fence and gate at the east end.
    for i in range(10):
        x = X0 + 0.5 + i * 2.0
        kit.rod("Fence post", mat("dark wood"), (x, Y0 - 0.25, -0.2), (x, Y0 - 0.25, 1.1), 0.05)
    for z in (0.4, 0.75, 1.05):
        kit.rod("Fence wire", mat("iron"), (X0 - 1.0, Y0 - 0.25, z), (GATE_X, Y0 - 0.25, z), 0.006, 4)
    reb.wall(reb.prim("cube", "North fence", None, ((X0 + X1) / 2, Y0 - 0.25, 0.5), (X1 - X0 + 2, 0.2, 1.0))).hide_render = True
    for y in (6.0, 8.0):
        reb.wall(kit.rod("Gate post", mat("rust"), (GATE_X, y, 0), (GATE_X, y, 2.0), 0.05), "circle")
    for y0, y1 in ((Y0 - 0.25, 6.0), (8.0, 13.2)):
        reb.prim("cube", "Chain-link fence", link_m, (GATE_X, (y0 + y1) / 2, 0.95), (0.03, y1 - y0, 1.8))
        kit.rod("Fence rail", mat("rust"), (GATE_X, y0, 1.85), (GATE_X, y1, 1.85), 0.025)
    reb.wall(reb.prim("cube", "East fence north", None, (GATE_X, (Y0 + 6.0) / 2, 0.5), (0.2, 6.0 - Y0 + 0.5, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "East fence south", None, (GATE_X, (8.0 + Y1) / 2, 0.5), (0.2, Y1 - 8.0 + 0.5, 1.0))).hide_render = True
    gate_pivot = reb.prim("sphere", "Gate hinge", mat("iron"), (GATE_X, 6.0, 0.95), (0.05, 0.05, 0.05))
    reb.prim("cube", "Line gate", link_m, (0.0, 0.62, 0.0), (0.03, 1.2, 1.8)).parent = gate_pivot
    gate_pivot.rotation_euler = (0, 0, -1.1)
    reb.prim("cube", "Gate sign", mat("white paint"), (GATE_X + 0.02, 8.3, 1.4), (0.03, 0.5, 0.35))
    kit.text("Gate sign words", "LINE TRACK", mat("red paint"), (GATE_X - 0.01, 8.3, 1.46), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.text("Gate sign words 2", "STAFF ONLY", mat("red paint"), (GATE_X - 0.01, 8.3, 1.36), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    # Beyond the gate: the gondola station's slab, the wheel house, the car, the booth.
    reb.prim("cube", "Platform slab", kit.dirtied(mat("concrete"), 0.7, scale=1.2), (27.4, 7.5, -0.15), (15.2, 11.8, 0.3))
    for x in (OFF + 2.5, OFF + 6.0):
        for y in (9.0, 12.6):
            kit.rod("Wheel house post", mat("rust"), (x, y, 0), (x, y, 4.2), 0.09)
    reb.prim("cube", "Wheel house roof", mat("tin"), (OFF + 4.25, 10.8, 4.3), (4.3, 4.4, 0.08), rot=(0.05, 0, 0))
    reb.prim("cyl", "Bullwheel", mat("rust"), (OFF + 4.25, 11.4, 3.1), (3.2, 3.2, 0.18), segments=32)
    reb.prim("cube", "Gearbox", mat("green paint"), (OFF + 4.25, 11.4, 0.55), (1.6, 1.2, 1.1), bevel=0.04)
    reb.prim("cube", "Gondola car", reb.mat_plain("Car paint", (0.32, 0.05, 0.03), 0.5), (OFF + 8.3, 11.8, 1.25), (2.6, 1.6, 2.1), bevel=0.25)
    kit.rod("Car hanger", mat("iron"), (OFF + 8.3, 11.8, 2.3), (OFF + 8.3, 11.8, 3.45), 0.06)
    hub, grip = Vector((OFF + 4.25, 11.4, 3.1)), Vector((OFF + 8.3, 11.8, 3.45))
    kit.rod("Haul cable", mat("iron"), hub + Vector((1.55, 0, 0)), grip, 0.022, 6)
    kit.rod("Haul cable on down", mat("iron"), grip, (OFF + 9.0, 120.0, -70.0), 0.022, 6)
    kit.rod("Haul cable, return", mat("iron"), hub - Vector((1.55, 0, 0)), (OFF + 5.0, 120.0, -70.0), 0.022, 6)
    reb.prim("cube", "Booth", kit.boards("Booth boards", (0.2, 0.22, 0.17), width=0.16, grime=0.7), (OFF + 14.1, 3.8, 1.2), (3.2, 2.6, 2.4))
    reb.prim("cube", "Booth roof", mat("tin"), (OFF + 14.1, 3.8, 2.55), (3.8, 3.2, 0.08))
    for x in (OFF + 2.2, OFF + 6.0, OFF + 10.0, OFF + 13.0):
        kit.rod("Station rail post", mat("rust"), (x, 13.15, 0), (x, 13.15, 1.1), 0.03)
    kit.rod("Station rail", mat("rust"), (OFF + 2.0, 13.15, 1.1), (OFF + 17.0, 13.15, 1.1), 0.025)

    # ---- The forest round the strip; the long grass where the adders are.
    def keep_out(x, y):
        if X0 - 6 < x < X1 + 1.5 and Y0 - 1.6 < y < Y1 + 3.5:
            return True
        if GATE_X - 1.0 < x < 37.0 and y > -1.0:
            return True
        if x > GATE_X - 1.0 and 12.5 < y < 15.0:
            return True
        if SWITCH[0] - 3.5 < x < X0 + 1.0 and -1.0 < y < 9.5:
            return True
        return any((Vector((x, y)) - Vector(c[:2])).length < 4.5 for c in CAMS)
    kit.forest(rng, height, keep_out, (-24, -16, 58, 40), count=170, spacing=1.8, ferns=40, needles=900, dead=0.1)

    def long_grass(r):
        while True:
            x, y = r.uniform(X0 - 6, X1 + 0.5), r.uniform(Y0 - 1.5, Y1 + 3)
            if not (TRACK[0] - 0.1 < y < TRACK[1] + 0.1) and (Vector((x, y)) - Vector(DEER)).length > 0.9:
                return x, y
    grass = kit.meadow(rng, 2600, long_grass, height)
    grass.scale = (1, 1, 1.9)
    dry = kit.meadow(rng, 900, long_grass, height, mat("dead grass"))
    dry.scale = (1, 1, 2.4)

    # ---- Light: the low sun from the south-west, long shadows of the pylons across the track.
    low_sun(232, 20, 6.0)

    anim = kit.Anim(16)
    anim.swing(brk, axis=0, degrees=12)
    anim.custom(lambda k: setattr(jpivot, "rotation_euler", (math.radians(4) * math.sin(anim.phase(k)), math.radians(3) * math.cos(anim.phase(k)), 0)))
    anim.sway(grass, amount=0.06)
    anim.sway(dry, amount=0.07)
    anim.flies((DEER[0], DEER[1], 0.45), count=10, radius=0.5)
    anim.bob(crow_b, height=0.05, speed=2)

    # ---- What the game needs.
    room.door("switch", (X0, SWITCH_DOOR[0] - 0.1, X0 + 0.6, SWITCH_DOOR[1] + 0.1), arrive=(2.5, 6.65), face=(1, 0), walk=False, touch=False)
    room.door("platform", (X1 - 0.6, TRACK[0], X1, TRACK[1]), arrive=(17.3, 7.0), face=(-1, 0))
    room.check((DEER[0] - 1.0, DEER[1] - 0.8, DEER[0] + 1.0, DEER[1] - 0.4), "A deer, torn open. The dogs have been at it.\nNot long ago. The flies are thick.")
    room.check((8.1, 6.0, 9.1, 6.9), "A hard hat. ARKLAY POWER. Upside down, with blood in it.")
    room.check((9.0, 6.9, 9.9, 7.7), "A torch, smashed. The grass is flattened all round here.\nSomeone fought for his life.")
    room.check((5.6, 8.6, 7.4, 9.4), "The line's dead. A string of insulators has torn loose up there.\nIt swings in the wind.")
    room.check((X1 - 1.4, 8.0, X1, 9.0), "LINE TRACK. STAFF ONLY. The gondola station's through the gate.")
    room.check((X0, 5.2, X0 + 0.8, SWITCH_DOOR[0] - 0.1), "The switch house. A handprint in blood on the door frame.")
    room.entry = "The power line. Not a hum from it."
    room.export(anim)


build()
