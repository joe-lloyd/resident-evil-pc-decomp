"""The dogs' den, a hollow north of the woods, at noon under cloud.

What it tells: this is where the drag marks end. The dogs have a den in a
hollow under a granite overhang, where the spruce roots hang down through
the bank. The ranger is here. They pulled him in under the lip of the rock
and ate what they wanted: his khaki shirt is torn open, an arm and a leg
are gone below the joint, and the flies are thick on him. His ring of keys
still hangs at his belt and catches what light there is. He is not the
first: the floor of the hollow is littered with gnawed bones, deer and
older ones, a human skull among them, and a hiker's orange jacket is
shredded across the roots. At the back, under the rock, the dogs have dug
a pit in the soil where they lie, matted with their hair. A heavy collar
with a broken chain lies by it: these were somebody's dogs once. Water
drips from the overhang into a puddle stained red.

Metres: she walks the floor of the hollow, x 3-15, y 2-12. The trampled
way comes down from the woods at the south edge, x 7.5-10. Earth banks
rise steeply west, east and south; the granite overhang juts out over the
north of the floor, its lip about 3.2 m up at y 4.5, and the rock face
under it stands at y 1.5. The pit is at x 8.5, y 2.9; the ranger lies at
x 10.6, y 5.0, his head toward the rock.

Moving: flies on the ranger and the pit, water dripping from the lip, the
hanging roots in the draught.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 3.0, 15.0, 2.0, 12.0
WAY = (7.5, 10.0)          # the trampled way down from the woods, x along the south edge
LIP_Y = 4.5                # the overhang's front edge
FACE_Y = 1.5               # the rock face under it
PIT = (8.5, 2.9)
RANGER = (10.6, 5.0)


def height(x, y):
    """The hollow's floor flat; banks rising steeply west and east, the slope
    back up to the woods in the south, the rock behind."""
    n = noise.noise(Vector((x * 0.3, y * 0.3, 5.0)))
    h = -0.03 + 0.025 * n
    d_pit = math.hypot((x - PIT[0]) / 1.3, (y - PIT[1]) / 0.9)
    if d_pit < 1.0:
        h -= 0.16 * (1 - d_pit ** 2)
    if x < X0 + 0.3:
        h += (X0 + 0.3 - x) ** 1.3 * 0.9
    if x > X1 - 0.3:
        h += (x - X1 + 0.3) ** 1.3 * 0.9
    if y > Y1 + 0.3:
        dy = y - Y1 - 0.3
        h += dy * (0.45 if WAY[0] - 0.5 < x < WAY[1] + 0.5 else 0.9)
    if y < Y0:
        h += (Y0 - y) * 1.5
    return h + (0.4 * n if (x < X0 or x > X1 or y > Y1 + 0.3) else 0.0)


def tube(verts, faces, pts, r, sides=5, taper=0.4):
    """A thin tube along `pts` (a root, a hanging rootlet), tapering toward the end."""
    pts = [Vector(p) for p in pts]
    base = len(verts)
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(d).normalized()
        rr = r * (1 - taper * i / max(1, len(pts) - 1))
        for k in range(sides):
            a = 2 * math.pi * k / sides
            verts.append(tuple(p + (side * math.cos(a) + up * math.sin(a)) * rr))
    for i in range(len(pts) - 1):
        for k in range(sides):
            a = base + i * sides + k
            b = base + i * sides + (k + 1) % sides
            faces.append((a, b, b + sides, a + sides))


def hanging_root(rng, verts, faces, top, length, r=0.03):
    """A root hanging from the bank or the lip, kinking as it falls."""
    p = Vector(top)
    pts = [p.copy()]
    seg = length / 6
    for _ in range(6):
        p = p + Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), -seg))
        pts.append(p.copy())
    tube(verts, faces, pts, r, 5, 0.7)


def world(at, heading, local):
    """A point in a kit.body's own frame placed in the world."""
    return Vector(at) + Matrix.Rotation(heading, 3, "Z") @ Vector(local)


