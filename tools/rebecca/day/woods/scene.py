"""The woods east of Ranger Station 3, at noon under cloud.

What it tells: last night the ranger heard the dogs, went out with his
rifle and a flashlight, and fired at them from the edge of the trees: his
brass is in the needles where he stood. They took him there. The drag marks
come in from the yard on the west side, his blood soaked into the needles
all the way, and swing north round the old blowdown, over the boards of the
old puncheon across the seep, toward the hollow where the dogs lie up. His
flashlight fell on the way and is still on, its battery nearly gone. One of
his boots came off where he caught his heel on a root, and a strip of his
green jacket is snagged on a dead branch. Big paw prints run beside the
smear. A player should work out that the ranger is somewhere north, and
that whatever took him is bigger than a coyote.

The spruce stands thick on every side, trunks in rows back into the dark
and the mist; off the paths it looks hopeless. Above the crowns is the
kit's overcast.

Metres: she walks the forest floor x 2-18, y 2-14, among old spruces whose
trunks stand in it. The yard's trail comes in at the west edge, y 7-9.
The drag marks go out at the north edge, x 7.5-10, down the trampled way to
the den, crossing a wet seep on four puncheon boards at x 7.6-9.4,
y 4.6-5.6. In the east, y 9-11.5, the trees thin into the ruts of the
logging road. A blowdown lies across the middle, x 9.5-15.5, y 9-10.6,
and an older one in the north-west, x 3-6.8, y 3.6-4.4, snapped off its
stump.

Moving: the flashlight failing, flies on the blood, the torn cloth and
the ribbon. No wind gets in under the trees: the grass and ferns stand still.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 2.0, 18.0, 2.0, 14.0
WEST = (7.0, 9.0)      # the yard's trail, y along the west edge
NORTH = (7.5, 10.0)    # the trampled way to the den, x along the north edge
EAST = (9.0, 11.5)     # the ruts, y along the east edge
# The old spruces that stand inside the floor: x, y, height.
STANDING = [(6.6, 13.3, 17), (11.4, 3.4, 18), (14.6, 2.3, 16), (11.8, 12.6, 17), (5.0, 1.5, 14), (17.3, 12.4, 15)]
# The blowdowns: from, to, radius.
LOGS = [((9.5, 10.6), (15.6, 9.0), 0.42), ((3.0, 4.4), (6.8, 3.6), 0.32)]
# The drag: in from the yard, round the old blowdown's east end, over the
# puncheon, out north.
DRAG = [(1.0, 8.2), (2.6, 8.0), (4.4, 7.6), (6.0, 7.3), (7.6, 6.6), (8.2, 5.4), (8.4, 4.0), (8.7, 2.6), (8.9, 0.8)]
# The paths, for the trees to keep off: the yard's trail in, the way north, the ruts east.
TRAIL = [(-14.0, 8.7), (-6.0, 8.5), (0.5, 8.1), (3.4, 8.0)]
WAY_NORTH = [(8.6, 3.6), (8.8, 1.4), (9.0, -2.0), (9.6, -8.0), (10.6, -16.0)]
ROAD = [(13.0, 10.3), (17.0, 10.2), (21.0, 10.0), (28.0, 9.6), (40.0, 9.0)]
# The cameras: eye, look.
CAMS = [((2.7, 13.4, 3.4), (9.0, 6.0, 0.2)), ((9.8, 2.6, 3.2), (7.4, 10.5, 0.2)), ((17.5, 3.4, 3.0), (10.5, 8.5, 0.3)),
        ((12.6, 6.4, 3.6), (18.0, 11.6, 0.0)), ((2.6, 2.6, 3.6), (11.0, 10.5, 0.2))]


def height(x, y):
    """The floor flat and just below zero; the forest floor rolling round it,
    dipping north into the hollow and rising south and west, levelling out
    far off into the kit's land."""
    n = noise.noise(Vector((x * 0.25, y * 0.25, 3.0)))
    if X0 - 0.4 < x < X1 + 0.4 and Y0 - 0.4 < y < Y1 + 0.4:
        return -0.04 + 0.03 * n
    h = 0.5 * n
    if y < Y0 - 0.4:
        h -= min(Y0 - 0.4 - y, 30.0) * (0.35 if 6.0 < x < 12.0 else 0.1)
    if y > Y1 + 0.4:
        h += min(y - Y1 - 0.4, 40.0) * 0.35
    if x < X0 - 0.4:
        h += min(X0 - 0.4 - x, 40.0) * 0.15
    if x > X1 + 0.4:
        h -= min(x - X1 - 0.4, 40.0) * 0.05
    return h


