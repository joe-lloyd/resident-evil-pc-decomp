"""The woods east of Ranger Station 3, at noon under cloud.

What it tells: last night the ranger heard the dogs, went out with his
rifle and a flashlight, and fired at them from the edge of the trees: his
brass is in the needles where he stood. They took him there. The drag marks
come in from the yard on the west side, blood on the needles all the way,
and swing north round the old blowdown toward the hollow where the dogs
lie up. His flashlight fell on the way and is still on, its battery nearly
gone. One of his boots came off where he caught his heel on a root, and a
strip of his khaki shirt is snagged on a dead branch. Big paw prints run
beside the smear. The dogs were hungry before him: a doe lies half eaten
under the spruces, opened up and black with flies. A player should work
out that the ranger is somewhere north, and that whatever took him is
bigger than a coyote.

Metres: she walks the forest floor x 2-18, y 2-14, among old spruces whose
trunks stand in it. The yard's trail comes in at the west edge, y 7-9.
The drag marks go out at the north edge, x 7.5-10, down a trampled way to
the den. In the east, y 9-11.5, the trees thin into the ruts of the
logging road. A blowdown lies across the middle, x 9.5-15.5, y 9-10.6,
and an older one in the north-west, x 3-6.8, y 3.6-4.4. The doe is at
x 13, y 5.5.

Moving: the flashlight failing, flies on the doe and on the blood, the
torn khaki and the ferns in the wind.
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
from mathutils import Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 2.0, 18.0, 2.0, 14.0
WEST = (7.0, 9.0)      # the yard's trail, y along the west edge
NORTH = (7.5, 10.0)    # the trampled way to the den, x along the north edge
EAST = (9.0, 11.5)     # the ruts, y along the east edge
DOE = (13.0, 5.5)
# The old spruces that stand inside the floor: x, y, height.
STANDING = [(6.6, 13.3, 17), (11.4, 3.4, 18), (14.6, 2.3, 16), (11.8, 12.6, 17), (5.0, 1.5, 14)]
# The blowdowns: from, to, radius.
LOGS = [((9.5, 10.6), (15.6, 9.0), 0.42), ((3.0, 4.4), (6.8, 3.6), 0.32)]
# The drag: in from the yard, round the old blowdown's east end, out north.
DRAG = [(1.0, 8.2), (2.6, 8.0), (4.4, 7.6), (6.0, 7.3), (7.6, 6.6), (8.2, 5.4), (8.4, 4.0), (8.7, 2.6), (8.9, 0.8)]


def height(x, y):
    """The floor flat and just below zero; the forest floor rolling round it,
    dipping north into the hollow and rising south and west."""
    n = noise.noise(Vector((x * 0.25, y * 0.25, 3.0)))
    if X0 - 0.4 < x < X1 + 0.4 and Y0 - 0.4 < y < Y1 + 0.4:
        return -0.04 + 0.03 * n
    h = 0.5 * n
    if y < Y0 - 0.4:
        h -= (Y0 - 0.4 - y) * (0.35 if 6.0 < x < 12.0 else 0.1)
    if y > Y1 + 0.4:
        h += (y - Y1 - 0.4) * 0.35
    if x < X0 - 0.4:
        h += (X0 - 0.4 - x) * 0.15
    if x > X1 + 0.4:
        h -= (x - X1 - 0.4) * 0.05
    return h


def spruce_crown(rng, base, h, verts, faces, lift):
    """An old spruce's needles from `lift` metres up: the lower branches long
    dead, grey sticks, so the cameras look in under the crowns."""
    up = Vector((0, 0, 1))
    radius = h * rng.uniform(0.17, 0.22)
    t0 = lift / h
    for _ in range(int(h * 300)):
        t = t0 + (1 - t0) * rng.uniform(0, 1.0) ** 0.8
        r = radius * (1.0 - t) ** 0.9 * rng.uniform(0.55, 1.05) + 0.05
        a = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(a), math.sin(a), 0))
        p = base + up * (h * t) + out * r * rng.uniform(0.3, 1.0)
        reb.card(verts, faces, p, out, up, rng.uniform(0.1, 0.2), rng.uniform(0.25, 0.5) * (0.6 + 0.4 * r), rng.uniform(0.3, 0.8))


def snags(rng, base, h, lift, sv, sf):
    """Dead branch stubs up a trunk below its crown, as thin boxes."""
    for _ in range(int(lift * 1.2)):
        z = rng.uniform(1.8, lift)
        a = rng.uniform(0, 2 * math.pi)
        length = rng.uniform(0.4, 1.1)
        d = Vector((math.cos(a), math.sin(a), -0.6)).normalized()
        c = base + Vector((0, 0, z)) + d * (length / 2 + h * 0.02)
        k = len(sv)
        reb.box(sv, sf, (0, 0, 0), (length, 0.03, 0.03))
        tilt = math.atan2(-d.z, Vector((d.x, d.y)).length)
        for j in range(k, len(sv)):
            x, y, zz = sv[j]
            x, zz = x * math.cos(tilt) + zz * math.sin(tilt), -x * math.sin(tilt) + zz * math.cos(tilt)
            sv[j] = (c.x + x * math.cos(a) - y * math.sin(a), c.y + x * math.sin(a) + y * math.cos(a), c.z + zz)


def log_walls(name, a, b, r, step=1.2):
    """Hidden boxes along a fallen trunk, so she can't walk through it but its
    footprint doesn't swallow the floor beside it."""
    a, b = Vector(a), Vector(b)
    n = max(1, int((b - a).length / step))
    yaw = math.atan2((b - a).y, (b - a).x)
    for i in range(n):
        p = a.lerp(b, (i + 0.5) / n)
        ob = reb.prim("cube", f"{name} footprint", None, (p.x, p.y, r), ((b - a).length / n * 0.9, 1.8 * r, 2 * r), rot=(0, 0, yaw))
        reb.wall(ob).hide_render = True


