"""The potting shed in the mansion's back garden, at night.

What it tells: the estate's gardener kept everything here in its place,
and then stopped. His lantern is still lit on the bench beside a mug of
tea gone cold and a tray of seedlings he never planted out; a calendar on
the wall has July crossed off day by day to the 20th and no further. On
the board by the door hang the estate's spare keys, each on its labelled
hook: the cellar key with its red tag is among them, and two hooks are
empty. Tools hang in a row on the south wall, sacks of bone meal and
potting soil slump in the corner, a sack has been gnawed open and spilled.
A rat lies dead on its back by the spilled meal, swollen, its fur coming
away, beside a trap that never caught it. A cobweb across the window
trembles in the draught from the door.

Metres: the floor is x 1.0-3.8, y 1.0-3.8, 2.2 high to the rafters. The
door is in the west wall at y 2.1-2.9, out to the back garden; a small
window beside it at y 3.25-3.65. The bench runs along the east wall, the
key board is on the north wall by the door, the tools on the south wall.

Moving: the lantern's flame, the cobweb trembling, flies over the rat.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 3.8, 1.0, 3.8, 2.2
DOOR = (2.1, 2.9)
WINDOW = (3.25, 3.65, 1.1, 1.6)


def settle(ob, offset, rot=None):
    """kit.join keeps its first part's frame, and kit.shelves, chair and
    crate then place the result as if it had none. Move the mesh back into
    the prop's own frame (children are placed in that frame already)."""
    m = Matrix.Translation(offset)
    if rot is not None:
        m = m @ rot.to_matrix().to_4x4()
    ob.data.transform(m)
    return ob


def shelves(name, m, at, size=(1.0, 0.3, 1.8), rows=4, rot=0.0, clutter=0.7, seed=0):
    return settle(kit.shelves(name, m, at, size=size, rows=rows, rot=rot, clutter=clutter, seed=seed), (-size[0] / 2, 0, size[2] / 2))


def web(name, corner, size, facing, sag=0.25, rings=4, spokes=7):
    """A proper cobweb across a corner: spokes from the corner and rings of
    thread sagging between them, all one mesh, for trembling."""
    c = Vector(corner)
    verts, faces = [], []

    def thread(a, b, r=0.006):
        k = len(verts)
        n = (b - a).cross(Vector((0.3, 0.5, 0.8))).normalized() * r
        verts.extend([tuple(a - n), tuple(a + n), tuple(b + n), tuple(b - n)])
        faces.append((k, k + 1, k + 2, k + 3))
    ends = []
    for i in range(spokes):
        t = i / (spokes - 1)
        d = Vector((facing[0] * math.cos(t * math.pi / 2), facing[1] * math.sin(t * math.pi / 2), -0.55)).normalized()
        ends.append(d)
        thread(c, c + d * size)
    for r in range(1, rings + 1):
        rr = size * r / (rings + 0.3)
        for i in range(spokes - 1):
            a, b = c + ends[i] * rr, c + ends[i + 1] * rr
            mid = (a + b) / 2 - Vector((0, 0, sag * rr * 0.15))
            thread(a, mid)
            thread(mid, b)
    return reb.mesh_object(name, verts, faces, mat("web"), smooth=False)


