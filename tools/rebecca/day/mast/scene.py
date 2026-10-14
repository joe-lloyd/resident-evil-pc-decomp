"""The radio mast at the north end of the summit, afternoon.

What it tells: the observer came here bleeding, along the ridge from the
weather station with the crows on him, because the telecom engineers keep
their stores by the mast. He forced the first crate he came to with a
tyre iron, tore open two first aid boxes and dressed himself on his knees:
wrappers and bloody gauze lie round the crates, and the flare case is open
with one flare gone. Then something made him run for the edge. His tracks
scuff to the east brink, his glove lies there, and he is on the ledge six
metres down, face down, with the crows on him. The crows have been at the
mast too: one flew into a guy wire and hangs tangled in it, turning in the
wind. Over it all the red warning light keeps blinking.

Metres: the floor is x 1-17, y 1-13, bare rock and gravel. The mast stands
in a fenced square, x 8.2-11.8, y 3.7-7.3, its gate open on the south. The
equipment cabin is x 1.5-5.5, y 1.5-4.2; the crates are stacked at its east
end, x 5.9-7.6, y 1.6-4.4. Guy wires run to anchors at the west
(2.0, 7.6) and the north-east (15.8, 2.6) and north off the floor. East
of x 17 the mountain drops away; the ledge is at x 18.5-22, 6 m down. The
trail back to the summit leaves south off the floor at x 7-10.

Moving: the red warning lights blinking, the dead crow turning on the
wire, the tarp's loose corner lifting, a crow on the body below pecking,
dead grass in the wind.
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

X0, Y0, X1, Y1 = 1.0, 1.0, 17.0, 13.0
MAST = (10.0, 5.5)
FENCE = (8.2, 11.8, 3.7, 7.3)
GATE = (9.4, 10.6)
CABIN = (1.5, 5.5, 1.5, 4.2)
TALL = 34.0
LEDGE = (19.0, 22.5, 3.5, 10.5, -3.5)
STORES_SHIFT = (-1.9, 3.5, 0.0)


def height(x, y):
    """Flat where she walks; the cliff east to the ledge and beyond; falls west and north; the ridge on south."""
    n = noise.noise(Vector((x * 0.15, y * 0.15, 5.0)))
    if X0 - 0.4 < x < X1 + 0.3 and Y0 - 0.4 < y < Y1 + 0.4:
        return 0.03 * n - 0.03
    out = max(X0 - 0.4 - x, x - X1 - 0.3, Y0 - 0.4 - y, y - Y1 - 0.4, 0.0)
    h = 0.5 * n * min(1.0, out / 3.0)
    if x > X1 + 0.3:
        # Down the cliff to the ledge, and past the ledge's lip, on down.
        d = x - X1 - 0.3
        if LEDGE[2] < y < LEDGE[3] and x < LEDGE[1]:
            # Scree down to the ledge.
            return max(LEDGE[4], LEDGE[4] * d / (LEDGE[0] - X1 - 0.3)) + 0.05 * n
        return h - min(6.0, d * 10.0) - d * 3.0
    if x < X0 - 0.4:
        h -= (X0 - 0.4 - x) * 0.8
    if y < Y0 - 0.4:
        h -= (Y0 - 0.4 - y) * 0.5
    return h


def struts(name, m, segs, r, sides=4):
    """Many square bars, one mesh: a lattice, a frame, a fence."""
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


def first_aid(name, at, rot=0.0, open_=False):
    """A white first aid box with its red cross, shut or torn open."""
    x, y, z = at
    box = kit.box(name, mat("white paint"), (x, y, z), (0.42, 0.3, 0.22), rot=rot, bevel=0.01)
    c, s = math.cos(rot), math.sin(rot)
    fx, fy = x - 0.151 * s, y + 0.151 * c
    reb.prim("cube", f"{name} cross", mat("red paint"), (fx, fy, z + 0.11), (0.14, 0.004, 0.04), rot=(0, 0, rot))
    reb.prim("cube", f"{name} cross", mat("red paint"), (fx, fy, z + 0.11), (0.04, 0.004, 0.14), rot=(0, 0, rot))
    if open_:
        reb.prim("cube", f"{name} lid", mat("white paint"), (x + 0.2 * s, y - 0.2 * c, z + 0.24), (0.42, 0.02, 0.3), rot=(1.1, 0, rot))
        reb.prim("cube", f"{name} inside", mat("black"), (x, y, z + 0.221), (0.38, 0.26, 0.002), rot=(0, 0, rot))
    return box


def build():
    rng = random.Random(3402)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((1.0, 15.2, 3.8), (10.0, 4.5, 0.6), 195, "from the trail in, south-west: the mast in its fence, the cabin, the crow on the wire")
    room.camera((17.0, 15.2, 3.6), (5.5, 4.5, 0.4), 200, "from the south-east by the brink: the cabin and the forced crates, the mast's foot")
    room.camera((15.4, 11.9, 4.0), (20.5, 6.4, -2.0), 200, "across to the east brink: his glove, the ledge below with him on it, the valley beyond")

    gravel = kit.dirtied(mat("gravel"), 0.5, scale=0.5)
    rock = kit.dirtied(reb.mat_surface("Summit granite", [(0.0, (0.07, 0.07, 0.065)), (0.45, (0.17, 0.165, 0.15)), (0.7, (0.22, 0.2, 0.18)), (1.0, (0.13, 0.12, 0.11))], scale=1.2, bump=0.8), 0.6, scale=0.35)
    mast_red = reb.mat_surface("Mast red", [(0.0, (0.3, 0.04, 0.02)), (0.8, (0.42, 0.06, 0.03)), (1.0, (0.2, 0.09, 0.05))], scale=8, rough=0.55, bump=0.1)
    mast_white = reb.mat_surface("Mast white", [(0.0, (0.45, 0.44, 0.4)), (0.8, (0.58, 0.57, 0.53)), (1.0, (0.3, 0.2, 0.12))], scale=8, rough=0.55, bump=0.1)
    cabin_m = reb.mat_surface("Cabin grey", [(0.0, (0.17, 0.19, 0.18)), (0.7, (0.26, 0.28, 0.26)), (1.0, (0.25, 0.13, 0.06))], scale=3, rough=0.5, bump=0.3)
    chainlink = reb.mat_surface("Chain link", [(0.0, (0.2, 0.2, 0.19)), (1.0, (0.32, 0.32, 0.3))], scale=60, rough=0.5, bump=0.8)
    nodes, links = chainlink.node_tree.nodes, chainlink.node_tree.links
    see = nodes.new("ShaderNodeMixShader")
    see.inputs["Fac"].default_value = 0.35
    links.new(nodes.new("ShaderNodeBsdfTransparent").outputs[0], see.inputs[1])
    links.new(nodes["Principled BSDF"].outputs[0], see.inputs[2])
    links.new(see.outputs[0], nodes["Material Output"].inputs["Surface"])
    crate_m = mat("planks")
    gauze = reb.mat_surface("Bloody gauze", [(0.0, (0.5, 0.48, 0.42)), (0.55, (0.45, 0.4, 0.35)), (0.7, (0.25, 0.02, 0.01)), (1.0, (0.12, 0.005, 0.004))], scale=18, bump=0.2)
    orange = reb.mat_plain("Flare orange", (0.6, 0.18, 0.02), 0.5)

    # ---- Ground: rock round a gravelled pad, the ledge below the brink.
    reb.terrain("Mountain", rock, (-60, 90), (-70, 80), height, step=0.7)
    reb.prim("cube", "Gravel pad", gravel, (8.0, 5.5, -0.04), (14.0, 9.0, 0.06))
    kit.cracks("Seams", mat("black"), (X0, Y0, X1, Y1), count=14, seed=4, length=2.0)
    kit.path_strip("Trail from the summit", reb.mat_plain("Worn rock", (0.15, 0.14, 0.13), 0.9), [(8.5, 50.0), (8.5, 20.0), (8.6, 13.5), (9.2, 10.0), (10.0, 7.6)], height, width=0.55, lift=0.004)
    rv, rf = [], []
    for _ in range(150):
        x, y = rng.uniform(-40, 50), rng.uniform(-50, 60)
        if X0 - 0.5 < x < X1 + 1 and Y0 - 0.5 < y < Y1 + 0.5:
            continue
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.3, 1.8), rv, rf)
    for _ in range(40):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        if 1.0 < x < 16.4 and 1.0 < y < 12.4:
            continue
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.08, 0.3), rv, rf)
    reb.mesh_object("Boulders", rv, rf, mat("rock"))
    for (x, y, r) in ((14.2, 8.8, 0.8), (3.4, 10.8, 0.6)):
        bv, bf = [], []
        reb.boulder(rng, (x, y, height(x, y) - 0.1), r, bv, bf, squash=0.7)
        reb.wall(reb.mesh_object("Outcrop", bv, bf, rock), "circle")
    grass = kit.meadow(rng, 500, lambda r: (r.uniform(X0 - 5, X1), r.uniform(Y0 - 5, Y1 + 5)), height, mat("dead grass"))

    # ---- The mast: a lattice in red and white bands, its ladder, its dishes, its lights.
    mx, my = MAST
    half = 1.2

    def corner(i, z):
        f = 1.0 - 0.75 * z / TALL
        dx, dy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[i]
        return (mx + dx * half * f, my + dy * half * f, z)
    bands = {0: [], 1: []}
    step = 2.0
    z = 0.0
    while z < TALL - 1e-6:
        band = int(z // 4.0) % 2
        segs = bands[band]
        for i in range(4):
            segs.append((corner(i, z), corner(i, z + step)))
            segs.append((corner(i, z + step), corner((i + 1) % 4, z + step)))
            segs.append((corner(i, z), corner((i + 1) % 4, z + step)))
        z += step
    struts("Mast red", mast_red, bands[0], 0.06)
    struts("Mast white", mast_white, bands[1], 0.06)
    for i in range(4):
        cx, cy, _ = corner(i, 0)
        reb.wall(reb.prim("cube", "Mast footing", mat("concrete"), (cx, cy, 0.15), (0.6, 0.6, 0.3)))
    # The ladder up the south face, inside a cage to 3 m.
    lz = []
    for side in (-0.2, 0.2):
        lz.append(((mx + side, my + half + 0.05, 0.0), (mx + side * 0.4, my + half * 0.25 + 0.05, TALL)))
    for k in range(0, int(TALL / 0.3)):
        zz = k * 0.3
        f = 1.0 - 0.75 * zz / TALL
        lz.append(((mx - 0.2 * (1 - 0.6 * zz / TALL), my + half * f + 0.05, zz), (mx + 0.2 * (1 - 0.6 * zz / TALL), my + half * f + 0.05, zz)))
    struts("Mast ladder", mat("steel"), lz, 0.015)
    for k in range(6):
        zz = 2.4 + k * 0.6
        pts = [(mx + 0.4 * math.cos(a), my + half + 0.35 + 0.35 * math.sin(a), zz) for a in [math.pi * j / 6 for j in range(7)]]
        struts("Ladder cage", mat("steel"), list(zip(pts, pts[1:])), 0.012)
    # Panels and dishes up top.
    for i, (dx, dy, zz, rot) in enumerate(((0.45, 0.0, 28.0, 0.0), (-0.45, 0.0, 28.0, math.pi), (0.0, 0.45, 30.5, math.pi / 2))):
        reb.prim("cube", f"Panel aerial {i}", mat("white paint"), (mx + dx, my + dy, zz), (0.12, 0.35, 1.6), rot=(0, 0, rot))
    for i, (zz, yaw) in enumerate(((22.0, 0.3), (18.0, 2.6))):
        reb.prim("cyl", f"Dish {i}", mat("white paint"), (mx + math.cos(yaw) * 0.9, my + math.sin(yaw) * 0.9, zz), (1.0, 1.0, 0.25), rot=(math.pi / 2, 0, yaw + math.pi / 2), segments=20)
    beacon_m = reb.mat_emit("Warning lamp", (1.0, 0.04, 0.02), 40)
    beacons = []
    for zz in (TALL + 0.4, 17.0):
        reb.prim("sphere", "Warning lamp", beacon_m, (mx, my, zz), (0.4, 0.4, 0.4), segments=10)
        beacons.append(reb.point("Warning lamp light", (mx, my, zz), 900 if zz > 20 else 250, (1.0, 0.05, 0.02), 0.2))
    kit.rod("Lightning rod", mat("steel"), (mx, my, TALL), (mx, my, TALL + 2.5), 0.03)
    # The fence round its foot, the gate open.
    fx0, fx1, fy0, fy1 = FENCE
    for side, a0, a1, fixed, along in (("n", fx0, fx1, fy0, "x"), ("w", fy0, fy1, fx0, "y"), ("e", fy0, fy1, fx1, "y"), ("s", fx0, GATE[0], fy1, "x"), ("s", GATE[1], fx1, fy1, "x")):
        length = a1 - a0
        mid = (a0 + a1) / 2
        at = (mid, fixed, 1.0) if along == "x" else (fixed, mid, 1.0)
        size = (length, 0.03, 2.0) if along == "x" else (0.03, length, 2.0)
        reb.wall(reb.prim("cube", f"Fence {side}", chainlink, at, size))
    for x, y in ((fx0, fy0), (fx1, fy0), (fx0, fy1), (fx1, fy1), (GATE[0], fy1), (GATE[1], fy1)):
        kit.rod("Fence post", mat("steel"), (x, y, 0), (x, y, 2.1), 0.035)
    barbed = []
    for (a, b) in (((fx0, fy0), (fx1, fy0)), ((fx1, fy0), (fx1, fy1)), ((fx0, fy0), (fx0, fy1)), ((fx0, fy1), (GATE[0], fy1)), ((GATE[1], fy1), (fx1, fy1))):
        for dz in (2.15, 2.3):
            barbed.append(((a[0], a[1], dz), (b[0], b[1], dz)))
    struts("Barbed wire", mat("iron"), barbed, 0.006)
    reb.prim("cube", "Gate, open", chainlink, (GATE[1] + 0.5, fy1 + 0.45, 1.0), (0.03, 1.15, 1.9), rot=(0, 0, 0.5))
    kit.rod("Broken padlock chain", mat("iron"), (GATE[1], fy1, 1.0), (GATE[1] + 0.05, fy1 + 0.1, 0.0), 0.012, 4)
    reb.prim("cube", "Fence sign", mat("white paint"), (fx1 - 0.6, fy1 + 0.03, 1.4), (0.6, 0.02, 0.4))
    kit.text("Fence sign words", "DANGER", mat("red paint"), (fx1 - 0.6, fy1 + 0.045, 1.48), size=0.1, rot=(math.pi / 2, 0, math.pi))
    kit.text("Fence sign words 2", "HIGH VOLTAGE", mat("black"), (fx1 - 0.6, fy1 + 0.045, 1.34), size=0.055, rot=(math.pi / 2, 0, math.pi))
    # Guy wires to their anchors; the crow caught in the low south-west one.
    anchors = [(2.0, 7.6), (15.8, 2.6), (10.0, -9.0)]
    for ax, ay in anchors:
        az = height(ax, ay)
        if X0 < ax < X1 and Y0 < ay < Y1:
            reb.wall(reb.prim("cube", "Guy anchor", mat("concrete"), (ax, ay, az + 0.2), (0.8, 0.8, 0.4), bevel=0.02))
        else:
            reb.prim("cube", "Guy anchor", mat("concrete"), (ax, ay, az + 0.2), (0.8, 0.8, 0.4))
        for zz in (12.0, 24.0):
            kit.rod("Guy wire", mat("iron"), (ax, ay, az + 0.4), (mx, my, zz), 0.012, 5)
    a = Vector((2.0, 7.6, 0.4 + height(2.0, 7.6)))
    b = Vector((mx, my, 12.0))
    snag = a.lerp(b, 0.16)
    crow_pivot = reb.prim("sphere", "Snag", mat("iron"), snag, (0.03, 0.03, 0.03))
    crow, wings = kit.crow("Dead crow on the wire", (0, 0, -0.32), heading=0.0, perched=False)
    crow.rotation_euler = (math.pi, 0.4, 0.0)
    for w, side in zip(wings, (-1, 1)):
        w.rotation_euler = (side * 0.9, 0.3, 0)
    crow.parent = crow_pivot
    kit.rod("Tangled wing feathers", mat("feathers"), (0, 0, 0), (0, 0, -0.18), 0.02, 4).parent = crow_pivot
    for i in range(6):
        reb.prim("cube", f"Feather under the wire {i}", mat("feathers"), (snag.x + rng.uniform(-0.4, 0.4), snag.y + rng.uniform(-0.4, 0.4), 0.006), (0.12, 0.025, 0.003), rot=(0, 0, rng.uniform(0, 3)))
    kit.splat("Drips under the crow", mat("old blood"), (snag.x, snag.y, 0.0), 0.08, seed=13)

    # ---- The equipment cabin: a steel box, its door padlocked, cable tray to the mast.
    cx0, cx1, cy0, cy1 = CABIN
    cab = reb.prim("cube", "Equipment cabin", cabin_m, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 1.3), (cx1 - cx0, cy1 - cy0, 2.6), bevel=0.03)
    reb.wall(cab)
    for i in range(11):
        reb.prim("cube", "Cabin rib", cabin_m, (cx0 + 0.2 + i * 0.36, cy1 + 0.02, 1.3), (0.06, 0.04, 2.56))
    reb.prim("cube", "Cabin door", reb.mat_plain("Cabin door", (0.13, 0.15, 0.14), 0.5), (cx0 + 1.2, cy1 + 0.05, 1.05), (0.95, 0.04, 2.05))
    reb.prim("cube", "Padlock hasp", mat("steel"), (cx0 + 1.6, cy1 + 0.08, 1.05), (0.06, 0.04, 0.12))
    reb.prim("cube", "Cabin sign", mat("yellow paint"), (cx0 + 2.6, cy1 + 0.045, 1.7), (1.0, 0.02, 0.5))
    kit.text("Cabin sign words", "ARKLAY TELECOM", mat("black"), (cx0 + 2.6, cy1 + 0.06, 1.8), size=0.09, rot=(math.pi / 2, 0, math.pi))
    kit.text("Cabin sign words 2", "AUTHORISED STAFF", mat("black"), (cx0 + 2.6, cy1 + 0.06, 1.62), size=0.07, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Air conditioner", mat("steel"), (cx0 + 3.5, cy1 + 0.25, 1.9), (0.7, 0.45, 0.5), bevel=0.01)
    reb.prim("cyl", "Fan grille", mat("black"), (cx0 + 3.5, cy1 + 0.48, 1.9), (0.36, 0.36, 0.01), rot=(math.pi / 2, 0, 0), segments=16)
    tray = [((cx1, 2.8, 2.4), (mx - 1.0, my - 0.6, 2.4)), ((mx - 1.0, my - 0.6, 2.4), (mx - 1.0, my - 0.6, 4.0))]
    struts("Cable tray", mat("steel"), tray, 0.08)
    for x in (cx1 + 0.8, 7.5):
        kit.rod("Tray post", mat("steel"), (x, 2.8 + (x - cx1) * (my - 0.6 - 2.8) / (mx - 1.0 - cx1), 0.0), (x, 2.8 + (x - cx1) * (my - 0.6 - 2.8) / (mx - 1.0 - cx1), 2.35), 0.04)
    kit.rod("Cabin aerial", mat("steel"), (cx0 + 0.4, cy0 + 0.4, 2.6), (cx0 + 0.4, cy0 + 0.4, 5.0), 0.02)

    # ---- The engineers' stores: crates under a tarp, one forced; first aid torn open; the flare case.
    # Laid out from (5.9, 1.6), then moved south of the cabin, where the cameras see them.
    before = set(bpy.data.objects)
    sx0 = 5.9
    kit.crate("Crate", crate_m, (sx0 + 0.4, 2.0, 0.0), size=(0.8, 0.6, 0.6))
    kit.crate("Crate", crate_m, (sx0 + 0.45, 2.0, 0.6), size=(0.7, 0.55, 0.5), rot=0.1)
    kit.crate("Crate", crate_m, (sx0 + 1.2, 2.1, 0.0), size=(0.7, 0.6, 0.55), rot=-0.1)
    reb.wall(reb.prim("cube", "Stores footprint", None, (sx0 + 0.85, 3.0, 0.4), (1.7, 2.8, 0.8))).hide_render = True
    tarp = reb.cloth("Tarp", reb.mat_surface("Tarp", [(0.0, (0.04, 0.12, 0.2)), (1.0, (0.08, 0.2, 0.3))], scale=5, rough=0.6, bump=0.2), (sx0 + 0.8, 2.1, 1.12), (1.8, 1.0), cuts=16, lumps=0.12, seed=3)
    corner_pivot = reb.prim("sphere", "Tarp corner pivot", None, (sx0 + 1.7, 2.6, 1.0), (0.01, 0.01, 0.01))
    corner_pivot.hide_render = True
    flap = reb.cloth("Tarp corner", tarp.data.materials[0], (0.25, 0.25, 0.0), (0.5, 0.5), cuts=6, lumps=0.03, seed=4)
    flap.parent = corner_pivot
    forced = kit.crate("Forced crate", crate_m, (sx0 + 0.9, 3.4, 0.0), size=(0.9, 0.6, 0.55), rot=0.25)
    reb.prim("cube", "Forced lid", crate_m, (sx0 + 1.6, 3.9, 0.04), (0.9, 0.6, 0.03), rot=(0, 0.15, 0.9))
    reb.prim("cube", "Split slat", crate_m, (sx0 + 1.2, 3.25, 0.57), (0.5, 0.08, 0.025), rot=(0.4, 0, 0.3))
    reb.prim("cube", "Tyre iron", mat("iron"), (sx0 + 1.5, 4.25, 0.015), (0.55, 0.03, 0.03), rot=(0, 0, -0.4))
    kit.text("Crate stencil", "ARKLAY TELECOM", mat("black"), (sx0 + 0.4, 2.0 + 0.31, 0.3), size=0.06, rot=(math.pi / 2, 0, math.pi))
    first_aid("First aid box", (sx0 + 0.85, 3.4, 0.55), rot=0.25, open_=True)
    first_aid("First aid box, torn open", (sx0 + 0.2, 4.4, 0.0), rot=-0.6, open_=True)
    first_aid("First aid box on the stack", (sx0 + 1.2, 2.1, 0.55), rot=0.1)
    case = kit.box("Flare case", orange, (sx0 - 0.2, 3.2, 0.0), (0.5, 0.3, 0.14), rot=0.4, bevel=0.015)
    reb.prim("cube", "Flare case lid", orange, (sx0 - 0.32, 2.95, 0.2), (0.5, 0.02, 0.3), rot=(1.2, 0, 0.4))
    for i in range(3):
        reb.prim("cyl", f"Flare {i}", mat("red paint"), (sx0 - 0.2 + (i - 1) * 0.1 * math.cos(0.4), 3.2 + (i - 1) * 0.1 * math.sin(0.4), 0.15), (0.04, 0.04, 0.3), rot=(math.pi / 2, 0, 0.4 + math.pi / 2), segments=8)
    reb.prim("cube", "Empty flare slot", mat("black"), (sx0 - 0.2 + 0.2 * math.cos(0.4), 3.2 + 0.2 * math.sin(0.4), 0.141), (0.3, 0.05, 0.002), rot=(0, 0, 0.4))
    # Where he dressed himself: gauze, wrappers, a pool, a smeared handprint on the crate.
    for i in range(6):
        reb.cloth(f"Gauze {i}", gauze, (sx0 + 0.6 + rng.uniform(-0.5, 0.6), 4.9 + rng.uniform(-0.3, 0.4), 0.012), (0.15, 0.09), rot=(0, 0, rng.uniform(0, 3)), cuts=6, lumps=0.015, seed=i)
    for i in range(7):
        reb.prim("cube", f"Wrapper {i}", mat("white paint"), (sx0 + 0.6 + rng.uniform(-0.8, 0.9), 4.9 + rng.uniform(-0.5, 0.6), 0.003), (0.08, 0.06, 0.002), rot=(0, 0, rng.uniform(0, 3)))
    kit.splat("Where he knelt", mat("blood"), (sx0 + 0.7, 4.85, 0.0), 0.32, seed=21, stretch=(1.3, 1.0))
    kit.splat("Hand on the crate", mat("old blood"), (sx0 + 0.9 - 0.31 * math.sin(0.25) + 0.02, 3.4 + 0.31 * math.cos(0.25), 0.35), 0.06, rot=(math.pi / 2, 0, 0.25), seed=22)
    reb.prim("cube", "Torn sleeve", mat("flannel"), (sx0 + 1.4, 5.3, 0.01), (0.28, 0.12, 0.01), rot=(0, 0, 0.7))
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None:
            ob.location += Vector(STORES_SHIFT)
    # His tracks to the brink: scuffs, drops, the glove at the edge.
    path = [(5.4, 8.6), (9.0, 9.4), (12.0, 9.6), (14.5, 8.4), (16.6, 7.4)]
    k = 0
    for a, b in zip(path, path[1:]):
        for i in range(5):
            t = i / 5
            x = a[0] + (b[0] - a[0]) * t + rng.uniform(-0.15, 0.15)
            y = a[1] + (b[1] - a[1]) * t + rng.uniform(-0.15, 0.15)
            kit.splat(f"Drop {k}", mat("blood"), (x, y, 0.0), rng.uniform(0.025, 0.05), seed=40 + k, lumps=0.4)
            if k % 2:
                kit.splat(f"Scuff {k}", reb.mat_plain("Scuffed gravel", (0.25, 0.23, 0.2), 0.9), (x + 0.15, y - 0.1, 0.0), 0.1, seed=70 + k, stretch=(1.8, 0.5), lumps=0.3)
            k += 1
    reb.prim("cube", "Glove at the brink", reb.mat_plain("Glove leather", (0.18, 0.1, 0.05), 0.8), (16.7, 7.5, 0.03), (0.22, 0.11, 0.05), rot=(0, 0, 0.4), bevel=0.02)
    kit.drag_trail("Slide at the brink", mat("old blood"), [(16.2, 7.6), (16.8, 7.3), (17.6, 7.2), (18.6, 7.3), (19.6, 7.4)], width=0.3, seed=5, height=height)

    # ---- Below the brink: the ledge, and him on it.
    lx0, lx1, ly0, ly1, lz = LEDGE
    kit.body("The observer", (20.2, 7.4, lz + 0.02), heading=2.6, pose="front", top=reb.mat_plain("Fleece", (0.12, 0.2, 0.32), 0.95), legs=mat("khaki"), bloody=1.0, seed=8)
    body_crow, _ = kit.crow("Crow on him", (20.7, 7.0, lz + 0.28), heading=2.0)
    kit.crow("Crow by him", (21.3, 7.9, lz + 0.02), heading=3.4)
    kit.crow("Crow on the brink", (17.2, 9.6, height(17.2, 9.6)), heading=0.3)
    rv, rf = [], []
    for _ in range(14):
        x, y = rng.uniform(lx0, lx1), rng.uniform(ly0, ly1)
        reb.boulder(rng, (x, y, lz), rng.uniform(0.15, 0.5), rv, rf)
    reb.mesh_object("Ledge rocks", rv, rf, mat("rock"))

    # ---- The summit far off south: the weather hut, the headframe.
    reb.prim("cube", "Far weather hut", kit.boards("Far hut boards", (0.28, 0.27, 0.22), width=0.14), (4.0, 50.0, height(4.0, 50.0) + 1.25), (4.0, 3.2, 2.5))
    reb.prim("cube", "Far head house", kit.boards("Far head house boards", (0.2, 0.14, 0.09), width=0.2), (15.0, 59.0, height(15.0, 59.0) + 1.5), (4.0, 3.6, 3.0))
    struts("Far headframe", mat("dark wood"), [((15 + dx, 59 + dy, 3.0), (15 + dx * 0.25, 59 + dy * 0.25, 8.0)) for dx in (-1.4, 1.4) for dy in (-1.2, 1.2)], 0.09)

    # ---- Light: the afternoon sun south-west; the valley falling away east and north.
    kit.time_light("afternoon", sun_heading=235, sun_energy=4.0, sky=((0.55, 0.5, 0.46), (0.2, 0.25, 0.34), 0.65))
    vb = set(bpy.data.objects)
    kit.vista(rng, (9.0, 7.0), (1.0, 0.0), below=-240.0, far=(320, 650), haze=(0.36, 0.38, 0.45))
    kit.vista(rng, (9.0, 7.0), (0.0, -1.0), below=-240.0, far=(320, 650), haze=(0.36, 0.38, 0.45))
    kit.vista(rng, (9.0, 7.0), (-1.0, 0.0), below=-240.0, far=(320, 650), ridges=2, haze=(0.36, 0.38, 0.45))
    # The afternoon sun washes the ridges out: darken them so they sit back in the haze.
    for ob in set(bpy.data.objects) - vb:
        ob.visible_shadow = False
        for m in ob.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == "VALTORGB":
                    for el in nd.color_ramp.elements:
                        el.color = (el.color[0] * 0.45, el.color[1] * 0.45, el.color[2] * 0.5, 1)
    reb.spot("Sun on the ledge", (26.0, 14.0, 6.0), (20.4, 7.4, lz), 700, (1.0, 0.85, 0.65), 25, 0.6, 0.3)

    anim = kit.Anim(16)
    anim.blink(beacons[0], beacon_m, on=(0, 6))
    anim.blink(beacons[1], None, on=(0, 6))
    anim.custom(lambda k: setattr(crow_pivot, "rotation_euler", (0.15 * math.sin(anim.phase(k)), 0.1 * math.cos(anim.phase(k)), 0.8 * math.sin(anim.phase(k)))))
    anim.custom(lambda k: setattr(corner_pivot, "rotation_euler", (0, -0.6 * max(0.0, math.sin(anim.phase(k, 2))), 0)))
    anim.custom(lambda k: setattr(body_crow, "rotation_euler", (0, 0.5 * max(0.0, math.sin(anim.phase(k, 3))), 2.0)))
    anim.sway(grass, amount=0.05)

    # ---- What the game needs.
    room.void((X1 - 0.25, Y0, X1, Y1))
    room.door("summit-trail", (7.0, Y1 - 0.6, 10.0, Y1), arrive=(8.6, 11.3), face=(0, -1))
    room.check((3.4, 6.2, 6.0, 8.0), "Engineers' stores. One crate's been forced with a tyre iron.\nTwo first aid boxes, ripped open. The flare case is missing one.")
    room.check((4.0, 8.0, 5.8, 9.2), "Gauze, wrappers, blood. Somebody patched himself up here, on his knees.")
    room.check((15.9, 6.6, X1 - 0.25, 8.4), "A glove, right at the edge.\nHe's down there on the ledge. Not moving. The crows are on him.")
    room.check((2.4, 6.4, 4.2, 8.0), "A crow, caught in the guy wire. It flew straight into it.")
    room.check((GATE[0], FENCE[3], GATE[1], FENCE[3] + 0.7), "The gate's open. The padlock chain's been cut.\nDANGER. HIGH VOLTAGE.")
    room.check((CABIN[0] + 0.6, CABIN[3], CABIN[0] + 3.2, CABIN[3] + 0.6), "ARKLAY TELECOM. AUTHORISED STAFF.\nPadlocked.")
    room.entry = "The mast. Its light's still blinking."
    room.export(anim)


build()