def far_land(x, y, z):
    """The kit's land, eased into the woods' own ground near the room."""
    r = math.hypot(x - 10.0, y - 8.0)
    w = max(0.0, min(1.0, (260.0 - r) / 180.0))
    return z + (height(x, y) - 0.4 - z) * w * w * (3 - 2 * w)


def near_lens(x, y, reach=4.5, around=2.0):
    """In front of a lens, where a trunk or its branches would fill the
    picture, or within `around` of it on any side."""
    for (ex, ey, _), (lx, ly, _) in CAMS:
        d = Vector((x - ex, y - ey))
        aim = Vector((lx - ex, ly - ey)).normalized()
        if d.length < around or (d.length < reach and d.normalized().dot(aim) > math.cos(math.radians(58))):
            return True
    return False


def high_crown(rng, base, h, lift, verts, faces):
    """A spruce's needles with the lower branches long dead and gone below
    `lift` metres, so a camera near it looks in under the crown."""
    v, f = [], []
    reb.conifer(rng, base, h, v, f)
    for face in f:
        if min(v[i][2] for i in face) > base.z + lift:
            k = len(verts)
            verts.extend(v[i] for i in face)
            faces.append(tuple(range(k, k + len(face))))


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


def puncheon(rng, x0, x1, y0, y1):
    """An old trail puncheon over the seep: two log sleepers sunk in the mud
    across the way, and four sawn boards laid along it, weathered grey, split
    at the ends, the nail heads rusted, one board kicked askew. Returns the
    boards, for the blood to be laid on."""
    board_m = kit.boards("Puncheon boards", (0.2, 0.17, 0.13), width=0.24, seam=0.03, grime=0.8)
    cut = reb.mat_surface("Board ends", [(0.0, (0.12, 0.09, 0.06)), (1.0, (0.26, 0.2, 0.13))], scale=30, bump=0.3)
    for i, y in enumerate((y0 + 0.15, y1 - 0.15)):
        kit.rough_log(f"Sleeper {i}", (x0 - 0.35, y, -0.1), (x1 + 0.35, y + 0.05, -0.09), 0.1, seed=40 + i, stubs=0)
    boards = []
    n = 4
    w = (x1 - x0) / n
    for i in range(n):
        cx = x0 + w * (i + 0.5) + rng.uniform(-0.02, 0.02)
        yaw = math.pi / 2 + rng.uniform(-0.03, 0.03) + (0.12 if i == 3 else 0.0)
        z = 0.022 + rng.uniform(-0.006, 0.006)
        bd = reb.prim("cube", f"Puncheon board {i}", board_m, (cx, (y0 + y1) / 2 + (0.08 if i == 3 else 0.0), z), (y1 - y0 + rng.uniform(-0.05, 0.1), w - 0.035, 0.045), rot=(rng.uniform(-0.02, 0.02), rng.uniform(-0.03, 0.03), yaw), bevel=0.008)
        boards.append(bd)
        for e in (-1, 1):
            # The split end of the board, and its nails into the sleeper.
            end = Vector((cx, (y0 + y1) / 2 + e * (y1 - y0) / 2, z))
            reb.prim("cube", f"Split {i}", cut, end + Vector((rng.uniform(-0.03, 0.03), -e * 0.004, 0.0)), (0.012, 0.004, 0.04))
            for k in (-1, 1):
                reb.prim("cyl", "Nail head", kit.mat("rust"), (cx + k * w * 0.25, end.y - e * 0.15, z + 0.024), (0.018, 0.018, 0.006), segments=6)
    return boards