def paw_prints(name, rng, path, m, every=0.45):
    """A big dog's prints beside a path: a pad and four toes each, one mesh."""
    verts, faces = [], []
    pts = [Vector(p) for p in path]
    side = 1
    for a, b in zip(pts, pts[1:]):
        d = b - a
        n = max(1, int(d.length / every))
        yaw = math.atan2(d.y, d.x)
        perp = Vector((-d.y, d.x)).normalized()
        for i in range(n):
            if rng.random() < 0.3:
                continue
            p = a.lerp(b, i / n) + perp * side * rng.uniform(0.35, 0.6)
            side = -side
            z = height(p.x, p.y) + 0.006
            kit._stain(verts, faces, rng, (p.x, p.y, z), 0.035, yaw, 0.2, (1.0, 1.1), i, points=8, drops=False)
            fwd = Vector((math.cos(yaw), math.sin(yaw)))
            for k, off in enumerate((-0.045, -0.015, 0.015, 0.045)):
                q = p + fwd * (0.06 if k in (1, 2) else 0.045) + Vector((-fwd.y, fwd.x)) * off
                kit._stain(verts, faces, rng, (q.x, q.y, z), 0.014, yaw, 0.1, (1, 1), k, points=6, drops=False)
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def casings(name, rng, at, count, spread):
    """Spent rifle brass: small cylinders lying in the needles, one mesh."""
    brass = reb.mat_metal("Brass", (0.55, 0.38, 0.12), 0.3)
    verts, faces = [], []
    for _ in range(count):
        x, y = at[0] + rng.gauss(0, spread), at[1] + rng.gauss(0, spread)
        a = rng.uniform(0, math.pi)
        c, s = math.cos(a), math.sin(a)
        k = len(verts)
        for e in (-0.035, 0.035):
            for j in range(6):
                t = 2 * math.pi * j / 6
                u, w = e, 0.009 * math.cos(t)
                verts.append((x + u * c - w * s, y + u * s + w * c, height(x, y) + 0.01 + 0.009 * math.sin(t)))
        faces.extend((k + j, k + (j + 1) % 6, k + 6 + (j + 1) % 6, k + 6 + j) for j in range(6))
        faces.append(tuple(k + j for j in range(6)))
        faces.append(tuple(k + 6 + j for j in reversed(range(6))))
    return reb.mesh_object(name, verts, faces, brass, smooth=False)