def build():
    rng = random.Random(24)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")
    room.camera((8.6, 11.7, 3.3), (9.4, 3.2, 0.6), 200, "from the way down: the hollow, the overhang, the ranger under the lip")
    room.camera((4.6, 5.8, 2.8), (11.2, 11.2, 0.2), 200, "from under the lip in the north-west: the ranger, the jacket on the east bank, the way back up")
    room.camera((14.6, 7.0, 3.6), (5.0, 6.0, 0.3), 200, "from the east bank: the den under the rock, the pit, the bones, the skull")

    soil = reb.mat_surface("Den soil", [(0.0, (0.03, 0.02, 0.012)), (0.5, (0.08, 0.055, 0.035)), (1.0, (0.13, 0.09, 0.055))], scale=2.5, bump=0.6)
    bank = reb.mat_surface("Earth bank", [(0.0, (0.03, 0.02, 0.012)), (0.4, (0.09, 0.062, 0.038)), (0.55, (0.05, 0.07, 0.025)), (0.75, (0.035, 0.065, 0.02)), (1.0, (0.07, 0.1, 0.035))], scale=2.2, bump=0.9)
    churned = reb.mat_surface("Churned soil", [(0.0, (0.015, 0.01, 0.006)), (1.0, (0.06, 0.04, 0.025))], scale=6, rough=0.8, bump=0.8)
    hair = reb.mat_cards("Dog hair", (0.02, 0.018, 0.016), (0.09, 0.08, 0.07))
    root_m = reb.mat_surface("Roots", [(0.0, (0.05, 0.035, 0.022)), (1.0, (0.13, 0.09, 0.06))], scale=20, bump=0.5)
    jacket = reb.mat_surface("Hiker's jacket", [(0.0, (0.5, 0.12, 0.02)), (0.75, (0.6, 0.18, 0.03)), (1.0, (0.18, 0.03, 0.01))], scale=6, rough=0.5, bump=0.2)
    trousers = reb.mat_surface("Ranger trousers", [(0.0, (0.06, 0.07, 0.04)), (1.0, (0.1, 0.11, 0.06))], scale=40, bump=0.2)
    flesh = reb.mat_surface("Torn flesh", [(0.0, (0.1, 0.006, 0.004)), (0.6, (0.3, 0.03, 0.025)), (1.0, (0.42, 0.12, 0.1))], scale=10, rough=0.3, bump=0.5)

    # ---- Ground: the floor of the hollow, the banks, the way down from the woods.
    reb.terrain("Hollow", soil, (X0 - 0.6, X1 + 0.6), (Y0 - 0.6, Y1 + 0.6), height, step=0.3)
    reb.terrain("Banks", bank, (-14, 32), (-12, 34), lambda x, y: height(x, y) - (0.02 if X0 - 0.6 < x < X1 + 0.6 and Y0 - 0.6 < y < Y1 + 0.6 else 0.0), step=0.6)
    kit.path_strip("Trampled way", reb.mat_plain("Trampled", (0.05, 0.035, 0.02), 0.9), [(8.8, 22.0), (8.8, 16.0), (8.7, 12.6), (8.9, 10.5), (9.6, 7.5), (10.2, 5.8)], height, width=0.6)
    kit.drag_trail("The drag ends here", mat("old blood"), [(8.8, 15.0), (8.8, 12.5), (9.0, 10.4), (9.7, 7.6), (10.3, 5.9)], width=0.5, seed=3, height=height)
    kit.drag_trail("Fresh drag", mat("blood"), [(8.8, 13.0), (9.1, 10.0), (9.8, 7.4), (10.4, 5.8)], width=0.32, seed=4, height=height)

    # ---- The overhang: granite blocks jutting out over the north of the floor, the face under it.
    rv, rf = [], []
    # The shelf: blocks whose flat undersides make the overhang's roof, about 3.2 m up.
    for (x, y, sx, sy) in ((4.6, 1.6, 2.8, 3.0), (8.4, 2.0, 2.6, 2.6), (12.2, 1.7, 2.8, 2.9), (15.6, 1.0, 2.2, 2.6)):
        kit.crag(rng, rv, rf, (x, y, 4.3), (sx, sy, 3.2), floor=-0.35)
    # The face under it and the rock behind, down to the floor.
    for (x, y, sx, sy, sz) in ((5.6, -0.6, 2.6, 2.0, 2.4), (9.6, -0.4, 2.4, 1.9, 2.3), (13.4, -0.6, 2.6, 2.0, 2.4), (2.0, 1.2, 2.2, 2.6, 3.6), (16.8, 2.0, 2.0, 2.2, 3.0), (9.0, -3.5, 6.0, 3.0, 6.0)):
        kit.crag(rng, rv, rf, (x, y, 0.8), (sx, sy, sz), floor=-0.6)
    granite = reb.mat_surface("Den granite", [(0.0, (0.025, 0.025, 0.023)), (0.45, (0.06, 0.058, 0.052)), (0.7, (0.035, 0.05, 0.025)), (1.0, (0.11, 0.105, 0.095))], scale=1.1, rough=0.6, bump=1.0)
    reb.mesh_object("Overhang", rv, rf, granite, smooth=False)
    # A spruce grows on top of the rock; its roots come down over the lip.
    cv, cf = [], []
    reb.conifer(rng, Vector((8.6, 0.8, 6.0)), 15, cv, cf)
    reb.mesh_object("Spruce on the rock", cv, cf, mat("needles"))
    reb.trunks("Its trunk", mat("bark"), [(Vector((8.6, 0.8, 5.6)), 15)])
    mv, mf = [], []
    for _ in range(14):
        reb.fern(rng, (rng.uniform(3.5, 15.0), rng.uniform(1.5, 3.4), 6.6 + rng.uniform(-0.6, 0.3)), rng.uniform(0.4, 0.7), mv, mf)
    reb.mesh_object("Ferns on the rock", mv, mf, mat("ferns"))
    # She can't walk into the rock face at the back.
    reb.wall(reb.prim("cube", "Rock face footprint", None, ((X0 + X1) / 2, Y0 - 0.2, 0.5), (X1 - X0 + 1, 0.6, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "West rock footprint", None, (X0 + 0.6, Y0 + 1.0, 0.5), (1.6, 2.0, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "East rock footprint", None, (X1 - 0.5, Y0 + 1.0, 0.5), (1.4, 2.0, 1.0))).hide_render = True
    # Loose rocks fallen from it, one tagged where she'd bump it.
    lv, lf = [], []
    for (x, y, r) in ((4.0, 2.7, 0.55), (13.8, 3.4, 0.45), (3.6, 10.6, 0.5), (14.3, 9.5, 0.6), (5.8, 3.0, 0.25), (12.2, 8.4, 0.2)):
        reb.boulder(rng, (x, y, height(x, y) - 0.05), r, lv, lf)
        if r > 0.4:
            reb.wall(reb.prim("cube", "Rock footprint", None, (x, y, r / 2), (r * 2.2, r * 1.9, r))).hide_render = True
    for (x, y, r) in ((1.6, 6.4, 1.1), (16.4, 8.2, 1.2), (12.4, 13.8, 0.9), (4.8, 13.6, 1.0), (16.6, 11.8, 0.8), (1.4, 10.6, 0.9), (17.0, 4.6, 1.0)):
        reb.boulder(rng, (x, y, height(x, y) - 0.2), r, lv, lf)
    reb.mesh_object("Fallen rocks", lv, lf, mat("rock"))

    # ---- Roots: hanging from the lip and the banks, snaking out over the floor's edges.
    tv, tf = [], []
    for i in range(34):
        x = rng.uniform(X0, X1)
        hanging_root(rng, tv, tf, (x, LIP_Y + rng.uniform(-0.6, 0.2), 3.0 + rng.uniform(0, 0.3)), rng.uniform(0.6, 1.9), rng.uniform(0.012, 0.035))
    for i in range(26):
        side = rng.choice(("w", "e"))
        y = rng.uniform(Y0 + 1, Y1)
        x = X0 - 0.4 if side == "w" else X1 + 0.4
        z = height(x, y) + rng.uniform(0.3, 1.2)
        hanging_root(rng, tv, tf, (x, y, z), rng.uniform(0.4, 1.2), rng.uniform(0.015, 0.04))
    for i in range(10):
        side = rng.choice((-1, 1))
        y = rng.uniform(Y0 + 2, Y1)
        x0 = X0 - 1.2 if side < 0 else X1 + 1.2
        pts = [(x0, y, height(x0, y) + 0.1)]
        for k in range(5):
            xx = x0 - side * (k + 1) * 0.35
            yy = y + rng.uniform(-0.3, 0.3)
            pts.append((xx, yy, height(xx, yy) + 0.04 + 0.05 * (k == 2)))
        tube(tv, tf, pts, rng.uniform(0.04, 0.08), 6, 0.6)
    roots = reb.mesh_object("Roots", tv, tf, root_m)

    # ---- The pit they lie in: churned soil, hair, a collar with a broken chain.
    kit.splat("The dogs' pit", churned, (PIT[0], PIT[1], height(*PIT) + 0.005), 1.0, seed=7, stretch=(1.3, 0.9), lumps=0.25)
    hv, hf = [], []
    for _ in range(500):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 1.0) ** 0.5
        x, y = PIT[0] + math.cos(a) * d * 1.3, PIT[1] + math.sin(a) * d * 0.85
        reb.card(hv, hf, Vector((x, y, height(x, y) + 0.012)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.02, 0.09, 0.0)
    reb.mesh_object("Dog hair in the pit", hv, hf, hair)
    cx, cy = PIT[0] + 1.6, PIT[1] + 0.9
    collar = reb.prim("cyl", "Collar", reb.mat_plain("Collar leather", (0.04, 0.025, 0.015), 0.6), (cx, cy, 0.02), (0.22, 0.22, 0.04), segments=16)
    reb.prim("cyl", "Collar hole", mat("black"), (cx, cy, 0.03), (0.17, 0.17, 0.02), segments=16)
    reb.prim("cube", "Collar tag", mat("steel"), (cx + 0.12, cy, 0.01), (0.05, 0.04, 0.004))
    for k in range(6):
        reb.prim("cyl", f"Chain link {k}", mat("iron"), (cx - 0.16 - k * 0.055, cy + 0.02 * math.sin(k), 0.012), (0.05, 0.03, 0.01), rot=(0 if k % 2 else math.pi / 2, 0, 0.2), segments=8)
    reb.prim("cube", "Broken link", mat("rust"), (cx - 0.52, cy + 0.04, 0.008), (0.04, 0.012, 0.012), rot=(0, 0, 0.8))

    # ---- The ranger: on his back under the lip, half eaten, the keys at his belt.
    heading = math.radians(100)   # head toward the rock (north)
    rx, ry = RANGER
    kit.body("The ranger", (rx, ry, height(rx, ry) + 0.01), heading, pose="back", top=mat("khaki"), legs=trousers, seed=8, missing=("l_hand", "r_foot"))
    # His keys, by his hand, for his partner to give her (plan step truck-keys).
    room.item("truck-keys", (rx + 0.45, ry + 0.35, height(rx + 0.45, ry + 0.35)))
    kit.splat("His blood", mat("blood"), tuple(world((rx, ry, 0), heading, (1.05, 0, 0.0))), 0.42, rot=(0, 0, 0.4), seed=9, stretch=(1.5, 1.0))
    kit.splat("His blood, older", mat("old blood"), tuple(world((rx, ry, 0), heading, (0.7, 0.3, -0.002))), 0.6, rot=(0, 0, 1.2), seed=10, stretch=(1.4, 1.0))
    j = kit._POSES["back"]
    chest = world((rx, ry, 0), heading, j["chest"])
    pelvis = world((rx, ry, 0), heading, j["pelvis"])
    reb.prim("sphere", "His opened chest", flesh, ((chest + pelvis) / 2) + Vector((0, 0, 0.06)), (0.34, 0.3, 0.12), rot=(0, 0, heading), segments=12)
    for i in range(5):
        p = chest.lerp(pelvis, i / 6)
        for s in (-1, 1):
            q = p + Matrix.Rotation(heading, 3, "Z") @ Vector((0, s * 0.15, 0))
            kit.rod("Rib", mat("bone"), p + Vector((0, 0, 0.15)), q + Vector((0, 0, 0.1)), 0.01, 4)
    for name, (lx, ly) in (("Stump of his arm", j["l_elbow"][:2]), ("Stump of his leg", j["r_knee"][:2])):
        p = world((rx, ry, 0), heading, (lx, ly, 0.08))
        reb.prim("sphere", name, flesh, p, (0.12, 0.12, 0.1), segments=10)
    # The belt and the key ring.
    belt_at = world((rx, ry, 0), heading, (0.9, 0, 0.17))
    reb.prim("cyl", "Belt", reb.mat_plain("Belt leather", (0.03, 0.02, 0.012), 0.5), belt_at, (0.07, 0.36, 0.26), rot=(0, 0, heading), segments=12)
    reb.prim("cube", "Buckle", reb.mat_metal("Brass", (0.55, 0.38, 0.12), 0.3), belt_at + Vector((0, 0, 0.13)), (0.06, 0.08, 0.01), rot=(0, 0, heading))
    ring_at = world((rx, ry, 0), heading, (0.9, -0.2, 0.1))
    reb.prim("cyl", "Key ring", mat("steel"), ring_at, (0.07, 0.07, 0.008), rot=(math.pi / 2, 0, heading), segments=12)
    for k in range(4):
        a = -0.6 + k * 0.4
        kp = ring_at + Matrix.Rotation(heading, 3, "Z") @ Vector((math.sin(a) * 0.06, -0.03, -math.cos(a) * 0.06 - 0.02))
        reb.prim("cube", f"Key {k}", reb.mat_metal("Bright keys", (0.7, 0.66, 0.55), 0.2), kp, (0.012, 0.025, 0.07), rot=(0, a, heading))
    reb.point("Glint on the keys", ring_at + Vector((0.2, 0.3, 0.6)), 0.6, (0.85, 0.88, 0.92), 0.05)
    # His hat, his radio, shreds of his shirt.
    hat_at = world((rx, ry, 0), heading, (2.4, 0.6, 0.0))
    reb.prim("cyl", "Ranger hat brim", reb.mat_plain("Hat felt", (0.2, 0.15, 0.08), 0.8), hat_at + Vector((0, 0, 0.01)), (0.42, 0.42, 0.012), rot=(0.12, 0, 0), segments=18)
    reb.prim("cone", "Ranger hat crown", reb.mat_plain("Hat felt", (0.2, 0.15, 0.08), 0.8), hat_at + Vector((0, 0.01, 0.07)), (0.2, 0.2, 0.12), rot=(0.12, 0, 0), segments=12, top=0.7)
    radio_at = world((rx, ry, 0), heading, (0.3, -0.9, 0.0))
    reb.prim("cube", "His radio", reb.mat_plain("Radio black", (0.02, 0.02, 0.02), 0.5), radio_at + Vector((0, 0, 0.04)), (0.08, 0.2, 0.06), rot=(0, 0, 0.9))
    kit.rod("Radio aerial", mat("black"), radio_at + Vector((0, 0, 0.05)), radio_at + Vector((0.18, 0.12, 0.05)), 0.004, 4)
    for k in range(4):
        p = world((rx, ry, 0), heading, (rng.uniform(0.2, 1.6), rng.uniform(-1.2, 1.2), 0))
        reb.cloth(f"Shred of khaki {k}", mat("khaki"), (p.x, p.y, height(p.x, p.y) + 0.01), (rng.uniform(0.12, 0.25), rng.uniform(0.08, 0.15)), rot=(0, 0, rng.uniform(0, 6)), cuts=4, lumps=0.015, seed=k)

    # ---- What they ate before him: deer bones and older ones, a human skull, a hiker's jacket.
    for k, (x, y, sk) in enumerate(((6.2, 4.2, False), (12.8, 4.0, True), (5.0, 6.4, False), (7.6, 8.4, False), (13.2, 7.0, False), (11.6, 2.8, False), (6.8, 2.4, True))):
        kit.bones(f"Gnawed bones {k}", (x, y, height(x, y)), spread=0.7, seed=40 + k, skull=sk)
    # A deer's skull with its antler, and a long jaw.
    reb.prim("sphere", "Deer skull", mat("bone"), (5.4, 5.2, 0.08), (0.36, 0.15, 0.14), rot=(0, 0, 0.5), segments=12)
    for s in (-1, 1):
        kit.rod("Antler", mat("bone"), (5.3, 5.2 + s * 0.05, 0.13), (5.0, 5.2 + s * 0.35, 0.45), 0.02, 5)
        kit.rod("Antler tine", mat("bone"), (5.1, 5.2 + s * 0.24, 0.32), (5.25, 5.2 + s * 0.38, 0.52), 0.014, 5)
    # The human skull, half buried by the pit.
    reb.prim("sphere", "Human skull", mat("bone"), (9.7, 2.5, 0.06), (0.17, 0.2, 0.18), segments=14)
    for s in (-1, 1):
        reb.prim("sphere", "Eye socket", mat("black"), (9.79, 2.42 + s * 0.04, 0.08), (0.04, 0.05, 0.05), segments=8)
    # The hiker's jacket, shredded over the west bank's roots, and its pieces.
    reb.cloth("Hiker's jacket", jacket, (X1 - 0.45, 9.4, 0.5), (0.7, 0.55), rot=(0.25, 0.9, 0.3), cuts=12, lumps=0.07, seed=11)
    reb.cloth("Torn sleeve", jacket, (X1 - 1.4, 9.0, 0.02), (0.55, 0.16), rot=(0, 0, 1.1), cuts=8, lumps=0.03, seed=12)
    for k in range(6):
        x, y = rng.uniform(11.0, 14.0), rng.uniform(7.5, 10.5)
        reb.cloth(f"Shred of jacket {k}", jacket, (x, y, height(x, y) + 0.01), (rng.uniform(0.1, 0.22), rng.uniform(0.06, 0.12)), rot=(0, 0, rng.uniform(0, 6)), cuts=4, lumps=0.01, seed=20 + k)
    kit.splat("Old stain on the jacket", mat("old blood"), (X1 - 0.5, 9.3, 0.57), 0.14, rot=(0.25, 0.9, 0.3), seed=13)
    # A boot of the hiker's, laced, and his pack frame bent.
    reb.prim("cube", "Hiker's boot", reb.mat_plain("Brown leather", (0.09, 0.05, 0.025), 0.6), (6.6, 9.8, 0.06), (0.3, 0.12, 0.13), rot=(0, 0, 0.4), bevel=0.03)
    for a, b in (((5.4, 10.2, 0.03), (6.1, 10.6, 0.05)), ((5.5, 10.5, 0.03), (6.0, 9.9, 0.06)), ((5.4, 10.2, 0.03), (5.5, 10.5, 0.03))):
        kit.rod("Bent pack frame", reb.mat_metal("Aluminium", (0.4, 0.4, 0.42), 0.4), a, b, 0.012, 6)
    # A deer's spine and ribs dragged out into the open, older bones round it.
    sx, sy = 7.2, 9.0
    for k in range(9):
        p = Vector((sx + k * 0.12, sy - k * 0.05, 0.05))
        reb.prim("sphere", f"Vertebra {k}", mat("bone"), p, (0.08, 0.06, 0.06), segments=8)
        if 2 <= k <= 7:
            for s_ in (-1, 1):
                kit.rod("Deer rib", mat("bone"), p, p + Vector((0.05, s_ * 0.3, 0.12 - 0.08 * (k % 2))), 0.012, 5)
    kit.splat("Dark earth under the spine", mat("old blood"), (sx + 0.5, sy - 0.2, height(sx, sy)), 0.4, seed=15, stretch=(1.4, 0.8))
    reb.cloth("Dragged hide", reb.mat_surface("Old hide", [(0.0, (0.06, 0.04, 0.025)), (1.0, (0.16, 0.11, 0.07))], scale=8, bump=0.4), (sx - 0.8, sy + 0.45, 0.04), (0.65, 0.42), rot=(0.1, 0.05, 0.9), cuts=10, lumps=0.09, seed=16)
    for k, (x, y) in enumerate(((10.5, 9.6), (12.6, 11.0), (4.4, 10.8))):
        kit.bones(f"Old bones {k}", (x, y, height(x, y)), spread=0.6, seed=60 + k, skull=False)
    # Prints everywhere in the soft floor.
    pv, pf = [], []
    for k in range(70):
        x, y = rng.uniform(X0 + 0.5, X1 - 0.5), rng.uniform(Y0 + 0.5, Y1 - 0.5)
        kit._stain(pv, pf, rng, (x, y, height(x, y) + 0.006), 0.04, rng.uniform(0, 6), 0.2, (1, 1.1), k, points=8, drops=False)
    reb.mesh_object("Paw prints", pv, pf, churned, smooth=False)

    # ---- Water dripping from the lip into a reddened puddle.
    drip_at = (9.4, LIP_Y - 0.3, 2.95)
    kit.splat("Puddle under the drip", reb.mat_plain("Red puddle", (0.04, 0.008, 0.006), 0.08), (drip_at[0], drip_at[1], height(drip_at[0], drip_at[1]) + 0.004), 0.32, seed=14, stretch=(1.3, 1.0))

    # ---- Round the hollow: spruces on the banks, ferns, needles.
    cams = ((8.6, 11.7), (4.6, 5.8), (14.6, 7.0))

    def keep_out(x, y):
        if X0 - 1.0 < x < X1 + 1.0 and Y0 - 3.5 < y < Y1 + 0.8:
            return True
        if y > Y1 and abs(x - 8.8) < 1.4:
            return True
        return any((x - cx) ** 2 + (y - cy) ** 2 < 9 for cx, cy in cams)
    kit.forest(rng, height, keep_out, (-14, -12, 32, 34), count=95, spacing=1.8, tall=(13, 21), ferns=120, needles=900, dead=0.15)
    fv, ff = [], []
    for _ in range(70):
        side = rng.choice((0, 1, 2))
        if side == 0:
            x, y = rng.uniform(X0 - 0.4, X0 + 0.4), rng.uniform(Y0 + 2, Y1)
        elif side == 1:
            x, y = rng.uniform(X1 - 0.4, X1 + 0.4), rng.uniform(Y0 + 2, Y1)
        else:
            x, y = rng.uniform(X0, X1), rng.uniform(Y1 - 0.4, Y1 + 0.6)
        if abs(x - 8.8) < 1.3 and y > Y1 - 1:
            continue
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.6), fv, ff)
    ferns = reb.mesh_object("Ferns on the banks", fv, ff, mat("ferns"))

    def on_bank(r_):
        while True:
            x, y = r_.uniform(X0 - 3, X1 + 3), r_.uniform(Y0 + 1.5, Y1 + 3)
            if (x < X0 + 0.2 or x > X1 - 0.2 or y > Y1 - 0.2) and not (abs(x - 8.8) < 1.0 and y > Y1 - 0.5):
                return x, y
    grass = kit.meadow(rng, 2600, on_bank, height)
    # Windfall on the rim: spruce trunks fallen into the hollow's edge, their bark split.
    for k, (a, b) in enumerate((((1.2, 7.0), (3.6, 9.6)), ((16.8, 5.2), (14.4, 6.6)), ((12.0, 14.6), (15.6, 12.8)))):
        za, zb = height(*a) + 0.25, height(*b) + 0.22
        kit.rod(f"Windfall {k}", mat("bark"), (a[0], a[1], za), (b[0], b[1], zb), 0.24, 10)

    # ---- Light: the cloud's flat light into the hollow, dark under the rock.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=2.6, mist=((9.0, 6.0, 4.0), (60.0, 60.0, 14.0), 0.008),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.1))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(30)
    reb.spot("Sky into the hollow", (9.0, 16.0, 9.0), (9.5, 5.0, 0.0), 900, (0.8, 0.84, 0.9), 45, 0.9, 4.0)
    reb.point("Under the rock", (9.0, 3.8, 1.6), 140, (0.6, 0.66, 0.75), 1.5)

    anim = kit.Anim(16)
    anim.flies((rx + 0.1, ry - 0.5, 0.15), count=16, radius=0.55)
    anim.flies((PIT[0], PIT[1], 0.05), count=6, radius=0.6)
    anim.drip(drip_at, fall=drip_at[2] - 0.02)
    anim.sway(roots, amount=0.02, along=(1.0, 0.3), every=5, tip=3)
    anim.sway(ferns, amount=0.02)
    anim.sway(grass, amount=0.04)

    # ---- What the game needs.
    room.door("woods", (WAY[0], Y1 - 0.6, WAY[1], Y1), arrive=(8.9, 10.6), face=(0, -1))
    room.check((rx - 1.0, ry - 1.2, rx + 0.8, ry + 0.8), "The ranger. What the dogs left of him.\nHis keys are still on his belt.")
    room.check((PIT[0] - 1.2, PIT[1] - 0.8, PIT[0] + 0.9, PIT[1] + 0.8), "A pit scraped in the soil, matted with black hair.\nThis is where they sleep.")
    room.check((cx - 0.7, cy - 0.4, cx + 0.4, cy + 0.4), "A heavy collar on a broken chain. The tag's too scratched to read.\nThese dogs belonged to someone.")
    room.check((9.3, 2.0, 10.3, 3.0), "A human skull. It's been here a lot longer than he has.")
    room.check((X1 - 1.9, 8.4, X1, 10.2), "A hiker's jacket, shredded on the roots.\nI don't want to know where the hiker is.")
    room.check((4.8, 4.6, 6.0, 5.8), "A deer's skull, licked clean.")
    room.check((8.9, 3.6, 10.0, 4.6), "Water dripping off the rock into a puddle. The puddle's red.")
    room.entry = "The smell hits first. Then the flies."
    room.export(anim)


build()