def boot(at, heading, height_at):
    """His boot, on its side where it came off: a laced leather upper, the
    heel and the cleated sole toward the camera, a grey sock in it."""
    leather = reb.mat_surface("Boot leather", [(0.0, (0.035, 0.02, 0.01)), (1.0, (0.12, 0.07, 0.035))], scale=12, rough=0.55, bump=0.2)
    parts = [
        reb.prim("sphere", "toe", leather, (0.1, 0, 0.055), (0.2, 0.11, 0.1), segments=14),
        reb.prim("cube", "foot", leather, (0.0, 0, 0.055), (0.2, 0.105, 0.1), bevel=0.03),
        reb.prim("cyl", "shaft", leather, (-0.08, 0, 0.15), (0.12, 0.115, 0.22), segments=14),
        reb.prim("cyl", "sock", reb.mat_plain("Grey sock", (0.2, 0.19, 0.17), 0.9), (-0.08, 0, 0.26), (0.1, 0.095, 0.02), segments=12),
        reb.prim("cube", "sole", kit.mat("rubber"), (0.03, 0, 0.004), (0.33, 0.115, 0.02), bevel=0.006),
        reb.prim("cube", "heel", kit.mat("rubber"), (-0.1, 0, -0.012), (0.09, 0.11, 0.035)),
    ]
    for k in range(5):
        parts.append(reb.prim("cube", "lace", reb.mat_plain("Lace", (0.02, 0.015, 0.01), 0.8), (0.02 - k * 0.04, 0, 0.11 + k * 0.025), (0.012, 0.09, 0.01)))
    ob = kit.join("Ranger's boot", parts, origin=(0, 0, 0))
    ob.location = (at[0], at[1], height_at + 0.06)
    ob.rotation_euler = (math.pi / 2 - 0.1, 0, heading)
    return ob


