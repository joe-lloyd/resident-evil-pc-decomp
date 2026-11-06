"""The junction chamber, where the old silver mine's ways meet.

What it tells: this is the heart of the old workings. The adit comes in
from the west. In the north wall the lift's cage waits at the bottom of
its shaft, its cable going up into the dark to the head house on the
summit. Along the east wall the pump house machinery that once kept the
lower levels dry stands silent, its knife switch thrown off and the power
lamp on its switch panel dark: the station's generator is not running. Its
suction pipe runs down into the flooded way: a decline in the south that
goes straight down under black water, the old gallery somewhere beneath.
The pipe's intake hung on a float, to keep it up out of the silt; the
float is split open and sunk, its arm bent down, and the intake lies
choked on the bottom. The water is still coming up. The web spinners breed
here: the roof is hung with their egg sacs, some split, and the corners
are choked with web. A dog that came down after something is wrapped
against the pump. Hal's drops of blood run from the adit to the water's
edge and into it: he went down the flooded way to hide. He is out there
now, across the water toward the gallery: slumped on an ore cart that
stands on a heap of fallen rock above the flood, his lantern burning low
beside him, the gondola's key glinting on its chain at his neck. He is too
far out to reach. An empty ore cart was shoved off the rails into the
south-west corner long ago.

Metres: the floor is x 1.0-13.0, y 1.0-10.0, the rock roof about 4 m up.
The adit comes in through the west wall at y 4.6-7.0. The lift cage is in
the north wall at x 6.0-8.4, its gate facing south. The pump machinery is
along the east wall, x 10.4-13.0, y 2.0-7.6. The flooded way goes down
through the south wall at x 4.2-7.8: the floor slopes from y 7.6 and the
water's edge is at y 8.3; beyond it the floor is gone under the water.
The float lies sunk at x 7.9, y 9.4, on its arm from the pipe. The power
lamp is on the switch panel at y 8.1, 1.5 up. Hal's cart stands in the
flooded way at x 6.0, y 12.4, four metres past the water's edge, off the
floor. The pushed-aside cart is at x 2.15, y 8.55.

Once the generator runs ("generator-on"), the power lamp is lit red.

Moving: the water in the sump rippling and lapping higher; the lamps on
the cable flickering; a split egg sac turning on its thread; Hal's
lantern guttering.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Vector, noise  # noqa: E402
import bpy  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 13.0, 1.0, 10.0, 4.0
ADIT = (4.6, 7.0, 2.9)          # y0, y1 in the west wall, height
CAGE = (6.0, 8.4, Y0 - 1.7, Y0 + 0.05)   # x0, x1, y0, y1 of the cage, set into the north wall
DECLINE = (4.2, 7.8)            # x0, x1 of the flooded way in the south wall
EDGE = 8.3                      # where the water starts
WATER_Z = -0.32
FLOAT = (7.9, 9.4)              # the pump intake's float, split and sunk
HAL_CART = (6.0, 12.4, -0.5)    # Hal's cart out in the flooded way: x, y, the height of its wheels


def rock_face(name, m, origin, u, v, nu, nv, out, depth=0.25, seed=0):
    """A lumpy rock surface over the rectangle origin + s*u + t*v, pushed back along `out` by noise."""
    o, u, v, out = Vector(origin), Vector(u), Vector(v), Vector(out).normalized()
    verts, faces = [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            p = o + u * (i / nu) + v * (j / nv)
            d = depth * (0.6 + noise.noise(p * 0.9 + Vector((seed, 0, 0))) + 0.35 * noise.noise(p * 3.0 + Vector((0, seed, 0))))
            verts.append(tuple(p + out * max(-0.03, d)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return reb.mesh_object(name, verts, faces, m)


def web_sheet(name, corner, a, b, size, rng, strands=9):
    """A thick web across a corner: fans of silk from `corner` along directions a and b, in one mesh."""
    verts, faces = [], []
    c = Vector(corner)
    a, b = Vector(a).normalized(), Vector(b).normalized()
    side = a.cross(b).normalized() * 0.006
    for i in range(strands):
        t = i / (strands - 1)
        d = (a * (1 - t) + b * t).normalized() * size * rng.uniform(0.75, 1.0)
        k = len(verts)
        verts += [tuple(c), tuple(c + d), tuple(c + d + side)]
        faces.append((k, k + 1, k + 2))
    for r in (0.3, 0.55, 0.8):
        for i in range(strands - 1):
            p = c + (a * (1 - i / (strands - 1)) + b * (i / (strands - 1))).normalized() * size * r
            q = c + (a * (1 - (i + 1) / (strands - 1)) + b * ((i + 1) / (strands - 1))).normalized() * size * r
            k = len(verts)
            verts += [tuple(p), tuple(q), tuple(q + Vector((0, 0, -0.01)))]
            faces.append((k, k + 1, k + 2))
    ob = reb.mesh_object(name, verts, faces, mat("web"), smooth=False)
    # A haze of silk filling the corner, mostly see-through.
    reb.mesh_object(f"{name} haze", [tuple(c), tuple(c + a * size * 0.75), tuple(c + b * size * 0.75)], [(0, 1, 2)], haze_material(), smooth=False).visible_shadow = False
    return ob


_haze = []


def haze_material():
    """Web silk seen as a film: mostly transparent, pale where it catches the light."""
    if _haze:
        return _haze[0]
    m, nodes, links, bsdf = reb.nodes_material("Web haze")
    bsdf.inputs["Base Color"].default_value = (0.7, 0.7, 0.68, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.22
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])
    _haze.append(m)
    return m


def rails(name, path, sleepers_m, rail_m, gauge=0.6):
    """Narrow-gauge track along `path` [(x, y)]: rails and sleepers, two meshes."""
    sv, sf, rv, rf = [], [], [], []
    pts = [Vector((x, y, 0.0)) for x, y in path]
    for a, b in zip(pts, pts[1:]):
        d = b - a
        side = Vector((-d.y, d.x, 0)).normalized()
        n = max(1, int(d.length / 0.55))
        for i in range(n):
            c = a.lerp(b, (i + 0.5) / n)
            reb.box(sv, sf, (c.x, c.y, 0.04), (1.0, 0.16, 0.08), math.atan2(side.y, side.x))
        for s in (-1, 1):
            o = side * gauge / 2 * s
            reb.box(rv, rf, ((a + b) / 2 + o + Vector((0, 0, 0.11))).to_tuple(), (d.length + 0.02, 0.05, 0.07), math.atan2(d.y, d.x))
    reb.mesh_object(f"{name} sleepers", sv, sf, sleepers_m, smooth=False)
    return reb.mesh_object(f"{name} rails", rv, rf, rail_m, smooth=False)


def ore_cart(name, m, at, yaw, roll=0.0, load=True):
    """A side-tipping ore cart on four wheels (as the mine entrance builds them), standing at `at`."""
    parts = [
        reb.prim("cube", "tub", m, (0, 0, 0.62), (1.1, 0.8, 0.6), bevel=0.04),
        reb.prim("cube", "chassis", mat("iron"), (0, 0, 0.27), (1.2, 0.6, 0.1)),
    ]
    if load:
        parts.append(reb.prim("cube", "load", mat("rock"), (0, 0, 0.9), (0.98, 0.68, 0.08)))
    for dx in (-0.38, 0.38):
        for dy in (-0.3, 0.3):
            parts.append(reb.prim("cyl", "wheel", mat("iron"), (dx, dy, 0.17), (0.34, 0.34, 0.05), rot=(math.pi / 2, 0, 0), segments=12))
    for dx in (-0.62, 0.62):
        parts.append(reb.prim("cube", "buffer", mat("iron"), (dx, 0, 0.3), (0.06, 0.3, 0.12)))
    for p in parts:
        bpy.ops.object.select_all(action="DESELECT")
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob = kit.join(name, parts)
    ob.rotation_euler = (roll, 0, yaw)
    ob.location = at
    return ob


def build():
    rng = random.Random(97)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("rock")
    room.camera((1.5, 1.5, 2.6), (8.5, 7.0, 0.2), 200, "high in the north-west corner: the pump house, the water coming up the flooded way")
    room.camera((12.5, 9.5, 2.6), (5.5, 3.0, 0.9), 200, "high in the south-east corner: the lift cage in its shaft, the adit coming in, the egg sacs")
    room.camera((9.6, 1.4, 2.6), (4.8, 8.6, 0.0), 200, "high on the north wall west of the pump: the flooded way down, Hal's drops into the water")
    room.camera((1.5, 9.4, 2.6), (9.5, 3.5, 0.9), 200, "high in the south-west corner: the pump machinery along the east wall, the wrapped dog")
    room.camera((7.6, 7.6, 2.3), (7.0, 1.0, 1.3), 195, "from the water's edge: the cage, its gate, the cable up into the dark")

    rock = kit.dirtied(mat("wet rock"), 0.55, scale=0.8)
    floor_m = reb.mat_surface("Chamber floor", [(0.0, (0.03, 0.026, 0.022)), (0.5, (0.075, 0.065, 0.052)), (1.0, (0.12, 0.1, 0.08))], scale=1.6, rough=0.55, bump=0.7)
    timber = kit.dirtied(reb.mat_wood("Mine timber", (0.14, 0.095, 0.055)), 0.7)
    rust = mat("rust")
    iron = mat("iron")
    green = kit.dirtied(mat("green paint"), 0.6)
    silk = reb.mat_plain("Silk", (0.68, 0.68, 0.66), 0.6)
    sac_m = reb.mat_surface("Egg sac", [(0.0, (0.42, 0.4, 0.33)), (0.7, (0.62, 0.6, 0.52)), (1.0, (0.35, 0.3, 0.18))], scale=18, rough=0.5, bump=0.6)
    water = mat("water")

    # ---- The rock: walls round the floor with the three ways out cut through; the roof; the floor and the decline.
    a0, a1, ah = ADIT
    rock_face("West rock, north", rock, (X0, Y0 - 0.5, -0.1), (0, a0 - Y0 + 0.5, 0), (0, 0, H + 0.6), 14, 18, (-1, 0, 0), seed=1)
    rock_face("West rock, south", rock, (X0, a1, -0.1), (0, Y1 - a1 + 0.6, 0), (0, 0, H + 0.6), 14, 18, (-1, 0, 0), seed=2)
    rock_face("West rock, over the adit", rock, (X0, a0, ah), (0, a1 - a0, 0), (0, 0, H + 0.5 - ah), 10, 6, (-1, 0, 0), seed=3)
    rock_face("East rock", rock, (X1, Y0 - 0.5, -0.1), (0, Y1 - Y0 + 1.1, 0), (0, 0, H + 0.6), 36, 18, (1, 0, 0), seed=4)
    c0, c1 = CAGE[0], CAGE[1]
    rock_face("North rock, west", rock, (X0 - 0.5, Y0, -0.1), (c0 - X0 + 0.5, 0, 0), (0, 0, H + 0.6), 20, 18, (0, -1, 0), seed=5)
    rock_face("North rock, east", rock, (c1, Y0, -0.1), (X1 - c1 + 0.5, 0, 0), (0, 0, H + 0.6), 18, 18, (0, -1, 0), seed=6)
    d0, d1 = DECLINE
    rock_face("South rock, west", rock, (X0 - 0.5, Y1, -2.0), (d0 - X0 + 0.5, 0, 0), (0, 0, H + 2.6), 14, 22, (0, 1, 0), seed=7)
    rock_face("South rock, east", rock, (d1, Y1, -2.0), (X1 - d1 + 0.5, 0, 0), (0, 0, H + 2.6), 16, 22, (0, 1, 0), seed=8)
    rock_face("South rock, over the way down", rock, (d0, Y1, 2.3), (d1 - d0, 0, 0), (0, 0, H + 0.3 - 2.3), 12, 6, (0, 1, 0), seed=9)
    rock_face("Roof", rock, (X0 - 0.5, Y0 - 0.5, H), (X1 - X0 + 1.0, 0, 0), (0, Y1 - Y0 + 1.0, 0), 40, 30, (0, 0, 1), depth=0.4, seed=10)
    # The floor: flat where she walks, sloping down into the water in the south.
    fv, ff = [], []
    nx, ny = 24, 22
    for j in range(ny + 1):
        y = Y0 - 0.5 + (Y1 + 3.0 - Y0 + 0.5) * j / ny
        for i in range(nx + 1):
            x = X0 - 0.5 + (X1 - X0 + 1.0) * i / nx
            z = 0.0
            if y > 7.6 and d0 - 0.6 < x < d1 + 0.6:
                z = -(y - 7.6) * 0.42 * min(1.0, min(x - d0 + 0.6, d1 + 0.6 - x) / 0.6)
            elif y > Y1:
                z = 0.6
            fv.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            ff.append((a, a + 1, a + nx + 2, a + nx + 1))
    reb.mesh_object("Floor", fv, ff, floor_m)
    # The way down: an arch going on south under the water, black beyond.
    down = kit.tunnel("Flooded way", rock, [(6.0, Y1 + 0.05), (6.0, Y1 + 6.0)], width=3.8, height=3.4, rough=0.12, seed=12)
    down.location.z = -1.1
    reb.prim("cube", "Down into the black", mat("black"), (6.0, Y1 + 5.5, 0.0), (5.0, 0.2, 5.0))
    pool = reb.prim("cube", "Sump water", water, (6.0, EDGE + 4.0, WATER_Z), (6.4, 8.0, 0.02))
    # Scum and wreckage riding on it, so the black reads as water: they rise with it.
    afloat = []
    for k, (x, y, r) in enumerate(((5.0, 8.9, 0.35), (6.9, 9.4, 0.5), (5.6, 10.3, 0.3))):
        afloat.append(kit.splat(f"Scum {k}", reb.mat_plain("Scum", (0.09, 0.09, 0.05), 0.5), (x, y, WATER_Z + 0.012), r, seed=50 + k, stretch=(1.6, 0.7), lumps=0.6))
    for k, (x, y, yaw, ln) in enumerate(((4.9, 9.3, 0.4, 1.3), (6.6, 10.0, 2.2, 0.9))):
        afloat.append(reb.prim("cube", f"Floating plank {k}", timber, (x, y, WATER_Z + 0.03), (ln, 0.16, 0.05), rot=(0, 0, yaw)))
    afloat.append(reb.prim("sphere", "Floating hard hat", mat("yellow paint"), (7.2, 8.9, WATER_Z + 0.04), (0.28, 0.25, 0.16), rot=(math.pi, 0.3, 0)))
    for ob in afloat:
        ob.parent = pool
        ob.matrix_parent_inverse = pool.matrix_world.inverted()
    under = reb.prim("cube", "Under the water", reb.mat_plain("Deep", (0.004, 0.005, 0.005), 0.9), (6.0, EDGE + 4.0, WATER_Z - 0.6), (6.4, 8.0, 0.02))

    # Once the pump runs (day/events.ts "drain"): the water down the way,
    # the decline showing wet below where it stood, its wreckage riding down.
    def drained(done):
        for ob in (pool, under):
            ob.location.z += -1.6 if done else 1.6
    room.state("drain", drained)
    # The adit coming in from the west: its arch, a lamp burning down it.
    kit.tunnel("Adit in", rock, [(X0 + 0.3, (a0 + a1) / 2), (X0 - 5.0, (a0 + a1) / 2)], width=a1 - a0 + 0.4, height=ah + 0.3, rough=0.12, seed=13, floor_m=floor_m)
    reb.prim("cube", "Adit dark", mat("black"), (X0 - 5.5, (a0 + a1) / 2, 1.5), (0.2, 4.0, 4.0))
    # A lamp burning a little way down the adit: the way back.
    adit_glow = reb.mat_emit("Adit lamp glow", (1.0, 0.72, 0.4), 12)
    reb.prim("sphere", "Adit lamp", adit_glow, (X0 - 2.2, (a0 + a1) / 2, 2.3), (0.08, 0.08, 0.11), segments=10)
    kit.rod("Adit lamp flex", mat("black"), (X0 - 2.2, (a0 + a1) / 2, 2.38), (X0 - 2.2, (a0 + a1) / 2, ah + 0.2), 0.007, 4)
    reb.point("Adit lamp light", (X0 - 2.2, (a0 + a1) / 2, 2.2), 35, (1.0, 0.68, 0.38), 0.05)
    for y in (a0 - 0.1, a1 + 0.1):
        kit.rod("Adit set post", timber, (X0 + 0.15, y, 0), (X0 + 0.15, y, ah), 0.11, 6)
    kit.rod("Adit set cap", timber, (X0 + 0.15, a0 - 0.3, ah), (X0 + 0.15, a1 + 0.3, ah), 0.12, 6)

    # ---- The lift: its cage at the foot of the shaft, the guides, the cable up into the dark.
    cy0, cy1 = CAGE[2], CAGE[3]
    rock_face("Shaft west", rock, (c0, cy0 - 0.4, -0.1), (0, cy1 - cy0 + 0.5, 0), (0, 0, H + 6.0), 6, 24, (-1, 0, 0), depth=0.15, seed=14)
    rock_face("Shaft east", rock, (c1, cy0 - 0.4, -0.1), (0, cy1 - cy0 + 0.5, 0), (0, 0, H + 6.0), 6, 24, (1, 0, 0), depth=0.15, seed=15)
    rock_face("Shaft back", rock, (c0 - 0.3, cy0 - 0.4, -0.1), (c1 - c0 + 0.6, 0, 0), (0, 0, H + 6.0), 8, 24, (0, -1, 0), depth=0.15, seed=16)
    reb.prim("cube", "Shaft dark", mat("black"), ((c0 + c1) / 2, (cy0 + cy1) / 2, H + 6.0), (c1 - c0 + 0.6, cy1 - cy0 + 0.8, 0.2))
    for x in (c0 + 0.15, c1 - 0.15):
        for y in (cy0 + 0.15, cy1 - 0.15):
            kit.rod("Shaft guide", timber, (x, y, 0), (x, y, H + 6.0), 0.08, 6)
    for z in (0.05, 2.35):
        reb.prim("cube", "Collar beam", timber, ((c0 + c1) / 2, cy1 + 0.05, z + 0.08 if z > 1 else 0.08), (c1 - c0 + 0.5, 0.25, 0.22))
    for x in (c0 - 0.12, c1 + 0.12):
        kit.rod("Collar post", timber, (x, cy1 + 0.05, 0), (x, cy1 + 0.05, 2.5), 0.12, 6)
    gx0, gx1 = c0 + 0.25, c1 - 0.25
    reb.prim("cube", "Cage floor", iron, ((gx0 + gx1) / 2, (cy0 + cy1) / 2, 0.06), (gx1 - gx0, cy1 - cy0 - 0.2, 0.12))
    reb.prim("cube", "Cage roof", iron, ((gx0 + gx1) / 2, (cy0 + cy1) / 2, 2.25), (gx1 - gx0, cy1 - cy0 - 0.2, 0.08))
    for x in (gx0, gx1):
        for y in (cy0 + 0.1, cy1 - 0.1):
            kit.rod("Cage corner", rust, (x, y, 0.1), (x, y, 2.25), 0.03, 6)
    # Sides and back of open bar-work, so the shaft's rock shows through behind: one object.
    bars = []
    for x in (gx0, gx1):
        for k in range(1, 6):
            y = cy0 + 0.1 + (cy1 - cy0 - 0.2) * k / 6
            bars.append(kit.rod("Cage bar", rust, (x, y, 0.12), (x, y, 2.2), 0.012, 4))
    for k in range(1, 8):
        x = gx0 + (gx1 - gx0) * k / 8
        bars.append(kit.rod("Cage bar", rust, (x, cy0 + 0.1, 0.12), (x, cy0 + 0.1, 2.2), 0.012, 4))
    for z in (0.12, 1.1, 2.2):
        bars.append(kit.rod("Cage rail", rust, (gx0, cy0 + 0.1, z), (gx1, cy0 + 0.1, z), 0.025, 6))
        for x in (gx0, gx1):
            bars.append(kit.rod("Cage rail", rust, (x, cy0 + 0.1, z), (x, cy1 - 0.1, z), 0.025, 6))
    kit.join("Cage bars", bars)
    gate = []
    for k in range(9):
        x = gx0 + (gx1 - gx0) * k / 8
        gate.append(kit.rod("Gate bar", rust, (x, cy1 - 0.08, 0.15), (x, cy1 - 0.08, 2.0), 0.012, 4))
    for z in (0.3, 1.0, 1.7):
        for k in range(8):
            xa = gx0 + (gx1 - gx0) * k / 8
            xb = gx0 + (gx1 - gx0) * (k + 1) / 8
            gate.append(kit.rod("Gate lattice", rust, (xa, cy1 - 0.08, z - 0.15), (xb, cy1 - 0.08, z + 0.15), 0.008, 4))
            gate.append(kit.rod("Gate lattice", rust, (xa, cy1 - 0.08, z + 0.15), (xb, cy1 - 0.08, z - 0.15), 0.008, 4))
    gate_ob = kit.join("Cage gate", gate)
    reb.mask(gate_ob)
    kit.rod("Hoist cable", iron, ((gx0 + gx1) / 2, (cy0 + cy1) / 2, 2.3), ((gx0 + gx1) / 2, (cy0 + cy1) / 2, H + 6.0), 0.025, 6)
    kit.rod("Counterweight cable", iron, (gx1 + 0.18, cy0 + 0.25, 1.2), (gx1 + 0.18, cy0 + 0.25, H + 6.0), 0.02, 6)
    reb.prim("cube", "Counterweight", iron, (gx1 + 0.18, cy0 + 0.25, 0.9), (0.18, 0.18, 0.6))
    cage_glow = reb.mat_emit("Cage lamp glow", (1.0, 0.75, 0.45), 6)
    reb.prim("sphere", "Cage lamp", cage_glow, ((gx0 + gx1) / 2, (cy0 + cy1) / 2, 2.15), (0.08, 0.08, 0.08))
    cage_light = reb.point("Cage lamp light", ((gx0 + gx1) / 2, (cy0 + cy1) / 2, 2.05), 10, (1.0, 0.72, 0.42), 0.05)
    reb.prim("cube", "Lift sign", mat("white paint"), (c1 + 0.55, Y0 + 0.08, 1.6), (0.6, 0.02, 0.35))
    kit.text("Lift sign words", "LIFT\nTO SURFACE", mat("black"), (c1 + 0.55, Y0 + 0.095, 1.6), size=0.07, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Call box", mat("yellow paint"), (c0 - 0.4, Y0 + 0.1, 1.3), (0.25, 0.14, 0.35), bevel=0.02)
    reb.prim("cyl", "Call button", mat("red paint"), (c0 - 0.4, Y0 + 0.18, 1.33), (0.07, 0.07, 0.03), rot=(math.pi / 2, 0, 0), segments=10)
    kit.rod("Bell wire", mat("black"), (c0 - 0.4, Y0 + 0.1, 1.48), (c0 - 0.4, Y0 + 0.1, H), 0.008, 4)

    # ---- The pump house along the east wall: motor, flywheel, pump, the pipes into the sump; the switch, off.
    reb.prim("cube", "Pump bed", mat("concrete"), (11.8, 4.6, 0.15), (2.0, 4.6, 0.3))
    reb.wall(reb.prim("cube", "Pump footprint", None, (11.8, 4.6, 0.5), (2.2, 4.8, 1.0))).hide_render = True
    motor = reb.prim("cyl", "Pump motor", green, (11.9, 3.2, 0.95), (1.1, 1.1, 1.4), rot=(math.pi / 2, 0, 0), segments=20)
    reb.mask(motor)
    for k in range(6):
        reb.prim("cube", "Motor fin", green, (11.9, 2.7 + k * 0.2, 1.52), (1.15, 0.03, 0.12))
    reb.prim("cube", "Motor plate", mat("steel"), (11.33, 3.2, 1.0), (0.01, 0.3, 0.18))
    fly = reb.prim("cyl", "Flywheel", iron, (11.9, 4.2, 1.05), (1.6, 1.6, 0.16), rot=(math.pi / 2, 0, 0), segments=28)
    for k in range(6):
        a = math.pi * k / 3
        kit.rod("Flywheel spoke", iron, (11.9, 4.18, 1.05), (11.9 + math.cos(a) * 0.72, 4.18, 1.05 + math.sin(a) * 0.72), 0.04, 6)
    pump = reb.prim("cube", "Pump casing", green, (11.9, 5.4, 0.85), (1.3, 1.6, 1.1), bevel=0.08)
    reb.mask(pump)
    reb.prim("cyl", "Pump volute", green, (11.9, 5.4, 0.85), (1.4, 1.4, 0.7), rot=(math.pi / 2, 0, 0), segments=20)
    pipe = [(11.3, 6.1, 0.6), (10.6, 6.7, 0.6), (8.8, 7.6, 0.4), (7.6, 8.4, -0.1), (7.0, 9.2, -0.9)]
    for a, b in zip(pipe, pipe[1:]):
        kit.rod("Suction pipe", rust, a, b, 0.14, 12)
    for p in pipe[1:-1]:
        reb.prim("sphere", "Pipe elbow", rust, p, (0.32, 0.32, 0.32), segments=12)
    for (x, y) in ((10.3, 6.85), (9.5, 7.25), (8.6, 7.7)):
        reb.wall(reb.prim("cube", "Pipe footprint", None, (x, y, 0.5), (0.7, 0.4, 1.0))).hide_render = True
    # The intake on the pipe's end, and the float that held it up off the
    # bottom: its arm bent down from a clamp on the pipe, the float split open
    # and sunk to its shoulders, so the intake lies choked in the silt.
    reb.prim("cyl", "Intake strainer", rust, (7.0, 9.2, -0.98), (0.36, 0.36, 0.22), segments=14)
    reb.prim("cube", "Float arm clamp", iron, (7.33, 8.78, -0.44), (0.2, 0.2, 0.16), rot=(0, 0, 0.9))
    fx, fy = FLOAT
    float_m = kit.dirtied(mat("red paint"), 0.65, scale=6)
    kit.rod("Float arm", rust, (7.38, 8.8, -0.4), (7.62, 9.08, -0.3), 0.03, 6)
    kit.rod("Float arm, bent down", rust, (7.62, 9.08, -0.3), (fx - 0.12, fy - 0.08, -0.36), 0.03, 6)
    reb.prim("sphere", "Split float", float_m, (fx, fy, -0.44), (0.56, 0.56, 0.48), rot=(0.35, 0.2, 0.6), segments=16)
    reb.prim("cube", "Float split", mat("black"), (fx + 0.03, fy - 0.03, -0.28), (0.11, 0.52, 0.26), rot=(0.35, 0.2, 0.6))
    reb.prim("cube", "Float seam", rust, (fx, fy, -0.44), (0.58, 0.035, 0.035), rot=(0.35, 0.2, 0.6))
    scum = kit.splat("Scum round the float", reb.mat_plain("Float scum", (0.12, 0.1, 0.05), 0.4), (fx, fy, WATER_Z + 0.012), 0.36, seed=61, stretch=(1.3, 0.9), lumps=0.5)
    scum.parent = pool
    scum.matrix_parent_inverse = pool.matrix_world.inverted()
    # The power lamp on the switch panel: dark until the station's generator runs.
    lens_off = reb.mat_plain("Power lamp, dark", (0.09, 0.012, 0.01), 0.25)
    lens_on = reb.mat_emit("Power lamp, lit", (1.0, 0.12, 0.05), 40)
    reb.prim("cyl", "Power lamp bezel", iron, (X1 - 0.155, 8.1, 1.52), (0.17, 0.17, 0.05), rot=(0, math.pi / 2, 0), segments=14)
    lens = reb.prim("sphere", "Power lamp lens", lens_off, (X1 - 0.18, 8.1, 1.52), (0.12, 0.12, 0.12), segments=12)
    power_glow = reb.point("Power lamp light", (X1 - 0.32, 8.1, 1.52), 4, (1.0, 0.15, 0.06), 0.03)
    power_glow.hide_render = True

    def power(on):
        lens.data.materials[0] = lens_on if on else lens_off
        power_glow.hide_render = not on
    room.state("generator-on", power)
    kit.rod("Discharge pipe", rust, (11.9, 5.4, 1.4), (12.6, 6.4, 2.0), 0.11, 10)
    kit.rod("Discharge pipe", rust, (12.6, 6.4, 2.0), (12.65, 6.4, H + 0.6), 0.11, 10)
    reb.prim("cyl", "Gate valve wheel", mat("red paint"), (12.6, 6.4, 2.6), (0.5, 0.5, 0.05), rot=(0, math.pi / 2, 0), segments=16)
    reb.prim("cube", "Switch panel", kit.dirtied(mat("steel"), 0.7), (X1 - 0.08, 7.9, 1.4), (0.12, 0.7, 0.9))
    kit.rod("Knife switch, off", mat("black"), (X1 - 0.18, 7.9, 1.45), (X1 - 0.5, 7.9, 1.1), 0.025, 6)
    reb.prim("cube", "Switch label", mat("white paint"), (X1 - 0.145, 7.9, 1.75), (0.01, 0.4, 0.12))
    kit.text("Switch words", "PUMP", mat("black"), (X1 - 0.152, 7.9, 1.75), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    reb.prim("cyl", "Gauge", reb.mat_plain("Gauge face", (0.5, 0.48, 0.4), 0.4), (X1 - 0.15, 7.7, 1.2), (0.14, 0.14, 0.02), rot=(0, math.pi / 2, 0), segments=14)
    kit.rod("Cable to the switch", mat("black"), (X1 - 0.1, 7.9, 1.85), (X1 - 0.1, 7.9, H), 0.015, 4)
    kit.drum("Oil drum", rust, (10.3, 1.6, 0.0))
    reb.wall(reb.prim("cube", "Drum footprint", None, (10.3, 1.6, 0.5), (0.65, 0.65, 1.0))).hide_render = True
    kit.crate("Spares crate", mat("planks"), (3.4, 1.55, 0.0), size=(0.8, 0.6, 0.5), rot=0.1)
    reb.wall(reb.prim("cube", "Crate footprint", None, (3.4, 1.55, 0.5), (0.85, 0.7, 1.0))).hide_render = True
    # The dog, wrapped against the pump bed.
    dog = reb.prim("sphere", "Wrapped dog", reb.mat_surface("Dog cocoon", [(0.0, (0.4, 0.39, 0.35)), (0.6, (0.58, 0.57, 0.52)), (0.85, (0.2, 0.12, 0.08)), (1.0, (0.3, 0.05, 0.03))], scale=14, bump=0.9), (10.55, 4.4, 0.32), (1.0, 0.5, 0.55), rot=(0, 0.2, 1.3), segments=14)
    reb.wall(dog)
    reb.prim("cone", "Paw out of the silk", reb.mat_plain("Fur", (0.06, 0.05, 0.04), 0.9), (10.4, 3.85, 0.18), (0.08, 0.08, 0.3), rot=(1.2, 0, 0.3), segments=8)
    for k in range(7):
        kit.rod("Silk tether", silk, (10.55, 4.4, 0.4), (10.95 + rng.uniform(0, 0.4), 4.4 + rng.uniform(-0.8, 0.8), rng.uniform(0.3, 1.4)), 0.004, 3)

    # ---- The spinners' nursery: egg sacs on the roof, some split; webs choking the corners.
    sv, sf = [], []
    split = None
    for cx, cy, n in ((4.0, 3.2, 9), (9.0, 5.8, 11), (3.4, 7.6, 7), (7.6, 4.2, 6)):
        for k in range(n):
            x, y = cx + rng.gauss(0, 0.45), cy + rng.gauss(0, 0.4)
            z = H - 0.05 - rng.uniform(0.1, 0.5)
            r = rng.uniform(0.1, 0.2)
            reb.boulder(rng, (x, y, z), r, sv, sf, squash=1.3)
            kit.rod("Sac thread", silk, (x, y, z + r * 0.9), (x + rng.uniform(-0.2, 0.2), y + rng.uniform(-0.2, 0.2), H + 0.1), 0.004, 3)
        web_sheet(f"Nursery web {cx}", (cx, cy, H + 0.05), (1, 0.3, -0.2), (-0.4, 1, -0.25), 1.4, rng, strands=11)
    reb.mesh_object("Egg sacs", sv, sf, sac_m)
    split = reb.prim("sphere", "Split sac", sac_m, (0, 0, -0.55), (0.34, 0.3, 0.4), segments=12)
    reb.prim("cube", "Split", mat("black"), (0, -0.15, 0.0), (0.08, 0.04, 0.26)).parent = split
    sac_pivot = reb.prim("sphere", "Split sac thread top", silk, (6.4, 6.2, H - 0.1), (0.02, 0.02, 0.02))
    kit.rod("Split sac thread", silk, (0, 0, 0), (0, 0, -0.38), 0.005, 3).parent = sac_pivot
    split.parent = sac_pivot
    kit.splat("Slime under the split sac", reb.mat_plain("Slime", (0.15, 0.15, 0.08), 0.1), (6.4, 6.2, 0.0), 0.3, seed=21, lumps=0.6)
    for corner, a, b in (((X0 + 0.1, Y0 + 0.1, H - 0.1), (1, 0, 0), (0, 1, -0.4)), ((X1 - 0.1, Y0 + 0.1, H - 0.1), (-1, 0, 0), (0, 1, -0.5)), ((X0 + 0.1, Y1 - 0.1, H - 0.1), (1, 0, 0), (0, -1, -0.4)), ((X1 - 0.1, Y1 - 0.1, H - 0.1), (-1, 0, 0), (0, -1, -0.5)), ((X0 + 0.1, Y1 - 0.1, 0.0), (1, 0, 0.4), (0, -1, 0.6))):
        web_sheet("Corner web", corner, a, b, rng.uniform(1.1, 1.6), rng, strands=12)
    strands = []
    for _ in range(26):
        a = Vector((rng.uniform(X0, X1), rng.uniform(Y0, Y1), H - 0.1))
        b = a + Vector((rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), -rng.uniform(1.0, 2.5)))
        strands.append(kit.rod("Strand", silk, a, b, 0.003, 3))
    kit.join("Strands", strands)

    # ---- The rails in from the adit: one line on to the cage, a branch running down into the water.
    rails("Rails to the cage", [(X0 - 4.5, 5.8), (3.4, 5.8), (5.4, 5.2), (6.7, 3.6), (7.2, 1.7), (7.2, 0.4)], timber, rust)
    rails("Rails to the water", [(3.4, 5.8), (4.9, 6.4), (5.9, 7.1), (6.0, 7.6)], timber, rust)
    # ---- Hal's drops from the adit to the water, a bloody hand on the pipe; a boot print in the mud at the edge.
    v, f = [], []
    for k in range(18):
        t = k / 17
        x = 1.6 + (6.2 - 1.6) * t + rng.uniform(-0.12, 0.12)
        y = 5.8 + (EDGE - 0.1 - 5.8) * t + rng.uniform(-0.12, 0.12)
        if rng.random() < 0.25:
            continue
        kit._stain(v, f, rng, (x, y, 0.005), rng.uniform(0.015, 0.035), 0.0, 0.45, (1.0, 1.0), k, points=10)
    reb.mesh_object("Hal's drops", v, f, mat("old blood"), smooth=False)
    kit.splat("Hand on the pipe", mat("old blood"), (8.2, 7.9, 0.42), 0.05, rot=(0.6, 0.5, 0), seed=5)
    for k in range(3):
        kit.splat(f"Boot print {k}", mat("mud"), (6.0 + (0.12 if k % 2 else -0.12), 7.2 + k * 0.35, -max(0.0, 7.2 + k * 0.35 - 7.6) * 0.42 + 0.004), 0.06, seed=40 + k, stretch=(0.6, 1.4), lumps=0.2)
    # Old stuff: a cable reel, an ore cart pushed to the side, a pile of timber.
    reb.prim("cyl", "Cable reel", timber, (2.0, 2.0, 0.45), (0.9, 0.9, 0.5), rot=(math.pi / 2, 0, 0.3), segments=16)
    reb.wall(reb.prim("cube", "Reel footprint", None, (2.0, 2.0, 0.5), (0.9, 0.6, 1.0))).hide_render = True
    for k in range(5):
        reb.prim("cyl", "Timber prop", timber, (4.95, 1.3 + (k % 3) * 0.28, 0.13 + (k // 3) * 0.25), (0.25, 0.25, 1.8), rot=(0, math.pi / 2, 0.03 * k), segments=8)
    reb.wall(reb.prim("cube", "Timber footprint", None, (4.95, 1.6, 0.5), (1.8, 1.0, 1.0))).hide_render = True
    hrng = random.Random(397)  # its own stream, so the room built above stays as it was
    ore_cart("Ore cart pushed aside", rust, (2.15, 8.55, 0.0), 0.25)
    reb.wall(reb.prim("cube", "Pushed cart footprint", None, (2.15, 8.55, 0.5), (1.35, 0.95, 1.0), rot=(0, 0, 0.25))).hide_render = True
    kit.splat("Rust under the cart", reb.mat_plain("Rust stain", (0.09, 0.04, 0.02), 0.8), (2.2, 8.6, 0.003), 0.5, seed=63, stretch=(1.4, 0.9), lumps=0.5)

    # ---- Hal, out across the flooded way toward the gallery: slumped on an ore
    # cart that stands on a heap of fallen rock above the water, his lantern
    # beside him, the key on its chain at his neck. Off the floor, out of reach.
    hx, hy, hz = HAL_CART
    heap_v, heap_f = [], []
    for (x, y, z, r) in ((hx, hy, -1.45, 0.95), (hx - 0.7, hy + 0.5, -1.3, 0.8), (hx + 0.7, hy - 0.4, -1.4, 0.7), (hx + 0.1, hy + 0.85, -1.2, 0.7), (hx - 0.4, hy - 0.8, -1.35, 0.7)):
        reb.boulder(hrng, (x, y, z), r, heap_v, heap_f)
    for (x, y, r) in ((hx - 0.7, hy - 0.2, 0.26), (hx + 0.7, hy + 0.5, 0.3), (hx - 0.4, hy - 1.0, 0.3), (hx + 0.5, hy - 0.9, 0.22), (hx - 0.6, hy + 0.9, 0.28), (hx + 0.55, hy + 1.0, 0.2)):
        reb.boulder(hrng, (x, y, WATER_Z - 0.12), r, heap_v, heap_f)
    reb.mesh_object("Fallen rock under Hal's cart", heap_v, heap_f, kit.dirtied(mat("wet rock"), 0.5), smooth=False)
    ore_cart("Hal's cart", rust, (hx, hy, hz), math.pi / 2 + 0.08, roll=0.04, load=False)
    top = hz + 0.92
    hal = kit.body("Hal", (hx + 0.02, hy + 0.5, top), heading=-math.pi / 2 + 0.08, pose="slumped", top=mat("flannel"), legs=reb.mat_plain("Work trousers", (0.08, 0.08, 0.06), 0.9), seed=12)
    reb.cloth("Blanket on Hal's cart", reb.mat_plain("Grey blanket", (0.14, 0.14, 0.13), 0.95), (hx + 0.05, hy + 0.3, top + 0.01), (0.9, 0.7), rot=(0, 0, 0.2), cuts=10, lumps=0.04, seed=7)
    hal_lamp, hal_light, hal_flame = kit.lantern("Hal's lantern", (hx - 0.28, hy - 0.25, top), energy=7)
    # The key on its chain, hanging on his chest: brass, catching the lantern.
    neck = Vector((hx + 0.02, hy + 0.5, top))
    chest = neck + Vector((0.0, -0.25, 0.5))
    # A touch of glow so the glint survives at 320 x 240, four metres out in the dark.
    brass = reb.mat_emit("Key brass glint", (1.0, 0.78, 0.35), 3)
    links = []
    for side in (-1, 1):
        a = neck + Vector((side * 0.08, -0.14, 0.78))
        for k in range(5):
            t = k / 4
            links.append(reb.prim("sphere", "Chain link", mat("steel"), a.lerp(chest + Vector((0, 0, 0.1)), t), (0.03, 0.015, 0.03), segments=6))
    kit.join("Key chain", links)
    reb.prim("cube", "Gondola key", brass, chest, (0.05, 0.015, 0.13), rot=(0.2, 0, 0.1))
    reb.prim("cyl", "Gondola key bow", brass, chest + Vector((0, 0, 0.08)), (0.07, 0.07, 0.015), rot=(math.pi / 2 - 0.2, 0, 0.1), segments=10)
    kit.splat("Blood down the cart", mat("old blood"), (hx + 0.1, hy - 0.56, hz + 0.75), 0.07, rot=(math.pi / 2, 0, 0), seed=65, lumps=0.5)

    # ---- Light: lamps on a cable across from the adit, one over the pump; the cage lamp.
    lamps = []
    for k, (x, y, e) in enumerate(((3.2, 5.8, 45), (6.6, 5.4, 40), (9.8, 4.8, 42), (6.4, 8.4, 40))):
        glow = reb.mat_emit(f"Lamp glow {k}", (1.0, 0.72, 0.4), 14)
        pivot = reb.prim("sphere", f"Lamp hook {k}", iron, (x, y, H - 0.4), (0.03, 0.03, 0.03))
        kit.rod(f"Lamp flex {k}", mat("black"), (0, 0, 0), (0, 0, -0.5), 0.007, 4).parent = pivot
        reb.prim("sphere", f"Lamp bulb {k}", glow, (0, 0, -0.58), (0.08, 0.08, 0.11), segments=10).parent = pivot
        light = reb.point(f"Lamp {k}", (0, 0, -0.62), e, (1.0, 0.68, 0.38), 0.05)
        light.parent = pivot
        lamps.append((pivot, light, glow))
    for (a, b) in (((X0 - 1.0, 5.8, H - 0.4), (3.2, 5.8, H - 0.4)), ((3.2, 5.8, H - 0.4), (6.6, 5.4, H - 0.4)), ((6.6, 5.4, H - 0.4), (9.8, 4.8, H - 0.4)), ((6.6, 5.4, H - 0.4), (6.4, 8.4, H - 0.4))):
        kit.rod("Lamp cable", mat("black"), a, b, 0.01, 4)
    # Underground: no sky, only the lamps (and nothing grey leaking through a seam in the rock).
    reb.point("Fill", (7.0, 5.0, 3.0), 18, (0.7, 0.6, 0.5), 2.5)

    anim = kit.Anim(16)
    anim.ripple(water, speed=1)
    anim.bob(pool, height=0.015, speed=1)
    for k, (pivot, light, glow) in enumerate(lamps):
        anim.flicker(light, glow, depth=0.55 if k == 3 else 0.08, dropouts=3 if k == 3 else 0)
    anim.flicker(cage_light, cage_glow, depth=0.15, dropouts=1)
    anim.custom(lambda k: setattr(sac_pivot, "rotation_euler", (math.radians(3) * math.sin(anim.phase(k)), 0, 0.6 * math.sin(anim.phase(k)))))
    anim.drip((9.0, 5.8, H - 0.4), fall=H - 0.4, size=0.015, m=reb.mat_plain("Slime drop", (0.2, 0.2, 0.1), 0.1))
    anim.flicker(hal_light, hal_flame, depth=0.3, dropouts=0)

    # ---- What the game needs.
    room.void((d0 - 0.5, EDGE, d1 + 0.5, Y1))
    room.door("tunnel", (X0, a0 + 0.2, X0 + 0.6, a1 - 0.2), arrive=(2.4, 5.8), face=(1, 0))
    room.door("mine-lift", (gx0, cy1 + 0.1, gx1, cy1 + 0.7), arrive=(7.2, 3.6), face=(0, 1))
    room.door("gallery", (d0, EDGE - 0.6, d1, EDGE), arrive=(6.0, 6.8), face=(0, -1))
    room.check((c1 + 0.1, Y0, c1 + 1.1, Y0 + 0.8), "The lift cage. LIFT TO SURFACE. The cable goes up into the dark.")
    # The pump's switch is behind it and its pipes, out of her reach: she works it from the pump's west face.
    room.spot("drain", (10.0, 5.2, 10.8, 6.6))  # day/events.ts says what she sees and does here
    room.check((d0, EDGE - 1.2, d1, EDGE - 0.6), "The way down goes under the water. His blood goes right to the edge.\nSomeone's out there, slumped on a cart. Hal?\nIt's too far, and too deep, to wade.")
    room.check((9.9, 3.6, 10.4, 5.2), "A dog, one of the big ones, wrapped up in web.\nSomething down here eats them.")
    room.check((5.4, 5.6, 7.4, 6.8), "Egg sacs, all over the roof. That one's split open.")
    room.export(anim)


build()
