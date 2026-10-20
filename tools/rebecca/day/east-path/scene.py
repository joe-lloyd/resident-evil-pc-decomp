"""The east path from the gondola station, a harsh late afternoon.

What it tells: Hal came this way at dawn, bitten, with the drive key. The
blood drips start at the west edge where the trail comes in from the
station, run along the path past the bench, and turn up to his cottage
door, where his hand is on the frame. Somewhere on the path he dropped his
thermos and never went back for it: the cup rolled into the grass and the
coffee dried. Then the drips come out of the cottage again and go on east,
fewer now, toward the quarry, and a bloody rag lies where he wrapped his
hand a second time. The cottage is a working man's place: logs stacked
under the eaves, the axe in the block, shirts still on the line. The
station's windsock on its pole by the drop still swings in the wind off
the valley, and the bench looks out over all of it. The crows are working
along the drips.

Metres: the floor is x 1.0-18.5, y 1.5-12.0 at z 0. The path comes in at
the west edge at y 6.5-8.5 and leaves at the east edge at y 7-9, curving
south past the bench (x 4.2-5.8, y 11.2) and the windsock (x 14.6, y 10.8).
The cottage stands back from the path, x 7.0-11.4, y 0.6-4.0, its door in
the south wall at x 8.6-9.5. The woodpile is against its west wall, the
water butt at its south-east corner, the clothes line from its east wall to
a pole at x 14.2, y 2.4. A rail fence runs along the drop at y 12.4; south
of it the mountain falls away to the valley.

Moving: the windsock on its pole, the shirts on the line, the grass, a crow
pecking at the drips.
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

X0, X1, Y0, Y1 = 1.0, 18.5, 1.5, 12.0
COT = (7.0, 11.4, 0.6, 4.0)
COT_DOOR = (8.6, 9.5)
WALL_H = 2.4
PATH = [(-6.0, 7.6), (1.0, 7.5), (4.0, 7.3), (6.5, 6.9), (9.0, 6.6), (11.5, 6.8), (14.0, 7.4), (16.5, 7.9), (18.5, 8.0), (25.0, 8.4)]
SOCK = (14.6, 10.8)



def height(x, y):
    """Flat where she walks; the slope rising north behind the cottage, the drop south of the fence."""
    h = 0.04 * noise.noise(Vector((x * 0.4, y * 0.4, 3)))
    if X0 - 0.8 < x < X1 + 0.8 and Y0 - 1.2 < y < Y1 + 0.5:
        return h - 0.02
    h += 0.4 * noise.noise(Vector((x * 0.15, y * 0.15, 1)))
    if y < Y0 - 1.2:
        h += (Y0 - 1.2 - y) * 0.75
    if y > Y1 + 0.5:
        h -= (y - Y1 - 0.5) ** 1.3 * 1.4
    return h


def drips(name, m, pts, rng, r=(0.02, 0.05), z=0.0):
    """Blood drops along a line of points, in one mesh."""
    v, f = [], []
    for x, y in pts:
        kit._stain(v, f, rng, (x, y, z + 0.005), rng.uniform(*r), rng.uniform(0, 6.3), 0.45, (1.0, 1.0), rng.randint(0, 99), points=10, drops=rng.random() < 0.35)
    return reb.mesh_object(name, v, f, m, smooth=False)


def along(path, step, rng, jitter=0.12, skip=0.0):
    """Points every `step` metres along a polyline, a little off the line."""
    out = []
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        a, b = Vector((ax, ay)), Vector((bx, by))
        n = max(1, int((b - a).length / step))
        for i in range(n):
            if rng.random() < skip:
                continue
            p = a.lerp(b, (i + rng.uniform(0, 0.6)) / n)
            out.append((p.x + rng.uniform(-jitter, jitter), p.y + rng.uniform(-jitter, jitter)))
    return out


def build():
    rng = random.Random(23)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # grass and the dirt path
    room.camera((1.6, 11.6, 3.5), (9.0, 5.0, 0.6), 200, "from the west end by the fence: the path in, the thermos, the cottage set back")
    room.camera((17.8, 3.2, 3.7), (9.0, 10.0, 0.9), 200, "from the north-east corner: the drips going on east, the windsock, the bench and the valley")
    room.camera((10.6, 11.7, 3.0), (9.4, 3.6, 1.1), 200, "from the fence below the cottage: its front, the open door, the hand on the frame")
    room.camera((2.0, 4.6, 3.8), (14.5, 9.0, 0.2), 200, "from beside the woodpile: the length of the path east toward the quarry")

    planks = kit.boards("Cottage boards", (0.2, 0.15, 0.1), width=0.2, grime=0.75)
    trim = reb.mat_wood("Trim", (0.12, 0.08, 0.05))
    shingle = reb.mat_surface("Tar shingle", [(0.0, (0.03, 0.03, 0.03)), (0.7, (0.07, 0.065, 0.06)), (1.0, (0.12, 0.1, 0.07))], scale=9, rough=0.85, bump=0.6)
    stone = reb.mat_surface("Fieldstone", [(0.0, (0.1, 0.1, 0.09)), (0.5, (0.22, 0.21, 0.19)), (1.0, (0.3, 0.28, 0.25))], scale=6, bump=1.0)
    dark = reb.mat_plain("Indoors dark", (0.012, 0.01, 0.008), 0.9)
    coffee = reb.mat_plain("Dried coffee", (0.05, 0.03, 0.015), 0.4)
    sock_m = reb.mat_stripes("Windsock", [(0.6, 0.18, 0.03), (0.6, 0.58, 0.52)], across=4.0, axis="Z")

    # ---- Ground: the shelf of grass the path crosses, the slope behind, the drop in front.
    reb.terrain("Hillside", mat("grass"), (-16, 36), (-18, 34), height, step=0.6)
    kit.path_strip("Path", mat("dirt"), PATH, height, width=0.75)
    kit.path_strip("Path to the door", mat("dirt"), [(9.05, 6.7), (9.05, 5.4), (9.05, 4.5)], height, width=0.45)
    kit.path_strip("Path worn", mat("mud"), PATH[1:-1], height, width=0.35, lift=0.012)

    # ---- The cottage: plank walls, a tar roof, a stone chimney, the door ajar.
    cx0, cx1, cy0, cy1 = COT
    for ob in kit.walls(cx0, cy0, cx1, cy1, WALL_H, planks, openings=[
        ("s", COT_DOOR[0], COT_DOOR[1], 0.0, 2.0),
        ("s", 7.55, 8.25, 1.0, 1.8),
        ("s", 10.15, 10.85, 1.0, 1.8),
        ("e", 1.6, 2.4, 1.05, 1.75),
    ], name="Cottage wall"):
        reb.wall(ob)
    reb.prim("cube", "Cottage inside", dark, ((cx0 + cx1) / 2, (cy0 + cy1) / 2 - 0.25, 1.2), (cx1 - cx0 - 0.2, cy1 - cy0 - 0.8, 2.3))
    ridge_z, eave = 3.55, 0.35
    half = (cy1 - cy0) / 2 + eave
    rise = ridge_z - WALL_H + eave * (ridge_z - WALL_H) / ((cy1 - cy0) / 2)
    pitch = math.atan2(ridge_z - WALL_H, (cy1 - cy0) / 2)
    run = half / math.cos(pitch)
    mid_y = (cy0 + cy1) / 2
    for side in (-1, 1):
        reb.prim("cube", "Roof", shingle, ((cx0 + cx1) / 2, mid_y + side * half / 2, ridge_z - rise / 2 + 0.06), (cx1 - cx0 + 0.7, run, 0.08), rot=(-side * pitch, 0, 0))
    reb.prim("cube", "Ridge board", trim, ((cx0 + cx1) / 2, mid_y, ridge_z + 0.1), (cx1 - cx0 + 0.75, 0.16, 0.08))
    for x in (cx0 - 0.12, cx1 + 0.12):
        reb.mesh_object("Gable", [(x, cy0 - 0.12, WALL_H), (x, cy1 + 0.12, WALL_H), (x, mid_y, ridge_z)], [(0, 1, 2)], planks, smooth=False)
    for x in (cx0 - 0.3, cx1 + 0.3):
        for side in (-1, 1):
            kit.rod("Barge board", trim, (x, mid_y, ridge_z + 0.05), (x, mid_y + side * (half + 0.02), WALL_H - eave * math.tan(pitch) + 0.02), 0.04, 6)
    chim = reb.prim("cube", "Chimney", stone, (cx1 + 0.35, mid_y + 0.4, 2.1), (0.6, 0.7, 4.2))
    reb.wall(chim)
    reb.prim("cube", "Chimney cap", mat("concrete"), (cx1 + 0.35, mid_y + 0.4, 4.24), (0.7, 0.8, 0.08))
    # Corner posts and the sill beam, so the walls stand on something.
    for x in (cx0 - 0.1, cx1 + 0.1):
        for y in (cy0 - 0.1, cy1 + 0.1):
            reb.prim("cube", "Corner post", trim, (x, y, WALL_H / 2), (0.14, 0.14, WALL_H))
    reb.prim("cube", "Sill beam", stone, ((cx0 + cx1) / 2, cy1 + 0.08, 0.08), (cx1 - cx0 + 0.4, 0.2, 0.2))
    # Windows: grimy glass, a curtain behind the west one, a crack in the east one.
    for i, (wx0, wx1) in enumerate(((7.55, 8.25), (10.15, 10.85))):
        reb.prim("cube", f"Window {i}", reb.mat_glass("Grimy glass", (0.4, 0.42, 0.38)), ((wx0 + wx1) / 2, cy1 + 0.05, 1.4), (wx1 - wx0, 0.01, 0.8))
        reb.prim("cube", f"Window cross {i}", trim, ((wx0 + wx1) / 2, cy1 + 0.07, 1.4), (0.04, 0.03, 0.8))
        reb.prim("cube", f"Window bar {i}", trim, ((wx0 + wx1) / 2, cy1 + 0.07, 1.4), (wx1 - wx0, 0.03, 0.04))
        reb.prim("cube", f"Window sill {i}", trim, ((wx0 + wx1) / 2, cy1 + 0.12, 0.97), (wx1 - wx0 + 0.16, 0.14, 0.05))
        for dx in (-1, 1):
            reb.prim("cube", f"Shutter {i}", reb.mat_plain("Shutter green", (0.05, 0.1, 0.06), 0.7), ((wx0 + wx1) / 2 + dx * ((wx1 - wx0) / 2 + 0.2), cy1 + 0.1, 1.4), (0.36, 0.03, 0.85))
    reb.cloth("Curtain", reb.mat_plain("Curtain", (0.32, 0.26, 0.15), 0.9), (7.9, cy1 - 0.06, 1.4), (0.7, 0.8), rot=(math.pi / 2, 0, 0), cuts=10, lumps=0.03, seed=4)
    for i in range(6):
        a = i * 1.05 + rng.uniform(-0.2, 0.2)
        kit.rod("Window crack", reb.mat_plain("Crack", (0.75, 0.78, 0.8), 0.3), (10.6, cy1 + 0.04, 1.55), (10.6 + math.cos(a) * 0.25, cy1 + 0.04, 1.55 + math.sin(a) * 0.25), 0.003, 4)
    # The door, standing ajar inward, its frame, the step, the hand.
    d0, d1 = COT_DOOR
    for x in (d0 - 0.05, d1 + 0.05):
        reb.prim("cube", "Door frame", trim, (x, cy1 + 0.02, 1.02), (0.08, 0.18, 2.04))
    reb.prim("cube", "Door head", trim, ((d0 + d1) / 2, cy1 + 0.02, 2.05), (d1 - d0 + 0.2, 0.18, 0.1))
    reb.prim("cube", "Cottage door", kit.boards("Door boards", (0.16, 0.08, 0.05), width=0.13), (d1 - 0.42 * math.cos(0.75), cy1 - 0.42 * math.sin(0.75), 1.0), (0.86, 0.05, 1.98), rot=(0, 0, 0.75))
    step = reb.prim("cube", "Door step", stone, ((d0 + d1) / 2, cy1 + 0.35, 0.07), (1.3, 0.5, 0.14), bevel=0.02)
    kit.splat("Hand on the frame", mat("blood"), (d0 - 0.06, cy1 + 0.115, 1.25), 0.065, rot=(math.pi / 2, 0, 0), seed=5, lumps=0.5)
    reb.prim("cube", "Smear down the frame", mat("old blood"), (d0 - 0.06, cy1 + 0.114, 0.95), (0.05, 0.004, 0.5), rot=(0, 0.05, 0))
    kit.splat("Blood on the step", mat("old blood"), ((d0 + d1) / 2 + 0.1, cy1 + 0.35, 0.145), 0.12, seed=6, stretch=(1.3, 0.8))
    # A lamp bracket by the door, a horseshoe over it, his boots scraper.
    reb.prim("cube", "Lamp bracket", mat("iron"), (d1 + 0.35, cy1 + 0.12, 2.0), (0.04, 0.25, 0.04))
    lamp, lamp_light, lamp_flame = kit.lantern("Porch lamp", (d1 + 0.35, cy1 + 0.25, 1.6), energy=0.0, hanging=True)
    reb.prim("cube", "Boot scraper", mat("iron"), (d0 - 0.4, cy1 + 0.35, 0.08), (0.35, 0.04, 0.16))
    # The woodpile against the west wall, under the eaves; the block and the axe.
    logs_m = mat("logs")
    log_parts = []
    for row in range(5):
        for k in range(9):
            y = cy0 + 0.25 + k * 0.36 + (0.18 if row % 2 else 0)
            if y > cy1 - 0.1:
                continue
            log_parts.append(reb.prim("cyl", "Log", logs_m, (cx0 - 0.5, y, 0.17 + row * 0.31), (0.32, 0.32, 0.62), rot=(0, math.pi / 2, rng.uniform(-0.05, 0.05)), segments=10))
    pile = kit.join("Woodpile", log_parts)
    reb.wall(pile)
    reb.prim("cube", "Woodpile roof", mat("tin"), (cx0 - 0.5, (cy0 + cy1) / 2, 1.85), (0.9, cy1 - cy0 + 0.3, 0.04), rot=(0, -0.25, 0))
    blk = reb.prim("cyl", "Chopping block", logs_m, (5.6, 4.7, 0.25), (0.55, 0.55, 0.5), segments=14)
    reb.wall(blk, "circle")
    kit.rod("Axe haft", reb.mat_wood("Haft", (0.35, 0.25, 0.14)), (5.62, 4.68, 0.48), (5.95, 4.95, 1.05), 0.022)
    reb.prim("cube", "Axe head", mat("steel"), (5.6, 4.66, 0.52), (0.04, 0.2, 0.12), rot=(0, 0, 0.7))
    split = [reb.prim("cube", "Split wood", logs_m, (5.1 + rng.uniform(-0.4, 0.4), 4.9 + rng.uniform(-0.3, 0.4), 0.05), (0.4, 0.12, 0.1), rot=(0, 0, rng.uniform(0, 3))) for _ in range(9)]
    kit.join("Split wood", split)
    kit.splat("Chips", reb.mat_plain("Wood chips", (0.32, 0.24, 0.14), 0.9), (5.4, 4.9, 0.0), 0.6, seed=12, lumps=0.6)
    # The water butt at the corner, a tin bath on a nail, the clothes line.
    butt = reb.prim("cyl", "Water butt", mat("logs"), (cx1 + 0.45, cy1 + 0.25, 0.45), (0.65, 0.65, 0.9), segments=16)
    reb.wall(butt, "circle")
    for z in (0.15, 0.75):
        reb.prim("cyl", "Butt hoop", mat("rust"), (cx1 + 0.45, cy1 + 0.25, z), (0.67, 0.67, 0.04), segments=16)
    reb.prim("cyl", "Butt water", reb.mat_plain("Butt water", (0.01, 0.012, 0.01), 0.05), (cx1 + 0.45, cy1 + 0.25, 0.86), (0.6, 0.6, 0.01), segments=16)
    reb.prim("cyl", "Tin bath", mat("tin"), (cx1 + 0.08, 1.2, 1.2), (0.9, 0.9, 0.25), rot=(0, math.pi / 2, 0), segments=18)
    line_a, line_b = Vector((cx1 + 0.12, 3.2, 1.9)), Vector((14.2, 2.4, 1.9))
    pole = kit.rod("Line pole", trim, (14.2, 2.4, 0), (14.2, 2.4, 2.05), 0.05)
    reb.wall(pole, "circle")
    kit.rod("Clothes line", mat("black"), line_a, line_b, 0.006, 4)
    hangers = []
    for i, (t, col, w, h) in enumerate(((0.25, mat("flannel"), 0.55, 0.7), (0.5, reb.mat_plain("Long johns", (0.5, 0.45, 0.36), 0.9), 0.4, 0.95), (0.75, mat("denim"), 0.5, 0.6))):
        p = line_a.lerp(line_b, t) - Vector((0, 0, 0.03))
        peg = reb.prim("sphere", f"Peg {i}", trim, p, (0.03, 0.03, 0.03))
        cl = reb.cloth(f"Washing {i}", col, (0, 0, -h / 2), (w, h), rot=(math.pi / 2, 0, math.atan2(line_b.y - line_a.y, line_b.x - line_a.x)), cuts=8, lumps=0.03, seed=i)
        cl.parent = peg
        hangers.append(peg)

    # ---- Along the path: the bench with the view, the sign, the thermos, the fence by the drop.
    bench_m = reb.mat_wood("Bench slats", (0.22, 0.15, 0.09))
    bench = kit.table("Bench", bench_m, (5.0, 11.2, 0.0), size=(1.7, 0.42, 0.45), legs_mat=mat("iron"))
    reb.wall(bench)
    reb.prim("cube", "Bench back", bench_m, (5.0, 11.4, 0.8), (1.7, 0.05, 0.3), rot=(0.15, 0, 0))
    for x in (4.25, 5.75):
        reb.prim("cube", "Bench back post", mat("iron"), (x, 11.38, 0.6), (0.04, 0.04, 0.5))
    reb.prim("cube", "Bench plaque", mat("steel"), (5.0, 11.37, 0.8), (0.25, 0.01, 0.07), rot=(0.15, 0, 0))
    # The fork sign: back to the station, on to the quarry and the mine.
    kit.rod("Sign post", trim, (12.6, 5.7, 0), (12.6, 5.7, 2.0), 0.05)
    reb.wall(reb.prim("cube", "Sign post foot", None, (12.6, 5.7, 0.5), (0.12, 0.12, 1.0))).hide_render = True
    for i, (words, z, dx) in enumerate((("SKYWAY >", 1.8, -0.35), ("< QUARRY", 1.55, 0.35), ("< OLD MINE", 1.32, 0.35))):
        reb.prim("cube", f"Sign arm {i}", mat("planks"), (12.6 + dx, 5.74, z), (1.0, 0.04, 0.18))
        kit.text(f"Sign words {i}", words, mat("white paint"), (12.6 + dx, 5.765, z), size=0.1, rot=(math.pi / 2, 0, math.pi))
    kit.splat("Hand on the sign post", mat("old blood"), (12.6, 5.755, 1.05), 0.04, rot=(math.pi / 2, 0, 0), seed=9)
    # His thermos, dropped, and its cup in the grass.
    reb.prim("cyl", "Thermos", mat("green paint"), (4.3, 7.15, 0.06), (0.11, 0.11, 0.34), rot=(math.pi / 2, 0, 0.4), segments=14)
    reb.prim("cyl", "Thermos cap", mat("steel"), (4.37, 6.98, 0.06), (0.1, 0.1, 0.04), rot=(math.pi / 2, 0, 0.4), segments=14)
    reb.prim("cyl", "Thermos cup", reb.mat_plain("Cup red", (0.3, 0.05, 0.03), 0.5), (4.85, 7.75, 0.045), (0.09, 0.09, 0.08), rot=(math.pi / 2, 0, 1.9), segments=12)
    kit.splat("Coffee", coffee, (4.1, 7.05, 0.0), 0.25, seed=3, stretch=(1.6, 0.8))
    # The fence along the drop, one rail down.
    fence_m = mat("planks")
    posts = []
    for i, x in enumerate([0.2 + 2.1 * k for k in range(10)]):
        posts.append(reb.prim("cube", "Fence post", fence_m, (x, Y1 + 0.4, 0.55), (0.12, 0.12, 1.15), rot=(rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0)))
    rails = []
    for i in range(9):
        x0, x1 = 0.2 + 2.1 * i, 0.2 + 2.1 * (i + 1)
        for z in (0.55, 0.98):
            if i == 6 and z > 0.9:
                rails.append(reb.prim("cube", "Fallen rail", fence_m, ((x0 + x1) / 2, Y1 + 0.75, 0.05), (2.1, 0.08, 0.08), rot=(0, 0, 0.15)))
                continue
            rails.append(reb.prim("cube", "Fence rail", fence_m, ((x0 + x1) / 2, Y1 + 0.43, z), (2.15, 0.06, 0.1)))
    kit.join("Fence", posts + rails)

    # ---- The windsock by the drop: a mast, a ring, the striped sock streaming east.
    sx, sy = SOCK
    mast = kit.rod("Windsock mast", mat("steel"), (sx, sy, 0), (sx, sy, 5.0), 0.05)
    reb.wall(mast, "circle")
    reb.prim("cyl", "Mast footing", mat("concrete"), (sx, sy, 0.05), (0.5, 0.5, 0.12), segments=12)
    sock_pivot = reb.prim("sphere", "Sock swivel", mat("steel"), (sx, sy, 4.85), (0.08, 0.08, 0.08))
    ring = reb.prim("cyl", "Sock ring", mat("steel"), (0.1, 0, 0), (0.42, 0.42, 0.03), rot=(0, math.pi / 2, 0), segments=16)
    sock = reb.prim("cone", "Windsock", sock_m, (0.85, 0, -0.12), (0.4, 0.4, 1.5), rot=(0, math.pi / 2 + 0.16, 0), segments=16, top=0.55)
    ring.parent = sock_pivot
    sock.parent = sock_pivot
    sock_pivot.rotation_euler = (0, 0, 0.35)
    kit.rod("Mast stay", mat("iron"), (sx, sy, 3.5), (sx + 1.6, sy - 1.0, 0), 0.008, 4)
    kit.rod("Mast stay", mat("iron"), (sx, sy, 3.5), (sx - 1.6, sy - 1.0, 0), 0.008, 4)
    reb.prim("cube", "Mast sign", mat("white paint"), (sx, sy - 0.05, 1.5), (0.4, 0.02, 0.28))
    kit.text("Mast sign words", "WIND\nSKYWAY", mat("red paint"), (sx, sy - 0.065, 1.5), size=0.075, rot=(math.pi / 2, 0, 0))

    # ---- Hal's blood: drips from the station to his door, and out again, east, fewer.
    in_path = [(X0, 7.55), (4.0, 7.35), (6.5, 6.95), (8.6, 6.65), (9.0, 5.6), (9.0, 4.55)]
    out_path = [(9.3, 4.6), (9.4, 5.8), (10.5, 6.75), (13.0, 7.2), (15.5, 7.75), (X1, 8.0)]
    drips("Drips to the door", mat("blood"), along(in_path, 0.32, rng), rng)
    drips("Drips going on", mat("old blood"), along(out_path, 0.45, rng, skip=0.35), rng, r=(0.015, 0.035))
    kit.splat("Where he stood", mat("blood"), (8.95, 5.0, 0.0), 0.16, seed=14, lumps=0.5)
    reb.cloth("Bloody rag", reb.mat_surface("Bloody rag", [(0.0, (0.4, 0.36, 0.3)), (0.5, (0.25, 0.03, 0.02)), (1.0, (0.1, 0.005, 0.004))], scale=10), (15.1, 7.25, 0.015), (0.3, 0.2), rot=(0, 0, 0.7), cuts=8, lumps=0.02, seed=6)

    # ---- The slope round it: spruces up behind, boulders, long grass on the shelf.
    def keep_out(x, y):
        return ((X0 - 1.2 < x < X1 + 1.2 and Y0 - 1.5 < y < Y1 + 1.2) or y > Y1 + 1.2
                or (abs(y - 7.8) < 2.0 and (x < X0 + 1.0 or x > X1 - 1.0))
                or (cx0 - 2 < x < cx1 + 2 and y > cy0 - 3))
    kit.forest(rng, height, keep_out, (-16, -16, 36, 18), count=70, ferns=26, needles=700)

    def tufts(r):
        while True:
            x, y = r.uniform(X0 - 1, X1 + 1), r.uniform(Y0, Y1 + 0.3)
            if cx0 - 0.3 < x < cx1 + 0.3 and y < cy1 + 0.6:
                continue
            py = min(PATH, key=lambda p: abs(p[0] - x))[1]
            if abs(y - py) < 0.55 and r.random() < 0.85:
                continue
            return x, y
    grass = kit.meadow(rng, 1900, tufts, height)
    kit.meadow(rng, 500, tufts, height, mat("dead grass"))
    rv, rf = [], []
    for (x, y, r) in ((0.0, 3.0, 0.8), (16.6, 1.0, 1.0), (18.9, 11.6, 0.6), (2.6, 12.0, 0.45), (12.0, 0.4, 0.7)):
        reb.boulder(rng, (x, y, height(x, y) - 0.1), r, rv, rf)
    reb.mesh_object("Rocks", rv, rf, mat("rock"))

    # ---- Crows on the drips and the fence.
    pecker, _ = kit.crow("Crow at the drips", (6.9, 6.75, 0.0), heading=2.6)
    kit.crow("Crow on the fence", (8.6, Y1 + 0.43, 1.03), heading=-1.4)
    kit.crow("Crow on the roof", (10.2, mid_y, ridge_z + 0.14), heading=0.4)

    # ---- Light: the late sun low in the south-west, hard across the grass; the valley below.
    sun = kit.time_light("afternoon", sun_heading=235, sun_energy=4.2)
    sun.rotation_euler[0] = math.radians(90 - 24)
    kit.vista(rng, (9.0, Y1 + 2), (0.0, 1.0), below=-110.0)

    anim = kit.Anim(16)

    def blow(k):
        a = anim.phase(k)
        sock_pivot.rotation_euler = (0.06 * math.sin(2 * a), 0.05 * math.sin(a + 1), 0.35 + 0.28 * math.sin(a))
    anim.custom(blow)
    def flap(k):
        for i, peg in enumerate(hangers):
            peg.rotation_euler = (0.2 * math.sin(anim.phase(k) + i * 0.9), 0, 0)
    anim.custom(flap)
    anim.sway(grass, amount=0.05)
    anim.custom(lambda k: setattr(pecker, "rotation_euler", (0, 0.35 * max(0.0, math.sin(anim.phase(k, 3))), 2.6)))

    # ---- What the game needs.
    room.door("platform", (X0, 6.5, X0 + 0.6, 8.5), arrive=(2.6, 7.5), face=(1, 0))
    room.door("cottage", (d0, cy1 + 0.15, d1, cy1 + 0.75), arrive=(9.05, 5.7), face=(0, 1), walk=False)
    room.door("quarry", (X1 - 0.6, 7.0, X1, 9.0), arrive=(17.0, 8.0), face=(-1, 0))
    room.check((3.7, 6.6, 5.2, 8.1), "A thermos, dropped on the path. The coffee's long dried.\nThe cup rolled off into the grass.")
    room.check((6.0, 6.2, 8.2, 7.4), "Blood, drop after drop, from the station. He was bleeding as he walked.")
    room.check((d0 - 0.5, cy1 + 0.15, d0, cy1 + 0.8), "A bloody hand on the door frame. He went in.")
    room.check((14.4, 6.8, 16.2, 8.2), "A rag soaked in blood. The drips go on, east.\nHe came out again and kept going.")
    room.check((11.9, 5.0, 13.3, 6.3), "SKYWAY back the way I came. QUARRY and OLD MINE on ahead.\nThere's blood on the post.")
    room.check((4.0, 10.5, 6.0, Y1), "A bench with a view of the whole valley. A little plaque:\nFOR THE ONES WHO BUILT THE SKYWAY.")
    room.check((13.8, 10.0, 15.4, 11.6), "The station's windsock. It's blowing hard off the valley.")
    room.check((5.0, 4.2, 6.2, 5.4), "The axe is still in the block. Somebody's woodpile, somebody's washing.")
    room.export(anim)


build()
