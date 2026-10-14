"""Camp 4's bunkhouse, noon: long and low, two rows of iron bunks.

What it tells: the men slept here, and this is where the sickness went
through them. The mattresses are soaked: sweat, sick, blood. Buckets stand
by the bunks. One man died in his bunk under his blanket and nobody moved
him; the flies have found him. Mike turned in the night: his friends tied
him to his bunk frame with their belts, and one of them kept a diary on the
next bunk: "Mike's fever broke at 3. He doesn't know us." Someone was
dragged out of the far bunk to the door, and out to the fire. Then they
held the door against the others: a footlocker and a bunk were shoved
against it, and shoved back when the axe came through. The card game on
the table never finished. Among the girlie calendars, a July 1998 calendar
from the supply company has three dates circled in red: 17, 31 and 8. A
player should notice the circled days.

Metres: the floor is x 1.0-12.0, y 1.0-6.0, 2.4 high (in the yard the
bunkhouse is x 6.0-17.0, y -3.4-1.6: this room is it moved 5 east, 4.4
south). The door is in the south wall at x 6.0-6.9, out to the yard.
Windows in the south wall at x 2.0-3.0, 3.9-4.9 (boarded outside), 8.0-9.0
(broken) and 10.0-11.0, from 1.0 to 1.7 high. Bunks along the north wall at
x 2.05, 4.15, 8.55, 10.65 and the south wall at x 2.05, 4.15, 8.0, 10.1,
heads east; the stove on the north wall at x 6.4; the card table at (6.0,
3.6). The calendar on the north wall at x 7.3, by the stove.

Moving: the bulb failing on its flex, flies over the man in his bunk, a rag
in the broken window stirring.
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
from mathutils import Matrix, Vector  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 12.0, 1.0, 6.0, 2.4
DOOR = (6.0, 6.9)
WINDOWS = [(2.0, 3.0), (3.9, 4.9), (8.0, 9.0), (10.0, 11.0)]
WZ = (1.0, 1.7)
NORTH_BUNKS = [2.05, 4.15, 8.55, 10.65]
SOUTH_BUNKS = [2.05, 4.15, 8.0, 10.1]
NY, SY = Y0 + 0.47, Y1 - 0.47   # bunk centre lines


def settle(ob, offset, rot=None):
    """kit.join keeps its first part's frame, and kit.body, bunk, chair,
    crate, shelves and crow then place the result as if it had none: bodies
    stand on end, bunks sink a metre. Move the mesh back into the prop's
    own frame (children are placed in that frame already)."""
    m = Matrix.Translation(offset)
    if rot is not None:
        m = m @ rot.to_matrix().to_4x4()
    ob.data.transform(m)
    return ob


def body(name, at, heading=0.0, pose="back", **kw):
    ob = kit.body(name, at, heading=heading, pose=pose, **kw)
    j, missing = kit._POSES[pose], kw.get("missing", ())
    a, b = next((Vector(j[p]), Vector(j[q])) for p, q, _, _ in kit._BONES if p not in missing and q not in missing)
    return settle(ob, (a + b) / 2, (b - a).to_track_quat("Z", "Y"))


def bunk(name, frame_m, at, rot=0.0, levels=2, **kw):
    ob = kit.bunk(name, frame_m, at, rot=rot, levels=levels, **kw)[0]
    return settle(ob, (-1.95 / 2, -0.85 / 2, (0.75 + (levels - 1) * 1.25) / 2))


def chair(name, m, at, rot=0.0, tipped=False):
    return settle(kit.chair(name, m, at, rot=rot, tipped=tipped), (0, 0, 0.45))


def crate(name, m, at, size=(0.6, 0.5, 0.5), rot=0.0, open_=False):
    return settle(kit.crate(name, m, at, size=size, rot=rot, open_=open_), (0, 0, size[2] / 2))


def local(at, heading, p):
    """A point given in a body's own frame (kit's poses) in the world."""
    c, s = math.cos(heading), math.sin(heading)
    return Vector((at[0] + p[0] * c - p[1] * s, at[1] + p[0] * s + p[1] * c, at[2] + p[2]))


def ring(name, m, centre, r, facing, width=0.012, seg=20):
    """A painted ring on a wall, round a date: an annulus in the wall's plane."""
    n = Vector((facing[0], facing[1], 0)).normalized()
    u = n.cross(Vector((0, 0, 1))).normalized()
    w = Vector((0, 0, 1))
    c = Vector(centre) + n * 0.003
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        d = u * math.cos(a) + w * math.sin(a) * 0.85
        v += [tuple(c + d * (r - width)), tuple(c + d * (r + width))]
    for i in range(seg):
        j = (i + 1) % seg
        f.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    return reb.mesh_object(name, v, f, m, smooth=False)