def settle(ob, at, rot):
    """Bake a joined object's parts where they were built (about the origin),
    then put it at `at`, turned by `rot`."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def doe(at, heading):
    """A doe on her side, legs toward +y in her own frame, her belly opened
    and the ribs showing, a hind leg gnawed to the bone."""
    hide = reb.mat_surface("Deer hide", [(0.0, (0.07, 0.045, 0.03)), (0.6, (0.15, 0.09, 0.055)), (1.0, (0.24, 0.17, 0.11))], scale=9, bump=0.3)
    flesh = reb.mat_surface("Torn flesh", [(0.0, (0.1, 0.006, 0.004)), (0.6, (0.3, 0.03, 0.025)), (1.0, (0.42, 0.12, 0.1))], scale=10, rough=0.3, bump=0.5)
    parts = [
        reb.prim("sphere", "hide", hide, (0, -0.05, 0.24), (1.25, 0.48, 0.46), segments=16),
        reb.prim("sphere", "opened belly", flesh, (-0.05, 0.14, 0.24), (0.8, 0.32, 0.34), segments=14),
        reb.prim("sphere", "haunch", hide, (-0.5, -0.02, 0.24), (0.5, 0.42, 0.4), segments=12),
    ]
    for i in range(7):
        x = 0.25 - i * 0.09
        parts.append(kit.rod("rib", mat("bone"), (x, -0.05, 0.44), (x + 0.02, 0.18, 0.4), 0.012, 5))
        parts.append(kit.rod("rib", mat("bone"), (x + 0.02, 0.18, 0.4), (x + 0.03, 0.3, 0.2), 0.011, 5))
    parts.append(kit.rod("neck", hide, (0.5, -0.04, 0.3), (0.9, 0.06, 0.2), 0.11, 10))
    parts.append(reb.prim("sphere", "head", hide, (1.02, 0.1, 0.16), (0.32, 0.15, 0.17), segments=12))
    parts.append(reb.prim("cone", "snout", hide, (1.2, 0.12, 0.13), (0.11, 0.11, 0.14), rot=(0, math.pi / 2, 0), segments=8, top=0.5))
    parts.append(reb.prim("sphere", "nose", mat("black"), (1.27, 0.12, 0.13), (0.05, 0.05, 0.05), segments=8))
    for dy in (-0.05, 0.08):
        parts.append(reb.prim("cone", "ear", hide, (0.95, 0.1 + dy, 0.27), (0.07, 0.03, 0.14), rot=(0.3, -0.5, 0), segments=6))
    legs = [((0.35, 0.12, 0.18), (0.55, 0.85, 0.05), True), ((0.25, 0.14, 0.14), (0.15, 0.82, 0.05), True),
            ((-0.5, 0.14, 0.18), (-0.25, 0.9, 0.05), True), ((-0.62, 0.12, 0.14), (-0.85, 0.55, 0.06), False)]
    for a, b, whole in legs:
        if whole:
            parts.append(kit.rod("leg", hide, a, b, 0.035, 8))
            parts.append(reb.prim("cube", "hoof", mat("black"), b, (0.06, 0.06, 0.06)))
        else:
            parts.append(kit.rod("gnawed leg", flesh, a, b, 0.05, 8))
            parts.append(kit.rod("leg bone", mat("bone"), b, (-1.05, 0.75, 0.05), 0.015, 6))
    ob = kit.join("Doe", parts)
    ob.scale = (1.2, 1.2, 1.2)
    return settle(ob, (at[0], at[1], height(*at) - 0.03), (0, 0, heading))


def far_spruces(rng, keep, count=320, area=(-55, -55, 75, 75)):
    """Spruces beyond the near forest, cheap: a dark trunk and a ragged cone
    of needle-coloured skirts each, all one mesh. Seen through the mist they
    only have to make a wall of trees."""
    m = reb.mat_surface("Far spruce", [(0.0, (0.015, 0.03, 0.018)), (1.0, (0.04, 0.07, 0.035))], scale=0.6, bump=0.3)
    verts, faces = [], []
    placed = 0
    while placed < count:
        x, y = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])
        if keep(x, y):
            continue
        placed += 1
        z = height(x, y) - 0.3
        h = rng.uniform(14, 24)
        for tier in range(4):
            z0 = z + h * (0.25 + 0.19 * tier)
            r = h * 0.2 * (1 - 0.22 * tier) * rng.uniform(0.8, 1.1)
            k = len(verts)
            sides = 9
            for j in range(sides):
                a = 2 * math.pi * j / sides + rng.uniform(-0.2, 0.2)
                rr = r * rng.uniform(0.75, 1.05)
                verts.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z0 - rng.uniform(0, 0.8)))
            verts.append((x, y, z0 + h * 0.3))
            faces.extend((k + j, k + (j + 1) % sides, k + sides) for j in range(sides))
        reb.box(verts, faces, (x, y, z + h * 0.15), (0.4, 0.4, h * 0.3))
    reb.mesh_object("Far spruces", verts, faces, m, smooth=False)


def build():
    rng = random.Random(1998)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # forest floor
    room.camera((2.7, 13.4, 3.4), (9.0, 6.0, 0.2), 200, "from the south-west: the drag in from the yard, the flashlight, the way north")
    room.camera((9.8, 2.6, 3.2), (7.4, 10.5, 0.2), 200, "from the north edge looking back: the boot, the smear swinging round the blowdown")
    room.camera((17.5, 3.4, 3.0), (10.5, 8.5, 0.3), 200, "from the north-east: the doe and her flies, the blowdown, the drag beyond")
    room.camera((12.6, 6.4, 3.6), (18.0, 11.6, 0.0), 200, "from by the doe, south-east: over the blowdown to the ruts and the way out east")
    room.camera((2.6, 2.6, 3.6), (11.0, 10.5, 0.2), 210, "from the north-west over the old blowdown: the casings, the drag in, the doe far off")

    # ---- Ground: the forest floor, the yard's trail in, the ruts out east.
    floor_m = reb.mat_surface("Forest floor", [(0.0, (0.05, 0.035, 0.02)), (0.4, (0.11, 0.075, 0.045)), (0.65, (0.15, 0.1, 0.06)), (0.85, (0.07, 0.08, 0.035)), (1.0, (0.05, 0.075, 0.025))], scale=1.2, bump=0.5)
    reb.terrain("Forest floor", floor_m, (-16, 36), (-14, 34), height, step=0.5)
    reb.terrain("Far forest floor", floor_m, (-60, 80), (-60, 80), lambda x, y: height(x, y) - 0.3, step=4.0)
    kit.path_strip("Trail from the yard", mat("dirt"), [(-12.0, 8.6), (-4.0, 8.4), (0.5, 8.1), (3.2, 8.0)], height, width=0.55)
    rut_m = reb.mat_surface("Wet ruts", [(0.0, (0.02, 0.015, 0.01)), (0.6, (0.05, 0.035, 0.022)), (1.0, (0.09, 0.065, 0.04))], scale=4, rough=0.3, bump=0.6)
    kit.path_strip("Track bed", reb.mat_plain("Track bed", (0.1, 0.075, 0.05), 0.9), [(13.0, 10.4), (17.0, 10.2), (20.0, 10.1), (34.0, 9.4)], height, width=1.3, wobble=0.15, lift=0.009)
    for dy in (-0.65, 0.65):
        kit.path_strip("Rut", rut_m, [(13.6, 10.3 + dy * 0.5), (17.0, 10.2 + dy), (20.0, 10.1 + dy), (34.0, 9.4 + dy)], height, width=0.24, lift=0.014)
    kit.path_strip("Trampled way north", reb.mat_plain("Trampled", (0.07, 0.05, 0.03), 0.9), [(8.6, 3.4), (8.8, 1.4), (8.9, -1.0), (9.2, -5.0)], height, width=0.7)

    # ---- The drag: a scuffed furrow through the needles, blood along it, prints beside it.
    kit.path_strip("Drag furrow", reb.mat_surface("Scuffed earth", [(0.0, (0.025, 0.016, 0.01)), (1.0, (0.07, 0.045, 0.028))], scale=8, rough=0.7, bump=0.6), DRAG, height, width=0.16, wobble=0.6, lift=0.006)
    kit.drag_trail("Blood on the needles", mat("old blood"), DRAG, width=0.6, seed=11, height=height)
    kit.drag_trail("Fresh blood", mat("blood"), DRAG, width=0.5, seed=12, height=height)
    kit.drag_trail("Fresh blood, again", mat("blood"), DRAG[:6], width=0.35, seed=14, height=height)
    kit.splat("Where they took him down", mat("blood"), (3.2, 8.4, height(3.2, 8.4)), 0.55, seed=13, stretch=(1.3, 1.0))
    paw_prints("Paw prints", rng, DRAG[1:], mat("mud"))
    sv_, sf_ = [], []
    for i, p in enumerate(DRAG[1:]):
        kit._stain(sv_, sf_, rng, (p[0] + rng.uniform(-0.3, 0.3), p[1] + rng.uniform(-0.3, 0.3), height(*p) + 0.007), rng.uniform(0.08, 0.16), rng.uniform(0, 6), 0.4, (1.3, 0.8), i, points=12)
    reb.mesh_object("Blood spots along the drag", sv_, sf_, mat("blood"), smooth=False)

    # What he dropped: brass where he stood, the flashlight, a boot, his khaki.
    casings("Rifle casings", rng, (3.4, 9.6), 9, 0.35)
    flm = reb.mat_surface("Flashlight body", [(0.0, (0.04, 0.05, 0.03)), (1.0, (0.08, 0.09, 0.05))], scale=30, rough=0.4, bump=0.1)
    lens_m = reb.mat_emit("Flashlight lens", (1.0, 0.82, 0.5), 4)
    fx, fy, fa = 6.4, 6.6, 2.7
    fd = Vector((math.cos(fa), math.sin(fa), 0))
    reb.prim("cyl", "Flashlight", flm, (fx, fy, height(fx, fy) + 0.035), (0.06, 0.06, 0.26), rot=(math.pi / 2, 0, fa - math.pi / 2), segments=12)
    reb.prim("cyl", "Flashlight head", flm, (fx + fd.x * 0.15, fy + fd.y * 0.15, height(fx, fy) + 0.045), (0.09, 0.09, 0.07), rot=(math.pi / 2, 0, fa - math.pi / 2), segments=12)
    reb.prim("cyl", "Flashlight lens", lens_m, (fx + fd.x * 0.188, fy + fd.y * 0.188, height(fx, fy) + 0.045), (0.08, 0.08, 0.005), rot=(math.pi / 2, 0, fa - math.pi / 2), segments=12)
    beam = reb.spot("Flashlight beam", (fx + fd.x * 0.2, fy + fd.y * 0.2, 0.06), (fx + fd.x * 3.0, fy + fd.y * 3.0, -0.2), 40, (1.0, 0.82, 0.5), 28, 0.5, 0.02)
    lens_glow = reb.point("Flashlight glow", (fx + fd.x * 0.22, fy + fd.y * 0.22, 0.07), 0.6, (1.0, 0.82, 0.5), 0.02)
    leather = reb.mat_surface("Boot leather", [(0.0, (0.05, 0.03, 0.015)), (1.0, (0.14, 0.08, 0.04))], scale=12, rough=0.55, bump=0.2)
    bx, by = 8.0, 5.9
    boot = kit.join("Ranger's boot", [
        reb.prim("cube", "foot", leather, (0.06, 0, 0.06), (0.3, 0.11, 0.12), bevel=0.03),
        reb.prim("cyl", "shaft", leather, (-0.06, 0, 0.13), (0.13, 0.12, 0.26), segments=12),
        reb.prim("cube", "sole", mat("rubber"), (0.06, 0, 0.005), (0.31, 0.12, 0.02)),
    ])
    settle(boot, (bx, by, height(bx, by) + 0.06), (math.pi / 2 - 0.15, 0, 0.9))
    reb.prim("cyl", "Sock in the boot", reb.mat_plain("Grey sock", (0.25, 0.24, 0.22), 0.9), (bx - 0.08, by + 0.05, height(bx, by) + 0.07), (0.1, 0.1, 0.05), rot=(math.pi / 2 - 0.15, 0, 0.9), segments=10)
    kit.splat("Blood by the boot", mat("old blood"), (bx + 0.2, by - 0.15, height(bx, by)), 0.18, seed=21)
    # A root he caught his heel on.
    kit.rod("Root", mat("bark"), (7.3, 5.5, -0.05), (8.7, 6.1, -0.05), 0.07, 6)

    # ---- The old spruces in the floor: trunks she walks round, crowns high, dead branches below.
    cv, cf, sv, sf = [], [], [], []
    trunk_bases = []
    for x, y, h in STANDING:
        base = Vector((x, y, height(x, y) - 0.15))
        lift = rng.uniform(4.2, 5.5)
        spruce_crown(rng, base, h, cv, cf, lift)
        snags(rng, base, h, lift, sv, sf)
        r = h * 0.028
        t = reb.prim("cone", "Old spruce", mat("bark"), (x, y, base.z + h * 0.45), (2 * r, 2 * r, h * 0.9), segments=9, top=0.25)
        reb.mask(reb.wall(t, "circle"))
        trunk_bases.append((x, y, r))
        # Roots flaring at the foot.
        for k in range(4):
            a = rng.uniform(0, 2 * math.pi)
            reb.box(sv, sf, (x + math.cos(a) * r * 1.2, y + math.sin(a) * r * 1.2, height(x, y) + 0.04), (r * 1.6, 0.12, 0.12), rot=a)
    reb.mesh_object("Old spruce crowns", cv, cf, mat("needles"))
    dead_m = reb.mat_plain("Dead branches", (0.17, 0.15, 0.12), 0.9)
    reb.mesh_object("Dead branches", sv, sf, dead_m)
    # The torn khaki, snagged on a dead branch of the spruce by the drag.
    # (It hangs from a broken limb at the old blowdown's east end, where the drag swings past.)
    kit.rod("Snag limb", dead_m, (6.7, 3.75, 0.35), (7.35, 4.2, 1.45), 0.04, 6)
    kit.rod("Snag twig", dead_m, (7.1, 4.03, 1.05), (7.6, 4.5, 1.2), 0.02, 5)
    khaki = reb.cloth("Torn khaki", mat("khaki"), (7.5, 4.42, 0.95), (0.2, 0.42), rot=(math.pi / 2, 0.25, 0.75), cuts=8, lumps=0.04, seed=4)
    kit.splat("Blood on the khaki", mat("old blood"), (7.48, 4.4, 0.9), 0.06, rot=(math.pi / 2, 0, 0.75), seed=22)

    # ---- The blowdowns: trunks down across the floor, their root plates torn up, moss on them.
    moss = reb.mat_surface("Moss", [(0.0, (0.03, 0.05, 0.015)), (1.0, (0.08, 0.12, 0.03))], scale=6, bump=0.6)
    for i, (a, b, r) in enumerate(LOGS):
        a3 = Vector((a[0], a[1], r * 0.85))
        b3 = Vector((b[0], b[1], r * 0.75))
        reb.mask(kit.rod(f"Blowdown {i}", mat("bark"), a3, b3, r, 12))
        kit.rod(f"Moss on the blowdown {i}", moss, a3 + Vector((0, 0, r * 0.55)), b3 + Vector((0, 0, r * 0.55)), r * 0.55, 8)
        log_walls(f"Blowdown {i}", a, b, r)
        # Its root plate, standing up at the west end like a wall of earth.
        d = (b3 - a3).normalized()
        pv, pf = [], []
        reb.boulder(rng, (0, 0, 0), r * 2.4, pv, pf, squash=1.0)
        plate = reb.mesh_object(f"Root plate {i}", pv, pf, mat("mud"))
        plate.scale = (0.3, 1.0, 1.0)
        plate.location = a3 - d * 0.3 + Vector((0, 0, r * 1.3))
        plate.rotation_euler = (0, 0, math.atan2(d.y, d.x))
        reb.wall(plate)
        for k in range(6):
            q = a3 - d * 0.3 + Vector((rng.uniform(-1, 1) * r * 2, rng.uniform(-1, 1) * r * 2, rng.uniform(0, r * 3)))
            kit.rod(f"Root {i}", mat("bark"), q, q - d * rng.uniform(0.5, 1.0) + Vector((0, 0, -0.3)), 0.03, 4)
        # Broken limbs along it.
        for k in range(4 if i == 0 else 0):
            p = a3.lerp(b3, rng.uniform(0.2, 0.9))
            u = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 1)).normalized()
            kit.rod(f"Limb {i}", dead_m, p, p + u * rng.uniform(0.6, 1.4), 0.03, 5)

    # ---- The doe, opened up, her blood and the flies.
    deer = doe(DOE, 2.6)
    reb.wall(reb.prim("cube", "Doe footprint", None, (DOE[0], DOE[1], 0.3), (1.6, 1.2, 0.6), rot=(0, 0, 2.6))).hide_render = True
    kit.splat("Doe's blood", mat("old blood"), (DOE[0] - 0.1, DOE[1] - 0.2, height(*DOE)), 0.75, seed=31, stretch=(1.4, 1.0))
    kit.splat("Doe's blood, fresher", mat("blood"), (DOE[0] + 0.1, DOE[1] - 0.35, height(*DOE) + 0.002), 0.3, seed=32)
    kit.bones("Older bones", (DOE[0] + 1.4, DOE[1] - 1.1, height(DOE[0] + 1.4, DOE[1] - 1.1)), spread=0.6, seed=33, skull=False)
    reb.cloth("Tufts of hide", reb.mat_plain("Hair tufts", (0.25, 0.18, 0.12), 0.95), (DOE[0] - 0.9, DOE[1] + 0.6, height(*DOE) + 0.01), (0.5, 0.4), rot=(0, 0, 0.7), cuts=6, lumps=0.02, seed=5)

    # ---- Ferns, trampled flat along the drag, high beside the paths; deadfall, rocks, needles.
    fv, ff = [], []
    for _ in range(60):
        x, y = rng.uniform(X0 - 0.5, X1 + 0.5), rng.uniform(Y0 - 0.5, Y1 + 0.5)
        if min((Vector((x, y)) - Vector(p)).length for p in DRAG) < 1.0 or abs(y - 10) < 1.4 and x > 15:
            continue
        if any((x - cx) ** 2 + (y - cy) ** 2 < 4 for cx, cy in ((2.7, 13.4), (9.8, 2.6), (17.5, 3.4), (12.6, 6.4), (2.6, 2.6))):
            continue
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.7), fv, ff)
    for p in DRAG[2:7]:
        reb.fern(rng, (p[0] + 0.7, p[1] + 0.3, height(*p) - 0.12), 0.35, fv, ff)
    ferns = reb.mesh_object("Ferns in the floor", fv, ff, mat("ferns"))
    sticks_v, sticks_f = [], []
    for _ in range(18):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        reb.box(sticks_v, sticks_f, (x, y, height(x, y) + 0.02), (rng.uniform(0.3, 0.8), 0.03, 0.03), rot=rng.uniform(0, math.pi))
    reb.mesh_object("Deadfall", sticks_v, sticks_f, dead_m)
    nv, nf = [], []
    for _ in range(5000):
        x, y = rng.uniform(X0 - 0.5, X1 + 0.5), rng.uniform(Y0 - 0.5, Y1 + 0.5)
        reb.card(nv, nf, Vector((x, y, height(x, y) + 0.008)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.03, 0.12, 0.0)
    reb.mesh_object("Needles on the floor", nv, nf, mat("dead needles"))
    rv, rf = [], []
    for (x, y, r) in ((14.2, 13.4, 0.7), (4.4, 2.6, 0.5), (17.6, 6.4, 0.45), (10.8, 7.6, 0.35), (0.8, 4.0, 1.1), (19.5, 13.8, 1.0)):
        reb.boulder(rng, (x, y, height(x, y) - 0.1), r, rv, rf)
        if X0 < x < X1 and Y0 < y < Y1:
            reb.wall(reb.prim("cube", "Rock footprint", None, (x, y, r / 2), (r * 2, r * 1.8, r))).hide_render = True
    reb.mesh_object("Rocks", rv, rf, mat("wet rock"))
    # (the root he caught his heel on lies just proud of the needles)

    # ---- Toward the road: old stumps with the saw cut showing, a blazed tree, a survey ribbon.
    pale_wood = reb.mat_surface("Cut face", [(0.0, (0.25, 0.17, 0.09)), (1.0, (0.4, 0.3, 0.17))], scale=14, bump=0.2)
    for i, (x, y, r) in enumerate(((15.4, 12.8, 0.42), (13.6, 8.0, 0.36), (17.2, 7.0, 0.4))):
        st = reb.prim("cyl", f"Stump {i}", mat("bark"), (x, y, 0.22), (2 * r, 2 * r, 0.5), segments=10)
        reb.mask(reb.wall(st, "circle"))
        reb.prim("cyl", f"Stump top {i}", pale_wood, (x, y, 0.475), (2 * r - 0.04, 2 * r - 0.04, 0.01), rot=(0.05, 0.04, 0), segments=10)
    ex, ey = 17.3, 12.4
    blazed = reb.prim("cone", "Blazed spruce", mat("bark"), (ex, ey, 6.5), (0.8, 0.8, 13.5), segments=9, top=0.25)
    reb.mask(reb.wall(blazed, "circle"))
    bcv, bcf = [], []
    spruce_crown(rng, Vector((ex, ey, -0.2)), 15, bcv, bcf, 5.0)
    reb.mesh_object("Blazed spruce crown", bcv, bcf, mat("needles"))
    reb.prim("cube", "Blaze", reb.mat_plain("Blaze orange", (0.6, 0.18, 0.02), 0.6), (ex - 0.36, ey - 0.12, 1.5), (0.02, 0.22, 0.3), rot=(0, 0, 0.3))
    kit.text("Blaze mark", "4", mat("black"), (ex - 0.38, ey - 0.12, 1.5), size=0.18, rot=(math.pi / 2, 0, -math.pi / 2 + 0.3))
    ribbon_knot = reb.prim("sphere", "Ribbon knot", reb.mat_plain("Survey pink", (0.7, 0.08, 0.2), 0.6), (ex - 0.3, ey - 0.3, 2.0), (0.06, 0.06, 0.06))
    ribbon = reb.prim("cube", "Survey ribbon", reb.mat_plain("Survey pink", (0.7, 0.08, 0.2), 0.6), (0, -0.0, -0.3), (0.012, 0.05, 0.6))
    ribbon.parent = ribbon_knot

    # ---- The forest round it, thick, the paths kept clear.
    cams = ((2.7, 13.4), (9.8, 2.6), (17.5, 3.4), (2.6, 2.6))

    def keep_out(x, y):
        if X0 - 0.8 < x < X1 + 0.8 and Y0 - 0.8 < y < Y1 + 0.8:
            return True
        if x < X0 and abs(y - 8.2) < 1.4:
            return True
        if y < Y0 and abs(x - 9.0) < 1.6:
            return True
        if x > X1 and abs(y - 10.2) < 2.4:
            return True
        return any((x - cx) ** 2 + (y - cy) ** 2 < 9 for cx, cy in cams) or (x - 17.3) ** 2 + (y - 12.4) ** 2 < 4
    kit.forest(rng, height, keep_out, (-16, -14, 36, 32), count=150, spacing=1.7, tall=(13, 22), ferns=220, needles=1400, dead=0.1)
    far_spruces(rng, keep=lambda x, y: -16 < x < 36 and -14 < y < 32)
    def verge(r):
        while True:
            x, y = r.uniform(14.0, 24.0), r.uniform(7.5, 13.0)
            if abs(y - 10.2) > 0.95 or abs(abs(y - 10.2) - 0.0) < 0.3:
                return x, y
    grass = kit.meadow(rng, 340, verge, height)

    # ---- Light: noon under thick cloud, mist hanging in the trees; the flashlight still on.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.2, mist=((10.0, 8.0, 5.0), (80.0, 80.0, 16.0), 0.013),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.1))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(28)
    reb.spot("Light where the trees thin", (24.0, 10.0, 8.0), (14.0, 10.0, 0.0), 900, (0.8, 0.84, 0.88), 40, 0.9, 3.0)

    anim = kit.Anim(16)
    anim.flicker(beam, lens_m, depth=0.5, dropouts=3)
    anim.flicker(lens_glow, None, depth=0.5, dropouts=3)
    anim.flies((DOE[0], DOE[1], height(*DOE) + 0.3), count=14, radius=0.6)
    anim.flies((3.2, 8.4, height(3.2, 8.4) + 0.05), count=6, radius=0.35)
    anim.sway(khaki, amount=0.03, along=(0.6, 1.0), every=2, tip=1)
    anim.sway(ferns, amount=0.025)
    anim.sway(grass, amount=0.05)
    anim.swing(ribbon_knot, axis=0, degrees=25)

    # ---- What the game needs.
    room.door("yard", (X0, WEST[0], X0 + 0.6, WEST[1]), arrive=(3.6, 8.1), face=(1, 0))
    room.door("den", (NORTH[0], Y0, NORTH[1], Y0 + 0.6), arrive=(8.9, 3.6), face=(0, 1))
    room.door("logging-road", (X1 - 0.6, EAST[0], X1, EAST[1]), arrive=(16.4, 10.2), face=(-1, 0))
    room.check((2.9, 9.0, 4.1, 10.3), "Rifle brass, a handful of it. He stood here and kept shooting.")
    room.check((2.6, 7.8, 3.9, 9.0), "The needles are soaked here. This is where they got him down.")
    room.check((5.9, 6.1, 7.0, 7.1), "His flashlight. It's still on, just. The battery's nearly gone.")
    room.check((7.5, 5.4, 8.6, 6.4), "One of his boots, the laces still done up.\nHe caught his heel on the root, and they pulled him out of it.")
    room.check((6.8, 4.0, 7.9, 4.9), "A strip of khaki on a dead branch, the same as his shirt.")
    room.check((7.8, 3.0, 9.6, 4.6), "Paw prints either side of the smear. Big ones.\nThey dragged him north, into the hollow.")
    room.check((12.0, 4.6, 14.1, 6.5), "A deer. They ate her soft parts first.\nShe's been here longer than he has.")
    room.check((16.6, 11.7, 18.0, 13.2), "Orange paint on the bark, and a 4. A tree marked for felling.\nThe logging camp must be that way.")
    room.entry = "The drag marks go on into the trees. So does the blood."
    room.export(anim)


build()