def build():
    rng = random.Random(1998)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # forest floor
    notes = ["from the south-west: the drag in from the yard, the flashlight, the way north",
             "from the north edge looking back: the puncheon, the boot, the smear swinging round the blowdown",
             "from the north-east: the blowdown, the stumps, the drag beyond",
             "from the middle, south-east: over the blowdown to the ruts and the way out east",
             "from the north-west over the old blowdown: the casings, the drag in"]
    for (eye, look), note, fov in zip(CAMS, notes, (200, 200, 200, 200, 210)):
        room.camera(eye, look, fov, note)

    # ---- Ground: the forest floor, the yard's trail in, the ruts out east, the way north.
    floor_m = reb.mat_surface("Forest floor", [(0.0, (0.04, 0.03, 0.018)), (0.4, (0.09, 0.065, 0.04)), (0.65, (0.12, 0.085, 0.05)), (0.85, (0.06, 0.07, 0.03)), (1.0, (0.04, 0.065, 0.022))], scale=1.2, bump=0.5)
    reb.terrain("Forest floor", floor_m, (-20, 40), (-22, 38), height, step=0.4)
    reb.terrain("Far forest floor", floor_m, (-70, 90), (-70, 90), lambda x, y: height(x, y) - 0.3, step=3.0)
    on_trail = kit.dirt_path("Trail from the yard", TRAIL, height, width=0.9)
    on_way = kit.dirt_path("Trampled way north", WAY_NORTH, height, width=0.8)
    kit.path_strip("Track bed", reb.mat_plain("Track bed", (0.07, 0.055, 0.035), 0.9), ROAD, height, width=2.2, wobble=0.15, lift=0.009)
    kit.ruts("Ruts", ROAD, height, gauge=1.5, width=0.3)

    # ---- The drag: a scuffed furrow through the needles, his blood soaked in along it, prints beside it.
    kit.path_strip("Drag furrow", reb.mat_surface("Scuffed earth", [(0.0, (0.025, 0.016, 0.01)), (1.0, (0.07, 0.045, 0.028))], scale=8, rough=0.7, bump=0.6), DRAG, height, width=0.16, wobble=0.6, lift=0.006)
    # Soaked into the needles and dried dark: brown more than red, broken up.
    soaked = reb.mat_surface("Blood in the needles", [(0.25, (0.018, 0.007, 0.005)), (0.5, (0.04, 0.013, 0.008)), (0.75, (0.06, 0.022, 0.012)), (0.9, (0.05, 0.035, 0.022))], scale=30, detail=6, rough=0.95, bump=0.15)
    kit.lay_on_ground(kit.drag_trail("Blood on the needles", soaked, DRAG, width=0.3, seed=11, height=height), height, 0.012)
    kit.lay_on_ground(kit.splat("Where they took him down", soaked, (3.3, 8.3, 0), 0.3, seed=13, stretch=(1.3, 0.9), lumps=0.6), height, 0.013)
    paw_prints("Paw prints", rng, DRAG[1:], kit.mat("mud"))

    # ---- The puncheon over the seep, the drag across its boards.
    kit.lay_on_ground(kit.splat("The seep", reb.mat_plain("Seep mud", (0.012, 0.01, 0.007), 0.15), (8.5, 5.1, 0), 0.75, seed=17, stretch=(1.6, 0.8), lumps=0.4), height, 0.007)
    boards = puncheon(rng, 7.6, 9.4, 4.6, 5.6)
    for i, bd in enumerate(boards[1:3]):
        kit.splat(f"Blood in the boards {i}", soaked, (bd.location.x + 0.03, 5.0 - 0.2 * i, bd.location.z + 0.0245), 0.07, seed=18 + i, stretch=(0.8, 1.6), lumps=0.9)

    # What he dropped: brass where he stood, the flashlight, a boot, his jacket.
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
    bx, by = 7.9, 6.2
    boot((bx, by), 0.9, height(bx, by))
    # A root he caught his heel on, running out from the spruce by the drag.
    kit.rough_log("Root", (7.1, 5.6, -0.06), (8.7, 6.4, -0.05), 0.06, seed=3, stubs=0)

    # ---- The old spruces in the floor: trunks she walks round, crowns high, roots in the needles.
    cv, cf = [], []
    bases = []
    for x, y, h in STANDING:
        base = Vector((x, y, height(x, y) - 0.2))
        high_crown(rng, base, h, 6.5, cv, cf)
        bases.append((base, h))
        r = h * 0.03 * 1.25
        reb.mask(reb.wall(reb.prim("cyl", "Old spruce footprint", None, (x, y, 1.0), (2 * r, 2 * r, 2.0), segments=8), "circle")).hide_render = True
    reb.mesh_object("Old spruce crowns", cv, cf, kit.mat("needles"))
    trunks = reb.trunks("Old spruce trunks", kit.mat("bark"), bases)
    reb.mask(trunks)
    kit.tree_roots(rng, bases, height, lambda x, y: on_trail(x, y) or on_way(x, y))
    # The torn green cloth, caught on a branch stub at the old blowdown's east end.
    jacket = reb.mat_surface("Ranger jacket", [(0.0, tuple(c * 0.55 for c in kit.UNIFORM["jacket"])), (1.0, tuple(c * 1.3 for c in kit.UNIFORM["jacket"]))], scale=30, bump=0.25)
    torn = reb.cloth("Torn jacket", jacket, (6.6, 3.72, 0.62), (0.36, 0.2), rot=(0.5, 0.15, 0.2), cuts=8, lumps=0.04, seed=4)

    # ---- The blowdowns: rough trunks down across the floor, the old one snapped off its stump.
    for i, (a, b, r) in enumerate(LOGS):
        a3 = Vector((a[0], a[1], height(*a) + r * 0.7))
        b3 = Vector((b[0], b[1], height(*b) + r * 0.6))
        reb.mask(kit.rough_log(f"Blowdown {i}", a3, b3, r, seed=7 + i, stubs=7 if i == 0 else 4))
        # Its stump at the west end, splintered where it went over.
        d = (b3 - a3).normalized()
        sx, sy = a[0] - d.x * 0.5, a[1] - d.y * 0.5
        stump = kit.rough_log(f"Snapped stump {i}", (sx, sy, height(sx, sy) - 0.4), (sx + 0.05, sy - 0.04, height(sx, sy) + 0.75 + 0.2 * i), r * 1.15, seed=20 + i, stubs=0)
        reb.mask(reb.wall(stump, "circle"))
        kit.tree_roots(rng, [(Vector((sx, sy, height(sx, sy) - 0.1)), 14)], height)

    # ---- Ferns, trampled flat along the drag, high beside the paths; deadfall, rocks.
    fv, ff = [], []
    for _ in range(70):
        x, y = rng.uniform(X0 - 0.5, X1 + 0.5), rng.uniform(Y0 - 0.5, Y1 + 0.5)
        if min((Vector((x, y)) - Vector(p)).length for p in DRAG) < 1.0 or abs(y - 10) < 1.4 and x > 15:
            continue
        if near_lens(x, y, 3.0) or 7.3 < x < 9.7 and 4.3 < y < 5.9:
            continue
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.7), fv, ff)
    for p in DRAG[2:7]:
        reb.fern(rng, (p[0] + 0.7, p[1] + 0.3, height(*p) - 0.12), 0.35, fv, ff)
    reb.mesh_object("Ferns in the floor", fv, ff, kit.mat("ferns"))
    for k in range(5):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        if near_lens(x, y, 3.0) or min((Vector((x, y)) - Vector(p)).length for p in DRAG) < 0.8:
            continue
        a = rng.uniform(0, math.pi)
        length = rng.uniform(0.6, 1.4)
        kit.rough_log(f"Deadfall {k}", (x, y, height(x, y) + 0.01), (x + math.cos(a) * length, y + math.sin(a) * length, height(x, y) + 0.03), rng.uniform(0.05, 0.08), seed=80 + k, stubs=2)
    # Needle litter: fine and close in colour to the floor, so it reads as
    # the floor's own texture, not as sticks lying on it.
    nv, nf = [], []
    for _ in range(9000):
        x, y = rng.uniform(X0 - 0.5, X1 + 0.5), rng.uniform(Y0 - 0.5, Y1 + 0.5)
        reb.card(nv, nf, Vector((x, y, height(x, y) + 0.008)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.012, 0.05, 0.0)
    reb.mesh_object("Needles on the floor", nv, nf, reb.mat_cards("Needle litter", (0.06, 0.045, 0.025), (0.11, 0.08, 0.04)))
    # Moss and grass in drifts over the needles where light gets down,
    # never on the drag or the paths, so no stretch of floor is bald.
    def bare(x, y, margin=0.0):
        if min((Vector((x, y)) - Vector(p)).length for p in DRAG) < 0.5 + margin:
            return True
        if on_trail(x, y, 0.3) or on_way(x, y, 0.3) or kit.path_distance(x, y, [ROAD]) < 1.5:
            return True
        return 7.3 < x < 9.7 and 4.3 < y < 5.9
    kit.grass_ground(rng, (X0 - 3, Y0 - 3, X1 + 3, Y1 + 3), height, per_m2=9,
                     keep_out=lambda x, y: bare(x, y) or noise.noise(Vector((x * 0.35, y * 0.35, 8.0))) < -0.1)
    kit.grass_ground(rng, (X0 - 3, Y0 - 3, X1 + 3, Y1 + 3), height, per_m2=3, m=kit.mat("dead grass"),
                     keep_out=lambda x, y: bare(x, y))
    rock = reb.mat_surface("Mossy rock", [(0.0, (0.03, 0.04, 0.025)), (0.5, (0.08, 0.08, 0.07)), (1.0, (0.14, 0.13, 0.11))], scale=3, bump=0.9)
    spots = [(14.2, 13.4, 0.7), (4.4, 2.6, 0.5), (17.6, 6.4, 0.45), (10.8, 7.6, 0.35), (0.8, 4.0, 1.1), (19.5, 13.8, 1.0)]
    kit.rocks("Rocks", rng, spots, height, rock)

    # ---- Toward the road: old stumps with the saw cut showing, a blazed tree, a survey ribbon.
    pale_wood = reb.mat_surface("Cut face", [(0.0, (0.2, 0.14, 0.08)), (1.0, (0.34, 0.25, 0.14))], scale=14, bump=0.2)
    stump_bases = []
    for i, (x, y, r) in enumerate(((15.4, 12.8, 0.42), (13.6, 8.0, 0.36), (17.2, 7.0, 0.4))):
        st = reb.prim("cyl", f"Stump {i}", kit.mat("bark"), (x, y, 0.1), (2 * r, 2 * r, 0.75), segments=11)
        reb.mask(st)
        reb.prim("cyl", f"Stump top {i}", pale_wood, (x, y, 0.475), (2 * r - 0.04, 2 * r - 0.04, 0.01), rot=(0.05, 0.04, 0), segments=11)
        stump_bases.append((Vector((x, y, height(x, y) - 0.1)), 12))
    kit.tree_roots(rng, stump_bases, height)
    ex, ey = 17.3, 12.4
    reb.prim("cube", "Blaze", reb.mat_plain("Blaze orange", (0.45, 0.12, 0.015), 0.6), (ex - 0.25, ey - 0.12, 1.5), (0.02, 0.2, 0.28), rot=(0, 0, 0.3))
    ribbon_knot = reb.prim("sphere", "Ribbon knot", reb.mat_plain("Survey pink", (0.55, 0.06, 0.15), 0.6), (ex - 0.22, ey - 0.3, 2.0), (0.06, 0.06, 0.06))
    ribbon = reb.prim("cube", "Survey ribbon", reb.mat_plain("Survey pink", (0.55, 0.06, 0.15), 0.6), (0, -0.0, -0.3), (0.012, 0.05, 0.6))
    ribbon.parent = ribbon_knot

    # ---- The forest round it, thick, trunks in rows back into the mist, the paths kept clear.
    def no_tree(x, y):
        if X0 - 0.8 < x < X1 + 0.8 and Y0 - 0.8 < y < Y1 + 0.8:
            return True
        if on_trail(x, y, 1.3) or on_way(x, y, 1.3) or kit.path_distance(x, y, [ROAD]) < 2.4:
            return True
        return near_lens(x, y, 9.0, 4.5)
    kit.forest(rng, height, no_tree, (-22, -24, 42, 40), count=380, spacing=1.6, tall=(14, 23), ferns=260, needles=500, dead=0.08)
    # Thicker close round the floor, so the trunks stand in rows.
    kit.forest(rng, height, no_tree, (-6, -8, 26, 22), count=170, spacing=1.25, tall=(13, 21), ferns=80, needles=200, dead=0.05)
    kit.far_spruces(rng, height, keep_out=lambda x, y: -22 < x < 42 and -24 < y < 40 or kit.path_distance(x, y, [ROAD]) < 2.5, count=1100, area=(-75, -75, 95, 95))

    def verge(r):
        while True:
            x, y = r.uniform(14.0, 26.0), r.uniform(7.5, 13.0)
            if kit.path_distance(x, y, [ROAD]) > 0.25:
                return x, y
    kit.meadow(rng, 500, verge, height)

    # ---- Light: noon under thick cloud, mist hanging in the trees; the flashlight still on.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.6, mist=((10.0, 8.0, 5.0), (90.0, 90.0, 18.0), 0.011),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.3))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(28)
    kit.overcast_sky()
    kit.backdrop((10.0, 8.0, 3.2), spread=360, below=-6.0, near=70.0, forest_to=1500.0, trees=60000,
                 keep_out=lambda x, y: math.hypot(x - 10.0, y - 8.0) < 75, shape=far_land, mist=25.0, rng=random.Random(9))
    reb.spot("Cloud light into the floor", (10.0, 8.0, 14.0), (10.0, 8.0, 0.0), 9000, (0.82, 0.85, 0.9), 120, 1, 6)
    reb.spot("Light where the trees thin", (24.0, 10.0, 8.0), (14.0, 10.0, 0.0), 900, (0.8, 0.84, 0.88), 40, 0.9, 3.0)

    anim = kit.Anim(16)
    anim.flicker(beam, lens_m, depth=0.5, dropouts=3)
    anim.flicker(lens_glow, None, depth=0.5, dropouts=3)
    anim.flies((3.3, 8.3, height(3.3, 8.3) + 0.05), count=6, radius=0.35)
    anim.flies((8.5, 5.1, 0.1), count=5, radius=0.3)
    anim.sway(torn, amount=0.03, along=(0.6, 1.0), every=2, tip=1)
    anim.swing(ribbon_knot, axis=0, degrees=12)

    # ---- What the game needs.
    room.door("yard", (X0, WEST[0], X0 + 0.6, WEST[1]), arrive=(3.6, 8.1), face=(1, 0))
    room.door("den", (NORTH[0], Y0, NORTH[1], Y0 + 0.6), arrive=(8.9, 3.6), face=(0, 1))
    room.door("logging-road", (X1 - 0.6, EAST[0], X1, EAST[1]), arrive=(16.4, 10.2), face=(-1, 0))
    room.check((2.9, 9.0, 4.1, 10.3), "Rifle brass, a handful of it. He stood here and kept shooting.")
    room.check((2.6, 7.8, 3.9, 9.0), "The needles are soaked here. This is where they got him down.")
    room.check((5.9, 6.1, 7.0, 7.1), "His flashlight. It's still on, just. The battery's nearly gone.")
    room.check((7.4, 5.7, 8.5, 6.7), "One of his boots, the laces still done up.\nHe caught his heel on the root, and they pulled him out of it.")
    room.check((6.2, 3.5, 7.4, 4.5), "A strip of green cloth caught on the log. Forest Service green.")
    room.check((7.8, 3.0, 9.6, 4.5), "Paw prints either side of the smear. Big ones.\nThey dragged him north, into the hollow.")
    room.check((7.6, 4.6, 9.4, 5.6), "Old boards over the wet ground. They dragged him straight across them.")
    room.check((16.6, 11.7, 18.0, 13.2), "Orange paint on the bark. A tree marked for felling.\nThe loggers must be that way.")
    room.export(anim)


build()