def build():
    rng = random.Random(97)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((3.65, 1.15, 2.05), (1.4, 3.4, 0.5), 200, "high in the north-east corner: the door, the web in the window, the tools, the sacks and the dead rat")
    room.camera((1.15, 3.65, 2.05), (3.4, 1.4, 0.7), 200, "high by the window: the key board, the bench and its lantern")

    boards = kit.boards("Shed boards", (0.15, 0.12, 0.08), width=0.15, grime=0.75)
    floor_m = kit.boards("Shed floor", (0.12, 0.09, 0.06), width=0.18, grime=0.85)
    bench_m = mat("planks")
    sack_m = mat("canvas")
    meal = reb.mat_plain("Bone meal", (0.5, 0.46, 0.38), 0.95)
    rat_fur = reb.mat_surface("Rat fur", [(0.0, (0.04, 0.035, 0.03)), (0.7, (0.09, 0.08, 0.065)), (1.0, (0.3, 0.15, 0.12))], scale=30, bump=0.4)
    rat_skin = reb.mat_plain("Rat skin", (0.45, 0.28, 0.25), 0.6)
    red_tag = mat("red paint")

    # ---- The shell: board walls, a board floor, rafters under the tin.
    kit.walls(X0, Y0, X1, Y1, H, boards, openings=[
        ("w", DOOR[0], DOOR[1], 0.0, 1.95),
        ("w", WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3]),
    ], thick=0.1, floor=floor_m)
    reb.prim("cube", "Tin roof", mat("tin"), ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.03), (X1 - X0 + 0.4, Y1 - Y0 + 0.4, 0.04))
    for y in (1.6, 2.4, 3.2):
        kit.rod("Rafter", mat("dark wood"), (X0 - 0.05, y, H - 0.06), (X1 + 0.05, y, H - 0.06), 0.05, 6)
    kit.rod("Tie beam", mat("dark wood"), ((X0 + X1) / 2, Y0, H - 0.1), ((X0 + X1) / 2, Y1, H - 0.1), 0.05, 6)
    # The door, shut, a latch; the window, grimy, the garden at night beyond.
    reb.prim("cube", "Door", kit.boards("Door", (0.15, 0.1, 0.06), width=0.12, grime=0.7), (X0 - 0.03, sum(DOOR) / 2, 0.97), (0.04, DOOR[1] - DOOR[0], 1.94))
    for z in (0.3, 1.6):
        reb.prim("cube", "Door ledge", mat("dark wood"), (X0 + 0.0, sum(DOOR) / 2, z), (0.03, DOOR[1] - DOOR[0] - 0.04, 0.1))
    reb.prim("cube", "Brace", mat("dark wood"), (X0 + 0.0, sum(DOOR) / 2, 0.95), (0.03, 0.06, 1.4), rot=(0.55, 0, 0))
    reb.prim("cube", "Latch", mat("iron"), (X0 + 0.03, DOOR[1] - 0.1, 1.0), (0.03, 0.15, 0.03))
    reb.prim("cube", "Window glass", reb.mat_glass("Grimy glass", (0.4, 0.42, 0.42)), (X0 - 0.05, sum(WINDOW[:2]) / 2, sum(WINDOW[2:]) / 2), (0.01, WINDOW[1] - WINDOW[0], WINDOW[3] - WINDOW[2]))
    the_web = web("Web in the window", (X0 + 0.02, WINDOW[1] + 0.05, WINDOW[3] + 0.05), 0.4, (1, -1), rings=4, spokes=6)
    reb.prim("cube", "Outside, gravel", mat("gravel"), (X0 - 4.0, 2.4, -0.05), (8.0, 8.0, 0.1))
    reb.prim("cube", "Outside, hedge", reb.mat_surface("Box hedge", [(0.0, (0.01, 0.025, 0.01)), (1.0, (0.035, 0.07, 0.03))], scale=6, bump=1.0), (X0 - 2.6, 2.4, 0.3), (1.6, 3.0, 0.6))

    # ---- The bench along the east wall: the lantern, his mug, seedlings, pots, the web over it.
    reb.wall(kit.table("Potting bench", bench_m, (X1 - 0.3, 2.3, 0.0), size=(0.55, 2.4, 0.85)))
    reb.prim("cube", "Bench shelf", bench_m, (X1 - 0.3, 2.3, 0.25), (0.5, 2.3, 0.03))
    lamp, lamp_light, flame = kit.lantern("Lantern", (X1 - 0.3, 1.75, 0.85), energy=18)
    reb.prim("cyl", "Mug", reb.mat_plain("Enamel", (0.5, 0.52, 0.55), 0.35), (X1 - 0.35, 2.05, 0.9), (0.09, 0.09, 0.1), segments=12)
    reb.prim("cyl", "Cold tea", reb.mat_plain("Tea", (0.06, 0.03, 0.01), 0.1), (X1 - 0.35, 2.05, 0.94), (0.075, 0.075, 0.003), segments=12)
    kit.box("Seed tray", mat("pine"), (X1 - 0.3, 2.55, 0.85), (0.4, 0.32, 0.06))
    reb.prim("cube", "Tray soil", reb.mat_surface("Potting soil", [(0.0, (0.03, 0.02, 0.012)), (1.0, (0.08, 0.055, 0.035))], scale=30, bump=0.8), (X1 - 0.3, 2.55, 0.905), (0.36, 0.28, 0.01))
    sv, sf = [], []
    for _ in range(24):
        p = Vector((X1 - 0.3 + rng.uniform(-0.16, 0.16), 2.55 + rng.uniform(-0.12, 0.12), 0.91))
        a = rng.uniform(0, 2 * math.pi)
        reb.card(sv, sf, p, Vector((math.cos(a), math.sin(a), 0.6)).normalized(), Vector((0, 0, 1)), 0.025, 0.07, 0.8)
    reb.mesh_object("Seedlings, wilting", sv, sf, reb.mat_cards("Wilting", (0.05, 0.07, 0.02), (0.14, 0.15, 0.05)))
    for i in range(5):
        reb.prim("cone", f"Pot {i}", reb.mat_plain("Terracotta", (0.3, 0.12, 0.06), 0.8), (X1 - 0.3, 2.95 + (i % 3) * 0.14, 0.92 + (i // 3) * 0.09), (0.13, 0.13, 0.13), rot=(math.pi, 0, 0), top=0.7, segments=10)
    for i in range(6):
        reb.prim("cone", f"Pot under {i}", reb.mat_plain("Terracotta", (0.3, 0.12, 0.06), 0.8), (X1 - 0.3, 1.4 + i * 0.12, 0.33 + (i % 2) * 0.06), (0.15, 0.15, 0.14), rot=(math.pi, 0, 0), top=0.7, segments=10)
    reb.prim("cube", "Seed packets", mat("old paper"), (X1 - 0.25, 3.25, 0.86), (0.1, 0.07, 0.01), rot=(0, 0, 0.4))
    reb.prim("cube", "Trowel", mat("steel"), (X1 - 0.4, 3.35, 0.86), (0.2, 0.06, 0.01), rot=(0, 0, 1.0))

    # ---- The key board on the north wall by the door: the cellar key on its red tag.
    kx = 1.75
    reb.prim("cube", "Key board", mat("dark wood"), (kx, Y0 + 0.015, 1.45), (0.7, 0.03, 0.45))
    kit.text("Key board label", "ESTATE KEYS", mat("white paint"), (kx, Y0 + 0.033, 1.62), size=0.045, rot=(math.pi / 2, 0, math.pi))
    labels = ("CELLAR", "SHED", "", "GATE", "", "STABLE")
    for i, lab in enumerate(labels):
        x = kx - 0.27 + (i % 3) * 0.27
        z = 1.48 - (i // 3) * 0.2
        reb.prim("cyl", f"Key hook {i}", mat("steel"), (x, Y0 + 0.05, z), (0.01, 0.01, 0.05), rot=(math.pi / 2, 0, 0), segments=6)
        if lab:
            kit.text(f"Hook label {i}", lab, mat("white paint"), (x, Y0 + 0.033, z + 0.05), size=0.025, rot=(math.pi / 2, 0, math.pi))
        if i in (2, 4):
            continue
        big = i == 0
        km = mat("iron") if big else reb.mat_metal("Brass", (0.45, 0.33, 0.12), 0.45)
        reb.prim("cyl", f"Key bow {i}", km, (x, Y0 + 0.06, z - 0.04), (0.05 if big else 0.03, 0.05 if big else 0.03, 0.01), rot=(math.pi / 2, 0, 0), segments=10)
        reb.prim("cube", f"Key shank {i}", km, (x, Y0 + 0.06, z - 0.12 if big else z - 0.08), (0.012, 0.01, 0.14 if big else 0.07))
        reb.prim("cube", f"Key tag {i}", red_tag if big else mat("old paper"), (x + 0.03, Y0 + 0.055, z - 0.06), (0.04, 0.005, 0.06), rot=(0, 0.3, 0))
    reb.prim("cube", "Calendar", mat("paper"), (2.75, Y0 + 0.012, 1.45), (0.35, 0.01, 0.48))
    reb.prim("cube", "Calendar picture", reb.mat_plain("Calendar roses", (0.3, 0.08, 0.08), 0.8), (2.75, Y0 + 0.018, 1.58), (0.3, 0.004, 0.18))
    kit.text("Calendar month", "JULY 1998", mat("black"), (2.75, Y0 + 0.022, 1.45), size=0.04, rot=(math.pi / 2, 0, math.pi))
    for d in range(20):
        x = 2.62 + (d % 7) * 0.04
        z = 1.39 - (d // 7) * 0.05
        kit.rod("Crossed off", mat("red paint"), (x - 0.012, Y0 + 0.02, z - 0.012), (x + 0.012, Y0 + 0.02, z + 0.012), 0.002, 4)

    # ---- The tools along the south wall; sacks in the corner, one gnawed open; the rat.
    reb.prim("cube", "Tool rail", mat("dark wood"), (2.4, Y1 - 0.02, 1.75), (2.2, 0.04, 0.08))
    tools = (("Rake", 1.5, 0.4, 0.06), ("Hoe", 1.8, 0.15, 0.1), ("Fork", 2.1, 0.17, 0.22), ("Spade", 2.4, 0.18, 0.26), ("Edger", 2.7, 0.22, 0.12))
    for name, x, w, hgt in tools:
        kit.rod(f"{name} handle", mat("pine"), (x, Y1 - 0.06, 1.77), (x + 0.03, Y1 - 0.07, 0.42), 0.016, 6)
        reb.prim("cube", f"{name} head", mat("rust"), (x + 0.03, Y1 - 0.07, 0.36), (w, 0.02, hgt))
    reb.prim("cube", "Saw", mat("steel"), (3.05, Y1 - 0.04, 1.45), (0.5, 0.01, 0.13), rot=(0, 0.1, 0))
    reb.prim("cube", "Shears", mat("steel"), (3.3, Y1 - 0.05, 1.3), (0.06, 0.02, 0.45), rot=(0, 0.25, 0))
    hose_v, hose_f = [], []
    for k in range(4):
        for i in range(24):
            a0, a1 = 2 * math.pi * i / 24, 2 * math.pi * (i + 1) / 24
            r = 0.25 - k * 0.02
            reb.box(hose_v, hose_f, (1.3 + math.cos(a0) * r, Y1 - 0.08, 1.2 + math.sin(a0) * r), (0.06, 0.04, 0.06))
    reb.mesh_object("Hose coil", hose_v, hose_f, mat("green paint"))
    for i, (x, y, rz, tip) in enumerate(((3.45, 3.4, 0.2, 0.0), (3.0, 3.5, -0.3, 0.0), (3.4, 2.95, 1.2, 0.0), (2.55, 3.45, 0.6, 1.2))):
        reb.prim("cube", f"Sack {i}", sack_m, (x, y, 0.3 if not tip else 0.2), (0.55, 0.4, 0.6 if not tip else 0.4), rot=(0, tip, rz), bevel=0.1)
    reb.wall(reb.prim("cube", "Sacks footprint", None, (3.25, 3.3, 0.4), (1.1, 1.0, 0.8))).hide_render = True
    # Watering cans and a stack of pots in the north-west corner, by the key board.
    for i in range(2):
        reb.prim("cyl", f"Watering can {i}", mat("green paint"), (1.25 + i * 0.25, 1.3, 0.17), (0.2, 0.2, 0.34), segments=12)
        kit.rod(f"Can spout {i}", mat("green paint"), (1.3 + i * 0.25, 1.35, 0.15), (1.45 + i * 0.25, 1.55, 0.38), 0.015, 6)
    reb.wall(reb.prim("cube", "Cans footprint", None, (1.35, 1.3, 0.4), (0.6, 0.5, 0.8))).hide_render = True
    kit.text("Sack stencil", "BONE MEAL", mat("black"), (3.0, 3.29, 0.38), size=0.06, rot=(math.pi / 2, 0, -0.3))
    mv, mf = [], []
    for i in range(10):
        kit._stain(mv, mf, rng, (2.3 + rng.gauss(0, 0.2), 3.2 + rng.gauss(0, 0.15), 0.004), rng.uniform(0.06, 0.15), rng.uniform(0, 3), 0.4, (1.3, 0.8), i, points=12, drops=False)
    reb.mesh_object("Spilled meal", mv, mf, meal, smooth=False)
    # The rat, on its back, swollen, fur coming away; the trap beside it, unsprung.
    rx, ry = 2.05, 2.95
    rat = kit.join("Dead rat", [
        reb.prim("sphere", "body", rat_fur, (0, 0, 0.05), (0.22, 0.1, 0.1), segments=12),
        reb.prim("cone", "head", rat_fur, (0.14, 0, 0.05), (0.07, 0.07, 0.1), rot=(0, math.pi / 2, 0), segments=10),
        reb.prim("sphere", "belly", rat_skin, (0.0, 0, 0.09), (0.15, 0.07, 0.04), segments=10),
        kit.rod("tail", rat_skin, (-0.1, 0, 0.04), (-0.32, 0.08, 0.01), 0.006, 4),
        kit.rod("leg", rat_skin, (0.05, 0.03, 0.08), (0.07, 0.06, 0.14), 0.008, 4),
        kit.rod("leg", rat_skin, (0.05, -0.03, 0.08), (0.07, -0.06, 0.14), 0.008, 4),
        kit.rod("leg", rat_skin, (-0.06, 0.03, 0.08), (-0.08, 0.06, 0.13), 0.008, 4),
        kit.rod("leg", rat_skin, (-0.06, -0.03, 0.08), (-0.08, -0.06, 0.13), 0.008, 4),
    ])
    settle(rat, (0, 0, 0.05))
    rat.location = (rx, ry, 0.0)
    rat.rotation_euler = (0, 0, 0.7)
    kit.splat("Under the rat", mat("old blood"), (rx, ry, 0.0), 0.08, seed=4)
    reb.prim("cube", "Rat trap", mat("pine"), (rx + 0.35, ry - 0.2, 0.01), (0.18, 0.08, 0.02))
    reb.prim("cube", "Trap spring", mat("steel"), (rx + 0.35, ry - 0.2, 0.03), (0.14, 0.07, 0.005))
    reb.prim("cube", "Bait", reb.mat_plain("Cheese", (0.5, 0.4, 0.1), 0.6), (rx + 0.3, ry - 0.2, 0.03), (0.03, 0.03, 0.015))
    # Mud trodden in at the door, his boots by it.
    for i in range(5):
        kit.splat(f"Mud {i}", mat("mud"), (X0 + 0.3 + i * 0.22, 2.4 + (0.1 if i % 2 else -0.1), 0.0), 0.06, seed=30 + i, stretch=(1.5, 0.6))
    reb.prim("cube", "Boot", mat("rubber"), (X0 + 0.3, 3.55, 0.17), (0.3, 0.13, 0.34), bevel=0.03)
    reb.prim("cube", "Boot, fallen", mat("rubber"), (X0 + 0.55, 3.5, 0.07), (0.34, 0.13, 0.13), rot=(0, 0, 0.4), bevel=0.03)
    reb.wall(shelves("Shelves", mat("planks"), (2.2, Y0 + 0.17, 0.0), size=(0.6, 0.28, 1.0), rows=3, clutter=0.8, seed=5))

    # ---- Light: the lantern, moonlight through the window.
    kit.time_light("night", sun_heading=250, sun_energy=0.3)
    reb.spot("Moon through the window", (X0 - 2.5, 3.9, 2.4), (2.4, 3.0, 0.0), 60, (0.55, 0.65, 0.9), 30, 0.5, 0.2)
    reb.point("Lantern bounce", ((X0 + X1) / 2, 2.4, 1.9), 4, (1.0, 0.65, 0.35), 0.5)

    anim = kit.Anim(16)
    anim.flicker(lamp_light, flame, depth=0.25, dropouts=1)
    rest = [v.co.copy() for v in the_web.data.vertices]
    corner = Vector((X0 + 0.02, WINDOW[1] + 0.05, WINDOW[3] + 0.05))

    def tremble(k):
        for i, v in enumerate(the_web.data.vertices):
            d = (rest[i] - corner).length
            off = 0.08 * d * math.sin(anim.phase(k, 2) + i * 0.05)
            v.co = (rest[i].x + off * 0.4, rest[i].y - off * 0.6, rest[i].z + off * 0.2)
        the_web.data.update()
    anim.custom(tremble)
    anim.flies((rx, ry, 0.05), count=6, radius=0.18)

    # ---- What the game needs.
    room.door("back-garden", (X0, DOOR[0], X0 + 0.5, DOOR[1]), arrive=(1.75, 2.5), face=(1, 0))
    room.check((1.3, Y0, 2.2, Y0 + 0.6), "The estate's spare keys. CELLAR, on a red tag.\nTwo of the hooks are empty.")
    room.check((2.5, Y0, 3.0, Y0 + 0.6), "A calendar. July, crossed off day by day.\nIt stops at the 20th.")
    room.check((X1 - 0.7, 1.4, X1, 2.2), "His lantern's still lit. The tea's stone cold.")
    room.check((1.8, 2.7, 2.6, 3.3), "A dead rat. Swollen. Its fur's falling out.\nThe trap didn't get it. Something else did.")
    room.check((2.6, 2.9, X1, Y1), "Bone meal. Something's gnawed a sack open.")
    room.check((1.3, Y1 - 0.6, 2.9, Y1), "His tools. Clean and in a row.")
    room.entry = "A potting shed. The lantern's lit."
    room.export(anim, samples=128)


build()