def belt(name, a, b, r=0.02):
    """A leather belt pulled tight from a wrist to a bunk post, with its buckle."""
    leather = reb.mat_plain("Belt leather", (0.07, 0.04, 0.02), 0.5)
    kit.rod(name, leather, a, b, r, 6)
    reb.prim("cube", f"{name} buckle", mat("steel"), Vector(b).lerp(Vector(a), 0.25), (0.05, 0.05, 0.04))


def build():
    rng = random.Random(11)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((11.85, 3.4, 2.25), (4.6, 3.7, 0.3), 200, "high on the east wall over the aisle: the length of the room, the table, the drag to the door")
    room.camera((1.15, 3.5, 2.25), (8.0, 3.2, 0.3), 200, "high on the west wall over the aisle: both rows of bunks, the card table, the stove")
    room.camera((6.45, 5.8, 2.2), (9.4, 2.2, 0.4), 200, "high over the door: the man dead in his bunk, the calendar by the stove")
    room.camera((7.35, 1.15, 2.25), (10.2, 5.2, 0.3), 200, "high over the calendar: Mike tied to his bunk, the diary, the footlocker shoved from the door")

    # ---- Materials.
    walls_m = kit.boards("Bunkhouse planks", (0.3, 0.22, 0.14), width=0.2, grime=0.7)
    floor_m = kit.dirtied(mat("planks"), 0.75, scale=1.5)
    ceil_m = kit.boards("Ceiling boards", (0.36, 0.3, 0.21), width=0.14, grime=0.4)
    frame_m = mat("dark wood")
    iron = reb.mat_metal("Bunk iron", (0.1, 0.11, 0.1), 0.6)
    soak = reb.mat_surface("Soaked", [(0.0, (0.09, 0.07, 0.03)), (0.6, (0.16, 0.12, 0.05)), (1.0, (0.12, 0.05, 0.02))], scale=5, rough=0.4, bump=0.1)
    sick = reb.mat_plain("Sick", (0.12, 0.11, 0.04), 0.2)
    galv = reb.mat_metal("Galvanised", (0.32, 0.33, 0.32), 0.45)
    locker = reb.mat_surface("Footlocker green", [(0.0, (0.05, 0.08, 0.05)), (0.8, (0.09, 0.13, 0.08)), (1.0, (0.15, 0.1, 0.06))], scale=6, rough=0.6)
    wool = reb.mat_surface("Grey wool", [(0.0, (0.1, 0.1, 0.09)), (1.0, (0.2, 0.19, 0.17))], scale=20, bump=0.3)
    skin_pink = reb.mat_plain("Pin-up", (0.55, 0.33, 0.25), 0.7)

    # ---- The shell: plank walls, the door and the windows cut, a board floor, a low boarded ceiling.
    kit.walls(X0, Y0, X1, Y1, H, walls_m, openings=[("s", DOOR[0], DOOR[1], 0.0, 2.05)] + [("s", a, b, WZ[0], WZ[1]) for a, b in WINDOWS], ceiling=ceil_m)
    kit.plank_floor(X0 - 0.1, Y0 - 0.1, X1 + 0.1, Y1 + 0.1, floor_m, along="x", seed=3)
    for x in (2.6, 4.8, 7.0, 9.2, 11.4):
        reb.prim("cube", "Ceiling joist", frame_m, (x, (Y0 + Y1) / 2, H - 0.07), (0.1, Y1 - Y0, 0.14))
    for i, (a, b) in enumerate(WINDOWS):
        if i != 2:
            reb.prim("cube", f"Window glass {i}", reb.mat_glass("Grimy glass", (0.45, 0.47, 0.42)), ((a + b) / 2, Y1 + 0.06, sum(WZ) / 2), (b - a, 0.01, WZ[1] - WZ[0]))
        reb.prim("cube", "Window mullion", frame_m, ((a + b) / 2, Y1 + 0.02, sum(WZ) / 2), (0.04, 0.05, WZ[1] - WZ[0]))
        reb.prim("cube", "Window sill", frame_m, ((a + b) / 2, Y1 - 0.03, WZ[0] - 0.02), (b - a + 0.1, 0.1, 0.04))
    # The boarded window: the boards on its outside, dark through the glass.
    kit.barricade("Boards outside", mat("planks"), (3.8, Y1 + 0.2), (5.0, Y1 + 0.2), 1.1, 1.6, count=3, seed=5)
    # The broken one: a jag of glass left, a rag stuffed in it that stirs.
    reb.prim("cube", "Glass jag", reb.mat_glass("Grimy glass", (0.45, 0.47, 0.42)), (8.25, Y1 + 0.06, 1.2), (0.45, 0.01, 0.35), rot=(0, 0.3, 0))
    rag = reb.cloth("Rag in the window", mat("flannel"), (0, 0, -0.2), (0.3, 0.4), rot=(math.pi / 2, 0, 0), cuts=8, lumps=0.04, seed=3)
    rag_peg = reb.prim("sphere", "Rag nail", mat("iron"), (8.7, Y1 + 0.02, 1.66), (0.02, 0.02, 0.02))
    rag.parent = rag_peg
    kit.shards("Glass on the floor", (8.5, Y1 - 0.5, 0.0), spread=0.6, count=16, seed=2)
    # The door, open out to the yard, its frame; light from the yard.
    for x in (DOOR[0] - 0.04, DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", frame_m, (x, Y1 + 0.04, 1.05), (0.08, 0.16, 2.1))
    reb.prim("cube", "Door head", frame_m, ((DOOR[0] + DOOR[1]) / 2, Y1 + 0.04, 2.09), (DOOR[1] - DOOR[0] + 0.16, 0.16, 0.08))
    reb.prim("cube", "Door, open out", mat("planks"), (DOOR[0] - 0.45, Y1 + 0.19, 1.02), (0.9, 0.05, 2.04))
    kit.rod("Axe handle through", reb.mat_wood("Axe handle", (0.4, 0.28, 0.14)), (DOOR[0] - 0.5, Y1 + 0.24, 1.3), (DOOR[0] - 0.25, Y1 + 0.95, 1.05), 0.02)
    kit.scratches("Gouges on the frame", mat("black"), (DOOR[1] + 0.09, Y1 - 0.01, 1.4), (0, -1), count=4, length=0.5, seed=4)
    kit.splat("Hand on the frame", mat("old blood"), (DOOR[0] - 0.09, Y1 - 0.005, 1.1), 0.07, rot=(math.pi / 2, 0, 0), seed=6)
    # The barricade, shoved back into the room: a footlocker, a chair, the scrape marks.
    crate("Footlocker shoved back", locker, (7.5, 4.25, 0.0), size=(0.8, 0.45, 0.42), rot=0.5)
    chair("Chair from the barricade", mat("pine"), (5.35, 4.85, 0.0), rot=2.2, tipped=True)
    for i in range(4):
        reb.prim("cube", f"Scrape {i}", reb.mat_plain("Scrape", (0.25, 0.2, 0.13), 0.9), (6.9 + i * 0.12, 5.0 - i * 0.05, 0.002), (0.02, 1.2, 0.002), rot=(0, 0, 0.55))
    reb.mask(reb.wall(reb.prim("cube", "Footlocker footprint", None, (7.5, 4.25, 0.2), (0.85, 0.7, 0.4)))).hide_render = True

    # ---- Outside: the yard's mud, the laundry, the fire pit's smoke, the mess beyond.
    reb.prim("cube", "Outside, mud", kit.dirtied(mat("mud"), 0.6), (6.5, Y1 + 12, -0.1), (40, 24, 0.2))
    reb.prim("cube", "Outside, step", mat("planks"), ((DOOR[0] + DOOR[1]) / 2, Y1 + 0.4, 0.06), (1.4, 0.5, 0.14))
    # (the yard's layout, moved 5 east and 4.4 south)
    reb.prim("cube", "Outside, mess", kit.boards("Mess boards", (0.42, 0.4, 0.36), width=0.18), (-5.7, 13.9, 1.4), (5.6, 9.2, 2.8))
    reb.prim("cube", "Outside, skidder", reb.mat_plain("Skidder yellow", (0.45, 0.3, 0.03), 0.6), (3.0, 17.4, 1.2), (4.0, 2.2, 1.8))
    reb.prim("cube", "Outside, workshop", mat("tin"), (11.3, 21.0, 1.5), (6.0, 5.8, 3.0))
    reb.prim("cube", "Outside, sawmill", kit.boards("Mill boards", (0.2, 0.19, 0.17), width=0.3), (20.0, 11.8, 3.0), (13.0, 9.8, 6.0))
    deck = [((7.6, 6.85 + i * 0.5, 0.25 + 0.5 * (i % 2)), (12.4, 6.85 + i * 0.5, 0.25 + 0.5 * (i % 2))) for i in range(5)]
    for i, (a, b) in enumerate(deck):
        kit.rod(f"Outside, log {i}", mat("bark"), a, b, 0.25, 10)
    reb.prim("cyl", "Outside, fire ring", reb.mat_plain("Ash", (0.1, 0.1, 0.1), 0.9), (4.0, 12.7, 0.02), (2.2, 2.2, 0.06), segments=16)
    reb.prim("cube", "Outside, far trees", reb.mat_plain("Far trees", (0.05, 0.07, 0.05), 0.9), (6.5, Y1 + 30, 8), (80, 1, 16))
    kit.rod("Outside, line pole", mat("dark wood"), (0.6, Y1 + 1.0, 0), (0.6, Y1 + 1.0, 2.15), 0.04)
    kit.rod("Outside, line pole", mat("dark wood"), (4.8, Y1 + 1.8, 0), (4.8, Y1 + 1.8, 2.15), 0.04)
    kit.rod("Outside, washing line", mat("canvas"), (0.6, Y1 + 1.0, 2.05), (4.8, Y1 + 1.8, 2.05), 0.006, 4)
    for i, (t, m) in enumerate(((0.33, reb.mat_plain("Long johns", (0.5, 0.45, 0.36), 0.9)), (0.5, mat("denim")), (0.68, mat("flannel")))):
        p = Vector((0.6, Y1 + 1.0, 0)).lerp(Vector((4.8, Y1 + 1.8, 0)), t)
        reb.cloth(f"Outside, washing {i}", m, (p.x, p.y, 1.65), (0.5, 0.8), rot=(math.pi / 2, 0, 0.19), cuts=6, lumps=0.03, seed=i)
    kit.drag_trail("Outside, the drag", mat("old blood"), [(6.4, Y1 + 0.5), (6.0, Y1 + 2.3), (5.2, Y1 + 4.1)], width=0.4, seed=7)

    # ---- The bunks: north row and south row, heads east.
    bunks = {}
    for row, (y, xs) in enumerate(((NY, NORTH_BUNKS), (SY, SOUTH_BUNKS))):
        for i, x in enumerate(xs):
            b = bunk(f"Bunk {row}{i}", iron, (x, y, 0.0), rot=0.0, levels=1 if (row, i) in ((0, 2), (1, 3)) else 2, slept_in=(row, i) not in ((0, 2), (1, 3)), seed=row * 10 + i + 1)
            reb.wall(b)
            bunks[(row, i)] = b
    # Soaked mattresses: dark stains on the lower ones.
    for row, (y, xs) in enumerate(((NY, NORTH_BUNKS), (SY, SOUTH_BUNKS))):
        for i, x in enumerate(xs):
            kit.splat(f"Soak {row}{i}", soak, (x + rng.uniform(-0.3, 0.3), y, 0.505), rng.uniform(0.2, 0.35), seed=row * 10 + i, stretch=(1.6, 0.8), lumps=0.5)
            if rng.random() < 0.5 and (row, i) not in ((0, 2), (1, 3)):
                kit.splat(f"Soak top {row}{i}", soak, (x + rng.uniform(-0.3, 0.3), y, 1.755), rng.uniform(0.15, 0.3), seed=row * 10 + i + 50, stretch=(1.6, 0.8))
    # Footlockers at the bunks' aisle side.
    for row, (y, xs) in enumerate(((NY + 0.68, NORTH_BUNKS), (SY - 0.68, SOUTH_BUNKS))):
        for i, x in enumerate(xs):
            if (row, i) in ((1, 2),):
                continue
            ob = crate(f"Footlocker {row}{i}", locker, (x + rng.uniform(-0.3, 0.3), y, 0.0), size=(0.8, 0.42, 0.4), rot=rng.uniform(-0.08, 0.08), open_=(row, i) == (0, 0))
            reb.mask(reb.wall(ob))
    # Clothes on the bunk ends, boots under them, a bucket by each sick man.
    for i, (x, y) in enumerate(((2.05 - 0.97, NY), (8.55 - 0.97, NY), (4.15 - 0.97, SY), (10.1 - 0.97, SY))):
        reb.cloth(f"Shirt over the rail {i}", mat("flannel") if i % 2 else mat("denim"), (x, y, 1.25), (0.05, 0.6), rot=(0, math.pi / 2 - 0.1, 0), cuts=6, lumps=0.03, seed=i)
    for i, (x, y) in enumerate(((3.6, NY + 0.1), (9.9, NY - 0.1), (1.6, SY), (8.9, SY + 0.1))):
        reb.prim("cube", f"Boot {i}", mat("rubber"), (x, y, 0.08), (0.3, 0.12, 0.16), rot=(0, 0, rng.uniform(-0.3, 0.3)), bevel=0.03)
        reb.prim("cube", f"Boot {i}b", mat("rubber"), (x + 0.05, y + 0.15, 0.08), (0.3, 0.12, 0.16), rot=(0, 0, rng.uniform(-0.3, 0.3)), bevel=0.03)
    for i, (x, y) in enumerate(((7.4, NY + 0.75), (11.5, SY - 0.75), (3.0, SY - 0.75), (9.6, NY + 0.75))):
        reb.prim("cyl", f"Sick bucket {i}", galv, (x, y, 0.15), (0.3, 0.3, 0.3), segments=14)
        reb.prim("cyl", f"In the bucket {i}", sick, (x, y, 0.26), (0.27, 0.27, 0.01), segments=14)
        kit.splat(f"Slop {i}", sick, (x + 0.2, y, 0.0), 0.15, seed=90 + i)

    # ---- The man who died in his bunk, under his blanket. The flies have him.
    dead_at = (8.55 - 0.85, NY, 0.5)
    body("Dead in his bunk", dead_at, heading=0.0, pose="back", top=wool, legs=mat("denim"), seed=4)
    reb.cloth("His blanket", wool, (8.3, NY + 0.05, 0.74), (1.3, 0.95), lumps=0.06, seed=4)
    kit.splat("Dripped under his bunk", mat("old blood"), (8.6, NY + 0.4, 0.0), 0.25, seed=41)

    # ---- Mike, tied to his bunk frame with his friends' belts.
    mx = SOUTH_BUNKS[3]
    mike_at = (mx + 0.85, SY, 0.5)
    mh = math.pi
    body("Mike", mike_at, heading=mh, pose="back", top=reb.mat_plain("Vest", (0.45, 0.42, 0.36), 0.9), legs=mat("denim"), seed=8)
    posts = [Vector((mx + dx, SY + dy, 0.55)) for dx in (-0.975, 0.975) for dy in (-0.425, 0.425)]
    for name, joint in (("Belt, left wrist", "l_hand"), ("Belt, right wrist", "r_hand"), ("Belt, left ankle", "l_foot"), ("Belt, right ankle", "r_foot")):
        at = local(mike_at, mh, kit._POSES["back"][joint])
        belt(name, at, min(posts, key=lambda p: (p.xy - at.xy).length))
    kit.splat("Mike's blood", mat("blood"), (mx - 0.6, SY, 0.506), 0.25, seed=81, stretch=(1.2, 0.8))
    kit.splat("Mike's blood, the floor", mat("blood"), (mx - 0.7, SY - 0.6, 0.0), 0.3, seed=82)
    kit.scratches("Gouges in the wall by Mike", mat("black"), (mx + 0.2, Y1 - 0.005, 1.0), (0, -1), count=5, length=0.35, seed=8)
    reb.prim("cube", "Claw hammer", mat("steel"), (mx + 0.3, SY - 0.75, 0.02), (0.3, 0.03, 0.03), rot=(0, 0, 0.7))
    # The diary on the next bunk, open; a pencil.
    dx = SOUTH_BUNKS[2]
    reb.prim("cube", "Diary", reb.mat_plain("Diary cover", (0.2, 0.08, 0.05), 0.7), (dx + 0.4, SY - 0.1, 0.52), (0.3, 0.22, 0.03), rot=(0, 0, 0.3))
    reb.prim("cube", "Diary page", mat("paper"), (dx + 0.4, SY - 0.1, 0.537), (0.28, 0.2, 0.004), rot=(0, 0, 0.3))
    kit.rod("Pencil", mat("yellow paint"), (dx + 0.15, SY - 0.3, 0.51), (dx + 0.3, SY - 0.4, 0.51), 0.005, 6)

    # ---- The dragged one: from the far north bunk to the door.
    kit.drag_trail("Drag to the door", mat("old blood"), [(10.6, NY + 0.4), (10.0, 2.6), (8.4, 3.4), (7.0, 4.4), (6.45, Y1 - 0.1)], width=0.4, seed=12)
    reb.prim("cube", "Mattress pulled half off", mat("mattress"), (10.6, NY + 0.55, 0.3), (1.8, 0.75, 0.12), rot=(0.5, 0, 0.05))

    # ---- The stove on the north wall, cold; its pipe; wood and kindling.
    stove = reb.prim("cyl", "Pot-belly stove", mat("iron"), (6.4, Y0 + 0.5, 0.5), (0.6, 0.6, 0.8), segments=16)
    reb.mask(reb.wall(stove, "circle"))
    reb.prim("sphere", "Stove belly", mat("iron"), (6.4, Y0 + 0.5, 0.55), (0.7, 0.7, 0.6))
    reb.prim("cyl", "Stove top", mat("iron"), (6.4, Y0 + 0.5, 0.92), (0.5, 0.5, 0.05))
    kit.rod("Stovepipe", mat("rust"), (6.4, Y0 + 0.5, 0.95), (6.4, Y0 + 0.5, H), 0.07)
    reb.prim("cube", "Stove door", mat("black"), (6.4, Y0 + 0.83, 0.5), (0.22, 0.02, 0.18))
    logs = [reb.prim("cyl", "Firewood", mat("logs"), (5.6 + (i % 3) * 0.13, Y0 + 0.3, 0.07 + (i // 3) * 0.12), (0.12, 0.12, 0.45), rot=(math.pi / 2, 0, 0), segments=8) for i in range(6)]
    kit.join("Firewood", logs)
    kit.splat("Ash before the stove", reb.mat_plain("Ash", (0.15, 0.14, 0.13), 0.9), (6.4, Y0 + 1.05, 0.0), 0.3, seed=5)
    # A shelf over the stove: a radio, cups, a can of coffee.
    reb.prim("cube", "Shelf over the stove", frame_m, (6.1, Y0 + 0.12, 1.55), (0.9, 0.24, 0.03))
    for i, x in enumerate((5.75, 5.9, 6.3, 6.45)):
        reb.prim("cyl", f"Cup {i}", reb.mat_plain("Enamel", (0.5, 0.52, 0.5), 0.4), (x, Y0 + 0.12, 1.62), (0.08, 0.08, 0.1), segments=10)
    reb.prim("cube", "Radio", reb.mat_plain("Radio brown", (0.15, 0.08, 0.04), 0.5), (6.1, Y0 + 0.12, 1.66), (0.22, 0.16, 0.18))

    # ---- The calendars: the July 1998 one, three days circled red; the girlie ones by the bunks.
    cx, cz = 7.05, 1.4
    reb.prim("cube", "Calendar", mat("paper"), (cx, Y0 + 0.012, cz), (0.6, 0.006, 0.8))
    reb.prim("cube", "Calendar picture", reb.mat_plain("Calendar picture", (0.22, 0.3, 0.2), 0.8), (cx, Y0 + 0.017, cz + 0.22), (0.54, 0.004, 0.3))
    kit.text("Calendar head", "PIKE SUPPLY CO", mat("white paint"), (cx, Y0 + 0.02, cz + 0.33), size=0.045, rot=(math.pi / 2, 0, math.pi))
    kit.text("Calendar month", "JULY 1998", mat("black"), (cx, Y0 + 0.02, cz + 0.02), size=0.06, rot=(math.pi / 2, 0, math.pi))
    days = []
    for d in range(1, 32):
        col = (d + 2) % 7
        row = (d + 2) // 7
        days.append((d, cx + 0.24 - col * 0.08, cz - 0.07 - row * 0.065))   # read from the south: east is to her left
    for d, x, z in days:
        kit.text(f"Day {d}", str(d), mat("black"), (x, Y0 + 0.02, z), size=0.03, rot=(math.pi / 2, 0, math.pi))
    red = reb.mat_plain("Red pen", (0.5, 0.02, 0.02), 0.5)
    for d, x, z in days:
        if d in (17, 31, 8):
            ring(f"Circled {d}", red, (x, Y0 + 0.02, z), 0.032, (0, 1))
    kit.text("Calendar note", "17 31 8", red, (cx - 0.14, Y0 + 0.021, cz - 0.38), size=0.035, rot=(math.pi / 2, 0, math.pi))
    for i, (x, y, z, side) in enumerate(((3.1, Y0 + 0.01, 1.5, "n"), (9.6, Y0 + 0.01, 1.45, "n"), (X0 + 0.01, 2.3, 1.4, "w"), (X1 - 0.01, 4.8, 1.45, "e"))):
        if side == "n":
            at, sz, rot = (x, y, z), (0.42, 0.006, 0.6), 0.0
        else:
            at, sz, rot = (x, y, z), (0.006, 0.42, 0.6), 0.0
        reb.prim("cube", f"Girlie calendar {i}", reb.mat_plain(f"Pin-up ground {i}", (0.2, 0.3, 0.45) if i % 2 else (0.45, 0.15, 0.12), 0.8), at, sz)
        off = Vector((0, 0.008, 0)) if side == "n" else Vector((0.008 if side == "w" else -0.008, 0, 0))
        reb.prim("sphere", f"Pin-up figure {i}", skin_pink, Vector(at) + off + Vector((0, 0, 0.06)), (0.12 if side == "n" else 0.01, 0.01 if side == "n" else 0.12, 0.35))
        reb.prim("cube", f"Pin-up dates {i}", mat("paper"), Vector(at) + off + Vector((0, 0, -0.22)), (0.38 if side == "n" else 0.004, 0.004 if side == "n" else 0.38, 0.14))

    # ---- The card table in the aisle: the last hand, bottles, an ashtray, the chairs.
    tbl = kit.table("Card table", mat("pine"), (5.1, 3.55, 0.0), size=(1.1, 0.8, 0.74))
    reb.mask(reb.wall(tbl))
    chair("Card chair", mat("pine"), (4.35, 3.5, 0.0), rot=0.1)
    chair("Card chair", mat("pine"), (5.9, 3.0, 0.0), rot=math.pi - 0.3)
    cards = []
    for i in range(14):
        cards.append(reb.prim("cube", "Card", mat("white paint"), (5.1 + rng.gauss(0, 0.2), 3.55 + rng.gauss(0, 0.15), 0.742 + i * 0.0008), (0.06, 0.09, 0.002), rot=(0, 0, rng.uniform(0, 3))))
    for i in range(5):
        cards.append(reb.prim("cube", "Card on the floor", mat("white paint"), (5.6 + rng.gauss(0, 0.4), 4.0 + rng.gauss(0, 0.3), 0.002), (0.06, 0.09, 0.002), rot=(0, 0, rng.uniform(0, 3))))
    kit.join("Playing cards", cards)
    kit.bottles("Bottles on the table", (5.0, 3.45, 0.74), count=3, spread=0.3, seed=3, tipped=0.3)
    kit.bottles("Empties on the floor", (4.0, 4.1, 0.0), count=6, spread=0.8, seed=6, tipped=0.8)
    reb.prim("cyl", "Ashtray", mat("steel"), (5.4, 3.7, 0.755), (0.14, 0.14, 0.03), segments=12)
    for i in range(4):
        reb.prim("cube", f"Coin {i}", mat("steel"), (4.85 + i * 0.07, 3.8, 0.743), (0.025, 0.025, 0.004))

    # ---- Light: the bulb over the aisle failing, grey noon through the windows and the door.
    kit.time_light("noon", sun_heading=200, sun_energy=1.5, sky=((0.5, 0.52, 0.54), (0.36, 0.39, 0.43), 0.8))
    cord, glass, bulb_light, glow = kit.bulb("Bulb", (6.6, 3.5, H - 0.02), energy=110, rgb=(1.0, 0.72, 0.42), flex=0.45)
    for i, (a, b) in enumerate(WINDOWS):
        if i == 1:
            continue
        reb.spot(f"Window light {i}", ((a + b) / 2, Y1 - 0.15, 1.65), ((a + b) / 2 - 0.3, Y1 - 2.6, 0.0), 90, (0.72, 0.78, 0.88), 150, 0.9, 0.5)
    reb.spot("Door light", ((DOOR[0] + DOOR[1]) / 2, Y1 + 3.0, 2.3), ((DOOR[0] + DOOR[1]) / 2, Y1 - 2.0, 0.0), 400, (0.75, 0.8, 0.88), 45, 0.8, 0.6)
    reb.point("West end fill", (2.5, 3.5, 1.5), 30, (0.6, 0.65, 0.75), 1.0)
    reb.point("East end fill", (10.5, 3.5, 1.5), 30, (0.6, 0.65, 0.75), 1.0)

    anim = kit.Anim(16)
    anim.flicker(bulb_light, glow, depth=0.5, dropouts=3)
    anim.flies((8.55 + 0.6, NY, 0.75), count=10, radius=0.4)
    anim.flies((mx + 0.4, SY, 0.6), count=6, radius=0.3)
    anim.custom(lambda k: setattr(rag_peg, "rotation_euler", (math.radians(14) * math.sin(anim.phase(k)), 0, 0)))

    # ---- What the game needs.
    room.door("camp-yard", (DOOR[0], Y1 - 0.5, DOOR[1], Y1), arrive=(6.45, 4.6), face=(0, -1))
    room.check((6.75, Y0, 7.55, 2.3), "A calendar from a supply company. July 1998.\nSomeone circled three days in red: the 17th, the 31st, the 8th.\nAnd wrote them again at the bottom. 17 31 8.")
    room.check((7.6, 2.3, 9.5, 2.8), "He died in his bed. Nobody even pulled the blanket over his face.")
    room.check((mx - 0.9, 4.1, mx + 0.9, 4.65), "They tied him to the bunk with their belts.\nWrists and ankles. Then something with a hammer.")
    room.check((dx - 0.4, 4.45, dx + 0.6, 5.1), "A diary, left open on the bunk.\n\"Mike's fever broke at 3. He doesn't know us.\"")
    room.check((4.4, 3.0, 5.8, 4.1), "A card game nobody finished. Bottles, all empty.")
    room.check((6.9, 3.7, 8.2, 4.8), "A footlocker and a chair, shoved back from the door.\nThey were holding it shut.")
    room.check((5.8, 1.85, 7.0, 2.4), "The stove's cold.")
    room.check((1.3, 2.3, 2.8, 2.8), "His footlocker, open. Letters from home. A photo of a woman.")
    room.entry = "It stinks of sickness in here."
    # Many scenes share the render machine's GPU: keep each frame cheap.
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    scene.cycles.volume_step_rate = 4.0
    scene.cycles.volume_max_steps = 64
    room.export(anim, samples=160)


build()
