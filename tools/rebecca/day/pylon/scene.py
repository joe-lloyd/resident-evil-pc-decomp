"""Pylon 7, halfway down the Arklay Skyway, at dusk.

What it tells: the gondola died with car 4 hanging just short of this
pylon, its roof level with the service platform. Its hatch is open: the
way out is across onto the grating, along the crossarm, and down the
ladder inside the tower, sixty metres to the forest. Pylon 7 had a
lineman on it this week. His toolbox is open on the platform and his hard
hat lies by the hatch to the ladder. He is still on the tower: seven
metres down, hanging in his harness from the ladder cage, and the crows
have found him. They sit along the crossarm and on the car's roof, and
watch. Below, the forest is going grey in the mist.

Metres: the floor is the platform, z 0: the grating along the crossarm's
north side, x 2-11, y 4.0-5.2, and the landing on the tower's top, x 6-8,
y 5.2-7.0, under the crossarm (z 2.2). The car hangs north of the grating,
x 1.2-3.8, y 1.8-3.4, its roof at z 0.1 and its hatch at the east end; she
crosses to it at the grating's west end. The ladder goes down through a
hatch at the landing's south edge, x 6.5-7.5. Everything else is a drop.

Moving: the car swinging on its hanger, the cables shaking, a crow on
the car's roof pecking at the hatch rim, another wheeling below, the
lineman turning slowly in his harness, the mist.
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

X0, Y0, X1, Y1 = 2.0, 4.0, 11.0, 7.0
WALK = (2.0, 11.0, 4.0, 5.2)
LANDING = (6.0, 8.0, 5.2, 7.0)
HATCH = (6.5, 7.5, 6.3, 7.0)
CAR = (1.2, 3.8, 1.8, 3.4)
ARM_Z = 2.2
CABLE_Z = 2.6
GROUND = -58.0
TOWER = (7.0, 6.1)


def ground(x, y):
    return GROUND + 2.5 * noise.noise(Vector((x * 0.04, y * 0.04, 2.0))) + 0.2 * y


def struts(name, m, segs, r, sides=4):
    """Many square bars, one mesh: a lattice, rails, a ladder."""
    verts, faces = [], []
    for a, b in segs:
        a, b = Vector(a), Vector(b)
        d = b - a
        if d.length < 1e-4:
            continue
        q = d.to_track_quat("Z", "Y")
        k = len(verts)
        for end in (a, b):
            for s in range(sides):
                t = 2 * math.pi * s / sides + math.pi / sides
                verts.append(tuple(end + q @ Vector((math.cos(t) * r, math.sin(t) * r, 0))))
        for s in range(sides):
            faces.append((k + s, k + (s + 1) % sides, k + sides + (s + 1) % sides, k + sides + s))
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def cone_trees(name, rng, area, keep_out, count, spacing, tall):
    """Spruces seen from far above: each a stack of cones, one mesh, cheap to render."""
    verts, faces = [], []
    placed = []
    tries = 0
    while len(placed) < count and tries < count * 30:
        tries += 1
        x, y = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])
        if keep_out(x, y) or any((x - px) ** 2 + (y - py) ** 2 < spacing ** 2 for px, py in placed[-60:]):
            continue
        placed.append((x, y))
        h = rng.uniform(*tall)
        z = ground(x, y)
        r = h * rng.uniform(0.18, 0.24)
        for t in range(4):
            z0 = z + h * (0.12 + 0.2 * t)
            rr = r * (1 - 0.22 * t)
            k = len(verts)
            for s in range(7):
                a = 2 * math.pi * s / 7 + t * 0.4
                verts.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z0))
            verts.append((x, y, z0 + h * 0.36))
            faces.extend((k + s, k + (s + 1) % 7, k + 7) for s in range(7))
    return reb.mesh_object(name, verts, faces, mat("needles"), smooth=False)


def mist_card_mat(name, rgb, density, scale):
    """Mist on a card: noise thinned to nothing at the card's edges."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    out = nodes["Material Output"]
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, scale, 4, 0.6)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, (0, 0, 0)), (0.75, (density,) * 3)])
    tc = nodes.new("ShaderNodeTexCoord")
    sub = nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    links.new(tc.outputs["Generated"], sub.inputs[0])
    mul = nodes.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = (2, 2, 0)
    links.new(sub.outputs[0], mul.inputs[0])
    ln = nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    links.new(mul.outputs[0], ln.inputs[0])
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 1.0
    edge.inputs["From Max"].default_value = 0.3
    links.new(ln.outputs["Value"], edge.inputs["Value"])
    prod = nodes.new("ShaderNodeMath")
    prod.operation = "MULTIPLY"
    links.new(r.outputs["Color"], prod.inputs[0])
    links.new(edge.outputs["Result"], prod.inputs[1])
    links.new(prod.outputs[0], mix.inputs["Fac"])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def build():
    rng = random.Random(707)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((12.2, 2.6, 3.0), (3.6, 5.0, -0.6), 200, "from off the east end: the length of the grating to the car, the crows on the arm, the drop")
    room.camera((-1.6, 3.2, 3.6), (7.5, 5.0, -0.6), 200, "from out past the car, west: the car's roof and its open hatch, the grating, the landing")
    room.camera((10.2, 9.4, 3.6), (7.0, 6.6, -3.2), 200, "from out over the drop, south-east: the landing, the ladder going down the tower, the lineman hanging below, the forest")

    grating = reb.mat_surface("Grating", [(0.0, (0.05, 0.05, 0.05)), (0.5, (0.18, 0.18, 0.17)), (1.0, (0.24, 0.16, 0.1))], scale=45, rough=0.6, bump=1.0)
    galv = reb.mat_surface("Galvanised", [(0.0, (0.2, 0.21, 0.21)), (0.7, (0.33, 0.33, 0.31)), (1.0, (0.28, 0.17, 0.09))], scale=6, rough=0.55, bump=0.2)
    yellow = mat("yellow paint")
    car_red = reb.mat_surface("Car paint", [(0.0, (0.22, 0.03, 0.02)), (0.8, (0.35, 0.05, 0.03)), (1.0, (0.18, 0.1, 0.06))], scale=4, rough=0.45, bump=0.1)
    droppings = reb.mat_plain("Droppings", (0.5, 0.5, 0.46), 0.8)

    # ---- The platform: the grating, the landing, the rails.
    wx0, wx1, wy0, wy1 = WALK
    lx0, lx1, ly0, ly1 = LANDING
    reb.prim("cube", "Grating", grating, ((wx0 + wx1) / 2, (wy0 + wy1) / 2, -0.04), (wx1 - wx0, wy1 - wy0, 0.08))
    reb.prim("cube", "Landing", grating, ((lx0 + lx1) / 2, (ly0 + ly1) / 2, -0.04), (lx1 - lx0, ly1 - ly0, 0.08))
    hx0, hx1, hy0, hy1 = HATCH
    reb.prim("cube", "Ladder hole", mat("black"), ((hx0 + hx1) / 2, (hy0 + hy1) / 2 + 0.05, 0.002), (hx1 - hx0 - 0.2, hy1 - hy0 - 0.1, 0.004))
    reb.prim("cube", "Ladder hatch, open", grating, ((hx0 + hx1) / 2, hy0 - 0.02, 0.35), (hx1 - hx0 - 0.2, 0.04, 0.7), rot=(-0.15, 0, 0))
    for side in (-1, 1):
        kit.rod("Ladder hoop rail", yellow, ((hx0 + hx1) / 2 + side * 0.4, hy1 - 0.05, 0), ((hx0 + hx1) / 2 + side * 0.4, hy1 - 0.05, 1.1), 0.025)
    kit.rod("Ladder hoop", yellow, ((hx0 + hx1) / 2 - 0.4, hy1 - 0.05, 1.1), ((hx0 + hx1) / 2 + 0.4, hy1 - 0.05, 1.1), 0.025)
    for y in (wy0 + 0.02, wy1 - 0.02):
        reb.prim("cube", "Grating edge", galv, ((wx0 + wx1) / 2, y, -0.06), (wx1 - wx0, 0.05, 0.14))
    rails = []
    # North rail, gapped at the car.
    posts = [x for x in [wx0 + 0.1 + i * 0.9 for i in range(11)] if not (2.0 < x < 3.9)]
    for x in posts:
        rails.append(((x, wy0 + 0.03, 0), (x, wy0 + 0.03, 1.1)))
    for z in (0.55, 1.1):
        rails.append(((3.9, wy0 + 0.03, z), (wx1, wy0 + 0.03, z)))
        rails.append(((wx1, wy0 + 0.03, z), (wx1, wy1, z)))
        rails.append(((wx0, wy0 + 0.03, z), (wx0, wy1 - 0.03, z)))
        rails.append(((wx0, wy1 - 0.03, z), (lx0, wy1 - 0.03, z)))
        rails.append(((lx1, wy1 - 0.03, z), (wx1, wy1 - 0.03, z)))
        rails.append(((lx0 - 0.03, wy1, z), (lx0 - 0.03, ly1, z)))
        rails.append(((lx1 + 0.03, wy1, z), (lx1 + 0.03, ly1, z)))
        rails.append(((lx0, ly1 + 0.03, z), (hx0, ly1 + 0.03, z)))
        rails.append(((hx1, ly1 + 0.03, z), (lx1, ly1 + 0.03, z)))
    for x, y in ((wx1, wy1), (wx0, wy1), (lx0 - 0.03, ly1), (lx1 + 0.03, ly1), (wx0, wy0 + 0.03)):
        rails.append(((x, y, 0), (x, y, 1.1)))
    rail_ob = struts("Platform rails", yellow, rails, 0.025)
    # The chain across the gap, unhooked and hanging.
    for k in range(6):
        t0, t1 = k / 6, (k + 1) / 6
        kit.rod("Gap chain", mat("iron"), (3.9, wy0 + 0.03 - 0.0 * t0, 0.9 - 0.7 * t0), (3.9, wy0 + 0.03, 0.9 - 0.7 * t1), 0.008, 4)
    reb.prim("cube", "Gap sign", mat("white paint"), (4.4, wy0 + 0.02, 0.8), (0.5, 0.02, 0.3))
    kit.text("Gap sign words", "CAR ACCESS", mat("red paint"), (4.4, wy0 + 0.005, 0.84), size=0.065)
    kit.text("Gap sign words 2", "CLIP ON", mat("red paint"), (4.4, wy0 + 0.005, 0.74), size=0.065)
    # The lineman's things: his toolbox open, his hard hat by the ladder, his flask, droppings and feathers.
    tb = kit.box("Toolbox", mat("red paint"), (8.6, 4.55, 0.0), (0.5, 0.25, 0.22), rot=0.1, bevel=0.01)
    reb.wall(tb)
    reb.prim("cube", "Toolbox tray", mat("red paint"), (8.62, 4.32, 0.28), (0.48, 0.18, 0.05), rot=(0.6, 0, 0.1))
    for i in range(4):
        reb.prim("cube", f"Spanner {i}", mat("steel"), (8.0 + rng.uniform(-0.3, 0.3), 4.7 + rng.uniform(-0.25, 0.25), 0.006), (0.26, 0.03, 0.01), rot=(0, 0, rng.uniform(0, 3)))
    reb.prim("cyl", "Grease gun", mat("iron"), (9.3, 4.8, 0.05), (0.08, 0.08, 0.4), rot=(math.pi / 2, 0, 0.7), segments=10)
    reb.prim("sphere", "Hard hat", mat("yellow paint"), (7.4, 6.0, 0.06), (0.3, 0.26, 0.17), segments=14)
    reb.prim("cyl", "Hard hat brim", mat("yellow paint"), (7.4, 6.0, 0.015), (0.36, 0.32, 0.02), segments=14)
    reb.prim("cyl", "Flask", mat("green paint"), (5.2, 4.8, 0.05), (0.1, 0.1, 0.3), rot=(math.pi / 2, 0, 2.0), segments=12)
    for i in range(18):
        x, y = rng.uniform(wx0 + 0.3, wx1 - 0.3), rng.uniform(wy0 + 0.1, wy1 - 0.1)
        kit.splat(f"Droppings {i}", droppings, (x, y, 0.0), rng.uniform(0.03, 0.07), seed=80 + i, lumps=0.6)
    for i in range(8):
        reb.prim("cube", f"Feather {i}", mat("feathers"), (rng.uniform(3, 10), rng.uniform(wy0 + 0.1, wy1 - 0.1), 0.004), (0.12, 0.025, 0.003), rot=(0, 0, rng.uniform(0, 3)))
    kit.drag_trail("His boots, bloody, to the ladder", mat("old blood"), [(9.6, 4.8), (8.4, 5.0), (7.3, 5.6), (7.0, 6.3)], width=0.12, seed=6)

    # ---- The crossarm over the landing, the sheave trains, the cables.
    reb.prim("cube", "Crossarm", galv, (6.5, 5.6, ARM_Z), (10.6, 0.45, 0.45))
    for x in (2.0, 11.0):
        kit.rod("Arm brace", galv, (x, 5.6, ARM_Z - 0.2), (TOWER[0] + (0.9 if x > 7 else -0.9), 6.1, -1.2), 0.05)
    reb.prim("cube", "Pylon plate", mat("white paint"), (6.5, 5.37, ARM_Z), (0.8, 0.02, 0.3))
    kit.text("Pylon number", "PYLON 7", mat("black"), (6.5, 5.355, ARM_Z), size=0.14)
    reb.prim("cube", "Danger plate", mat("yellow paint"), (8.4, 5.37, ARM_Z), (0.9, 0.02, 0.28))
    kit.text("Danger words", "NO CLIMBING", mat("black"), (8.4, 5.355, ARM_Z), size=0.1)
    cables = []
    for cx in (2.5, 10.5):
        reb.prim("cube", "Sheave frame", mat("iron"), (cx, 5.6, ARM_Z + 0.35), (0.4, 2.0, 0.3))
        for k in range(4):
            reb.prim("cyl", "Sheave", mat("rust"), (cx, 4.95 + k * 0.42, CABLE_Z - 0.12), (0.34, 0.34, 0.08), rot=(0, math.pi / 2, 0), segments=14)
        hub = reb.prim("sphere", "Cable hub", None, (cx, 5.6, CABLE_Z), (0.01, 0.01, 0.01))
        hub.hide_render = True
        up = kit.rod("Cable up the mountain", mat("iron"), (0, 0, 0), (0, -160.0, 100.0), 0.028, 6)
        down = kit.rod("Cable down to the valley", mat("iron"), (0, 0, 0), (0, 170.0, -55.0), 0.028, 6)
        for c in (up, down):
            c.location += Vector((cx, 5.6, CABLE_Z))
            c.parent = hub
            c.matrix_parent_inverse = hub.matrix_world.inverted()
        cables.append(hub)

    # ---- Car 4, hanging off the north side, its hatch open.
    cx0, cx1, cy0, cy1 = CAR
    ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    grip = Vector((2.5, ccy, CABLE_Z))
    car_pivot = reb.prim("sphere", "Car pivot", mat("iron"), grip, (0.06, 0.06, 0.06))
    before = set(bpy.data.objects)
    reb.prim("cube", "Car grip", mat("iron"), grip, (0.5, 0.3, 0.25))
    kit.rod("Car hanger", mat("iron"), grip, (ccx, ccy, 0.15), 0.05)
    reb.prim("cube", "Car body", car_red, (ccx, ccy, -1.0), (cx1 - cx0, cy1 - cy0, 2.2), bevel=0.2)
    reb.prim("cube", "Car windows", reb.mat_glass("Car glass", (0.4, 0.45, 0.45)), (ccx, ccy, -0.65), (cx1 - cx0 + 0.02, cy1 - cy0 + 0.02, 0.95))
    reb.prim("cube", "Car inside", reb.mat_plain("Car dark", (0.03, 0.015, 0.01), 0.9), (ccx, ccy, -1.0), (cx1 - cx0 - 0.15, cy1 - cy0 - 0.15, 2.0))
    reb.prim("cube", "Car roof", car_red, (ccx, ccy, 0.07), (cx1 - cx0 + 0.15, cy1 - cy0 + 0.15, 0.08), bevel=0.03)
    reb.prim("cube", "Car hatch hole", mat("black"), (3.25, ccy, 0.115), (0.55, 0.6, 0.01))
    reb.prim("cube", "Car hatch lid", car_red, (3.6, ccy, 0.4), (0.06, 0.6, 0.6), rot=(0, -0.3, 0))
    reb.prim("cube", "Car glow in the hatch", reb.mat_emit("Car lamp glow", (1.0, 0.8, 0.55), 0.6), (3.25, ccy, -0.4), (0.5, 0.55, 0.01))
    kit.text("Car number", "4", mat("white paint"), (cx1 - 0.35, cy1 + 0.012, -1.4), size=0.3, rot=(math.pi / 2, 0, math.pi))
    for i in range(3):
        kit.splat(f"Smear inside the glass {i}", mat("blood"), (cx0 + 0.5 + i * 0.7, cy1 + 0.015, -0.6 + rng.uniform(-0.15, 0.15)), 0.14, rot=(math.pi / 2, 0, 0), seed=60 + i, stretch=(0.6, 1.5))
    roof_crow, _ = kit.crow("Crow on the car roof", (2.9, ccy - 0.2, 0.11), heading=0.2)
    kit.crow("Crow on the car roof, west", (1.6, ccy + 0.3, 0.11), heading=-0.6)
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None:
            ob.parent = car_pivot
            ob.matrix_parent_inverse = car_pivot.matrix_world.inverted()

    # ---- The tower, down to the forest; the ladder in its cage; the lineman in his harness.
    tx, ty = TOWER
    gz = ground(tx, ty)

    def leg(i, z):
        f = (z - gz) / (-0.1 - gz)
        dx, dy = ((-3.2, -2.6), (3.2, -2.6), (3.2, 2.6), (-3.2, 2.6))[i]
        return (tx + dx * (1 - 0.7 * f), ty + dy * (1 - 0.7 * f), z)
    segs = []
    z = gz
    while z < -0.1:
        z2 = min(-0.1, z + 3.2)
        for i in range(4):
            segs.append((leg(i, z), leg(i, z2)))
            segs.append((leg(i, z2), leg((i + 1) % 4, z2)))
            segs.append((leg(i, z), leg((i + 1) % 4, z2)))
            segs.append((leg((i + 1) % 4, z), leg(i, z2)))
        z = z2
    struts("Tower", galv, segs, 0.08)
    for i in range(4):
        x, y, _ = leg(i, gz)
        reb.prim("cube", "Footing", mat("concrete"), (x, y, gz + 0.3), (1.2, 1.2, 0.8))
    lad = []
    lxm = (hx0 + hx1) / 2
    for side in (-0.22, 0.22):
        lad.append(((lxm + side, hy1 - 0.1, -0.1), (lxm + side, hy1 - 0.1 + 0.9, gz + 0.5)))
    n = int((0.0 - gz) / 0.3)
    for k in range(1, n):
        t = k / n
        zz = -0.1 + (gz + 0.5 + 0.1) * t
        yy = hy1 - 0.1 + 0.9 * t
        lad.append(((lxm - 0.22, yy, zz), (lxm + 0.22, yy, zz)))
    for k in range(0, n, 3):
        t = k / n
        zz = -0.1 + (gz + 0.5 + 0.1) * t
        yy = hy1 - 0.1 + 0.9 * t
        pts = [(lxm + 0.38 * math.cos(a), yy + 0.38 + 0.38 * math.sin(a), zz) for a in [math.pi * j / 6 for j in range(7)]]
        lad += list(zip(pts, pts[1:]))
    struts("Tower ladder", yellow, lad, 0.016)
    # He hangs from the cage by his lanyard, outside the ladder, limp: head down on his chest, legs dangling.
    hang_at = Vector((lxm + 0.85, 7.95, -6.5))
    lanyard = reb.prim("sphere", "Lanyard hook", mat("steel"), hang_at, (0.05, 0.05, 0.05))
    man = kit.body("The lineman", (0, 0, 0), heading=0.0, pose="back", top=reb.mat_plain("Hi-vis", (0.75, 0.4, 0.02), 0.6), legs=mat("denim"), seed=3)
    man.rotation_euler = (0, -math.pi / 2 + 0.2, 0.4)
    man.location = (0.0, 0.0, -1.0)   # the joined body's origin is at its chest
    man.parent = lanyard
    kit.rod("Lanyard", mat("black"), (0, 0, 0), (0.0, 0.0, -0.9), 0.015, 5).parent = lanyard
    for i, (dx, dy, dz, hd) in enumerate(((0.15, 0.2, -0.72, 1.0), (-0.1, -0.2, -0.8, 2.4), (0.25, 0.0, -1.1, 0.2))):
        c, w = kit.crow(f"Crow on the lineman {i}", (dx, dy, dz), heading=hd)
        c.parent = lanyard
    kit.splat("Blood down the tower", mat("old blood"), (lxm + 0.25, hy1 + 1.1, gz + 0.05), 0.4, seed=8)

    # ---- Crows on the arm; one wheeling below.
    for i, x in enumerate((4.1, 5.0, 9.3, 11.2)):
        kit.crow(f"Crow on the arm {i}", (x, 5.6, ARM_Z + 0.225), heading=math.pi / 2 + rng.uniform(-0.6, 0.6))
    wheeler, wheeler_wings = kit.crow("Crow wheeling", (7.0, 2.0, -6.0), perched=False)

    # ---- The forest far below, the valley, the mist.
    reb.terrain("Forest floor", mat("grass"), (-120, 130), (-120, 140), ground, step=3.0)

    def keep_out(x, y):
        return abs(x - tx) < 5 and abs(y - ty) < 4.5
    cone_trees("Spruces below", rng, (-90, -80, 100, 110), keep_out, 1400, 3.2, (14, 22))
    vb = set(bpy.data.objects)
    kit.vista(rng, (6.0, 5.0), (0.0, 1.0), below=-130.0, far=(200, 450), haze=(0.32, 0.2, 0.22))
    kit.vista(rng, (6.0, 5.0), (-1.0, 0.0), below=-230.0, far=(220, 450), haze=(0.4, 0.22, 0.18))
    kit.vista(rng, (6.0, 5.0), (1.0, 0.0), below=-130.0, far=(200, 450), haze=(0.22, 0.16, 0.22))
    kit.vista(rng, (6.0, 5.0), (0.0, -1.0), below=-60.0, far=(140, 300), haze=(0.22, 0.16, 0.2))
    for ob in set(bpy.data.objects) - vb:
        ob.visible_shadow = False
        if ob.name.startswith("Valley floor"):
            ob.hide_render = True

    # ---- Light: the last of the sun, low in the west; a work lamp on the arm, failing.
    sun = kit.time_light("dusk", sun_heading=275, sun_energy=3.0)
    # Mist lying in the forest below: cards, not a volume, so the long look down stays cheap.
    mist_m = mist_card_mat("Valley mist", (0.55, 0.42, 0.42), 0.7, 0.03)
    mists = []
    for i, (x, y, z, w) in enumerate(((7.0, 6.0, GROUND + 14, 160), (-40.0, 40.0, GROUND + 10, 140), (50.0, 30.0, GROUND + 12, 140), (10.0, 70.0, GROUND + 9, 160), (10.0, -50.0, GROUND + 16, 140))):
        ob = reb.prim("plane", f"Valley mist {i}", mist_m, (x, y, z), (w, w, 1), rot=(0, 0, rng.uniform(0, 3)))
        ob.visible_shadow = False
        mists.append((ob, ob.location.copy(), rng.uniform(0, 6.3)))
    sun.visible_glossy = False
    for nd in bpy.context.scene.world.node_tree.nodes:
        if nd.type == "MIX" and nd.blend_type == "ADD":
            nd.inputs["B"].default_value = (0.3, 0.1, 0.03, 1)
    lamp_m = reb.mat_emit("Work lamp", (1.0, 0.8, 0.5), 2.5)
    reb.prim("cube", "Work lamp", mat("iron"), (7.0, 5.35, ARM_Z - 0.25), (0.25, 0.15, 0.15))
    reb.prim("cube", "Work lamp glass", lamp_m, (7.0, 5.27, ARM_Z - 0.28), (0.2, 0.01, 0.1))
    reb.spot("Last light on the lineman", (hang_at.x - 9.0, hang_at.y + 6.0, hang_at.z + 1.0), (hang_at.x, hang_at.y, hang_at.z - 1.0), 700, (1.0, 0.45, 0.22), 12, 0.5, 0.3)
    work = reb.spot("Work lamp light", (7.0, 5.25, ARM_Z - 0.3), (6.5, 5.0, 0.0), 120, (1.0, 0.78, 0.5), 110, 0.6, 0.1)

    anim = kit.Anim(16)
    anim.custom(lambda k: setattr(car_pivot, "rotation_euler", (math.radians(3.0) * math.sin(anim.phase(k)), math.radians(0.8) * math.cos(anim.phase(k)), 0)))
    for i, hub in enumerate(cables):
        anim.custom(lambda k, hub=hub, i=i: setattr(hub, "rotation_euler", (math.radians(0.25) * math.sin(anim.phase(k, 2) + i), 0, math.radians(0.15) * math.sin(anim.phase(k, 3) + i))))
    anim.custom(lambda k: setattr(roof_crow, "rotation_euler", (0, 0.5 * max(0.0, math.sin(anim.phase(k, 2))), 0.2)))
    anim.custom(lambda k: setattr(lanyard, "rotation_euler", (math.radians(4) * math.sin(anim.phase(k)), 0, math.radians(25) * math.sin(anim.phase(k)))))
    anim.flap(wheeler_wings, degrees=35)

    def wheel(k):
        a = anim.phase(k)
        wheeler.location = (7.0 + 9.0 * math.cos(a), 6.0 + 7.0 * math.sin(a), -6.0 + 1.0 * math.sin(2 * a))
        wheeler.rotation_euler = (0.3, 0, a + math.pi / 2)
    anim.custom(wheel)
    anim.flicker(work, lamp_m, depth=0.45, dropouts=2)
    for ob, rest, ph in mists:
        anim.custom(lambda k, ob=ob, rest=rest, ph=ph: setattr(ob, "location", rest + Vector((5.0 * math.sin(anim.phase(k) + ph), 3.0 * math.cos(anim.phase(k) + ph), 0))))

    # ---- What the game needs.
    room.void((X0, ly0, lx0, Y1))
    room.void((lx1, ly0, X1, Y1))
    room.door("car", (2.2, wy0, 3.8, wy0 + 0.5), arrive=(3.2, 4.65), face=(1, 0), walk=False)
    room.door("valley-path", (hx0, hy0, hx1, hy1), arrive=(7.0, 5.6), face=(0, -1), walk=False)
    room.check((7.1, 5.6, 7.8, 6.3), "A hard hat. Someone was working up here.")
    room.check((8.1, 4.1, 9.6, 5.2), "A toolbox, open. Spanners everywhere. He left in a hurry, or fell.")
    room.check((5.9, 5.2, 7.2, 5.7), "PYLON 7. NO CLIMBING.\nNo choice.")
    room.check((hx0, hy0 - 0.4, hx1, hy0), "The ladder goes down inside the tower, all the way to the trees.\nThere's someone on it, a little way down. Hanging by his harness. The crows are on him.")
    room.check((2.2, wy0, 3.8, wy0 + 0.5), "Car 4. The hatch is open. The crows on its roof don't even move.")
    room.entry = "Pylon 7. It's a long way down."
    room.export(anim)


build()
