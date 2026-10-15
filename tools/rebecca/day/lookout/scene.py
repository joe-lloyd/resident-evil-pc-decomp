"""The ranger's lookout, inside: a one-room log cabin, the morning after.

The ranger left in a hurry. Breakfast is half eaten, a chair lies where it
fell, the rifle is gone from its rack, and the east window is smashed in with
blood on the sill. The stove is still warm and the lamp still burns. The radio
on the desk hisses with S.T.A.R.S. chatter. His keys hang by the door. His
typewriter stands on a table in the corner by the window, and the item box
at the bunk's foot: she saves here.

Metres, real sizes (reb.UNITS turns them into game units): the floor is
x 2.0-7.0, y 2.0-6.0, the ceiling 2.45 up. The door is in the south wall.

Moving (reb.export anim): the lamp flame and its light, the fire behind the
stove's grate, the radio's signal lamp, and the curtain at the broken window.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from mathutils import Vector  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))

X0, X1, Y0, Y1, H = 2.0, 7.0, 2.0, 6.0, 2.45
DOOR = (3.5, 4.4)          # x, south wall, 2.0 high
NORTH_WINDOW = (3.0, 3.9, 0.95, 1.75)   # x0, x1, z0, z1
EAST_WINDOW = (2.6, 3.5, 1.0, 1.7)      # y0, y1, z0, z1
FRAMES = 16


def G(x, y, z=0.0):
    """Blender metres to a game point (X, Y, Z)."""
    return (reb.g(x), -reb.g(z), reb.g(y))


CAMERAS = [
    # 0: high in the south-west corner, over the stove: the desk, the table, the bunk.
    {"from": G(2.6, 5.8, 2.2), "to": G(5.9, 2.75, 0.55), "fov": 200},
    # 1: high in the north-east corner: the stove, the door and its pegs, the table.
    {"from": G(6.8, 2.85, 2.2), "to": G(2.9, 5.3, 0.5), "fov": 200},
]


def build():
    rng = random.Random(11)
    reb.clear_scene()

    logs = reb.mat_wood("Logs", (0.21, 0.13, 0.075))
    chink = reb.mat_surface("Chinking", [(0.0, (0.32, 0.29, 0.24)), (1.0, (0.45, 0.41, 0.34))], scale=30, bump=0.4)
    boards = reb.mat_wood("Floorboards", (0.17, 0.11, 0.065))
    dark = reb.mat_wood("Dark wood", (0.09, 0.055, 0.035))
    pine = reb.mat_wood("Pine", (0.3, 0.2, 0.11))
    iron = reb.mat_metal("Iron", (0.05, 0.048, 0.045), rough=0.6)
    tin = reb.mat_metal("Tin", (0.55, 0.53, 0.5), rough=0.4)
    brass = reb.mat_metal("Brass", (0.7, 0.5, 0.2), rough=0.3)
    olive = reb.mat_plain("Radio olive", (0.07, 0.08, 0.05), rough=0.5)
    black = reb.mat_plain("Bakelite", (0.015, 0.015, 0.015), rough=0.3)
    paper = reb.mat_surface("Paper", [(0.0, (0.58, 0.55, 0.45)), (1.0, (0.7, 0.66, 0.55))], scale=20, bump=0.05)
    glass = reb.mat_glass("Glass")
    blood = reb.mat_plain("Blood", (0.12, 0.005, 0.005), rough=0.25)
    beans = reb.mat_surface("Beans", [(0.0, (0.35, 0.12, 0.04)), (1.0, (0.5, 0.2, 0.06))], scale=60, bump=0.8)
    enamel = reb.mat_plain("Enamel", (0.55, 0.6, 0.62), rough=0.35)
    wool = reb.mat_stripes("Wool blanket", [(0.3, 0.07, 0.05), (0.3, 0.07, 0.05), (0.05, 0.05, 0.05), (0.42, 0.33, 0.15)], across=10)
    rug = reb.mat_stripes("Rag rug", [(0.28, 0.12, 0.08), (0.12, 0.16, 0.2), (0.36, 0.3, 0.2), (0.15, 0.1, 0.08)], across=14, axis="Y")
    ticking = reb.mat_stripes("Ticking", [(0.5, 0.48, 0.42), (0.2, 0.22, 0.3)], across=40)
    curtain_m = reb.mat_stripes("Curtain", [(0.32, 0.1, 0.06), (0.32, 0.1, 0.06), (0.45, 0.38, 0.22), (0.12, 0.1, 0.06)], across=24, axis="Y")
    mapm = reb.mat_surface("Survey map", [(0.0, (0.35, 0.42, 0.25)), (0.45, (0.55, 0.55, 0.38)), (0.5, (0.3, 0.22, 0.12)), (0.55, (0.6, 0.58, 0.42)), (1.0, (0.62, 0.6, 0.48))], scale=9, bump=0.05)
    felt = reb.mat_plain("Felt hat", (0.25, 0.2, 0.12), rough=0.95)
    cardm = reb.mat_plain("Playing card", (0.75, 0.73, 0.68), rough=0.6)
    red_label = reb.mat_plain("Label", (0.5, 0.1, 0.06), rough=0.7)
    books = [reb.mat_plain(f"Book {i}", c, 0.7) for i, c in enumerate([(0.25, 0.06, 0.04), (0.06, 0.12, 0.2), (0.12, 0.16, 0.08), (0.35, 0.28, 0.12)])]

    # ---- The shell: log walls on chinking, floorboards, a boarded ceiling on beams.
    r = 0.125

    def gaps(a0, a1, z, holes):
        """The spans of a0..a1 a log at height z keeps, round the openings (a0, a1, z0, z1)."""
        spans = [(a0, a1)]
        for h0, h1, hz0, hz1 in holes:
            if z + r <= hz0 or z - r >= hz1:
                continue
            spans = [p for s0, s1 in spans for p in ((s0, min(s1, h0)), (max(s0, h1), s1)) if p[1] - p[0] > 0.02]
        return spans

    def log_wall(axis, at, a0, a1, holes):
        k = 0
        z = r
        while z < H + r:
            for s0, s1 in gaps(a0 - 0.28, a1 + 0.28, z, holes):
                mid, length = (s0 + s1) / 2, s1 - s0
                wobble = rng.uniform(-0.012, 0.012)
                if axis == "x":
                    reb.prim("cyl", f"Log {at:.1f} {k}", logs, (mid, at, z), (2 * r + wobble, 2 * r, length), rot=(0, math.pi / 2, 0), segments=14)
                else:
                    reb.prim("cyl", f"Log {at:.1f} {k}", logs, (at, mid, z), (2 * r + wobble, 2 * r, length), rot=(math.pi / 2, 0, 0), segments=14)
                k += 1
            z += 2 * r
        # Chinking behind the logs, with the same openings.
        for s0, s1 in gaps(a0, a1, H / 2, [(h0, h1, -1, 9) for h0, h1, *_ in holes]):
            if axis == "x":
                reb.prim("cube", "Chinking", chink, ((s0 + s1) / 2, at, H / 2), (s1 - s0, 0.04, H))
            else:
                reb.prim("cube", "Chinking", chink, (at, (s0 + s1) / 2, H / 2), (0.04, s1 - s0, H))
        for h0, h1, hz0, hz1 in holes:
            for zz0, zz1 in ((0, hz0), (hz1, H)):
                if zz1 - zz0 > 0.01:
                    if axis == "x":
                        reb.prim("cube", "Chinking", chink, ((h0 + h1) / 2, at, (zz0 + zz1) / 2), (h1 - h0, 0.04, zz1 - zz0))
                    else:
                        reb.prim("cube", "Chinking", chink, (at, (h0 + h1) / 2, (zz0 + zz1) / 2), (0.04, h1 - h0, zz1 - zz0))

    log_wall("x", Y0 - r, X0, X1, [(NORTH_WINDOW[0], NORTH_WINDOW[1], NORTH_WINDOW[2], NORTH_WINDOW[3])])
    log_wall("x", Y1 + r, X0, X1, [(DOOR[0], DOOR[1], 0.0, 2.0)])
    log_wall("y", X0 - r, Y0, Y1, [])
    log_wall("y", X1 + r, Y0, Y1, [(EAST_WINDOW[0], EAST_WINDOW[1], EAST_WINDOW[2], EAST_WINDOW[3])])

    # Floorboards, each its own length and shade.
    y = Y0 - 0.1
    while y < Y1 + 0.1:
        w = rng.choice((0.13, 0.15, 0.17))
        reb.prim("cube", "Board", boards, ((X0 + X1) / 2 + rng.uniform(-0.1, 0.1), y + w / 2, -0.015 + rng.uniform(-0.003, 0.003)),
                 (0.03, w - 0.008, X1 - X0 + 0.5), rot=(0, math.pi / 2, 0), bevel=0.004)
        y += w
    reb.prim("cube", "Under floor", reb.mat_plain("Void", (0.01, 0.008, 0.006)), ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.05), (X1 - X0 + 1, Y1 - Y0 + 1, 0.02))
    # Ceiling boards and three beams across.
    reb.prim("cube", "Ceiling", dark, ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.03), (X1 - X0 + 0.6, Y1 - Y0 + 0.6, 0.06))
    for by in (3.0, 4.2, 5.4):
        reb.prim("cube", "Beam", dark, ((X0 + X1) / 2, by, H - 0.09), (X1 - X0 + 0.5, 0.16, 0.18), bevel=0.01)

    # The door: planks with a Z brace, shut, in a frame.
    dw = DOOR[1] - DOOR[0]
    for i in range(5):
        reb.prim("cube", "Door plank", pine, (DOOR[0] + dw * (i + 0.5) / 5, Y1 + 0.04, 1.0), (dw / 5 - 0.006, 0.04, 2.0), bevel=0.004)
    for z in (0.35, 1.65):
        reb.prim("cube", "Door rail", pine, ((DOOR[0] + DOOR[1]) / 2, Y1 + 0.005, z), (dw - 0.08, 0.03, 0.12))
    reb.prim("cube", "Door brace", pine, ((DOOR[0] + DOOR[1]) / 2, Y1 + 0.004, 1.0), (0.1, 0.03, 1.5), rot=(0, math.atan2(dw - 0.15, 1.3), 0))
    reb.prim("cube", "Door latch", iron, (DOOR[0] + 0.12, Y1 - 0.02, 1.05), (0.12, 0.03, 0.03))
    for x in DOOR:
        reb.prim("cube", "Door post", dark, (x, Y1 + 0.02, 1.05), (0.1, 0.16, 2.1))
    reb.prim("cube", "Door head", dark, ((DOOR[0] + DOOR[1]) / 2, Y1 + 0.02, 2.06), (dw + 0.2, 0.16, 0.1))

    # ---- Windows: the north one whole, the east one smashed in.
    def window(axis, at, a0, a1, z0, z1, broken):
        for a in (a0, a1):
            if axis == "x":
                reb.prim("cube", "Window post", dark, (a, at, (z0 + z1) / 2), (0.07, 0.2, z1 - z0 + 0.07))
            else:
                reb.prim("cube", "Window post", dark, (at, a, (z0 + z1) / 2), (0.2, 0.07, z1 - z0 + 0.07))
        for z in (z0, z1, (z0 + z1) / 2):
            if axis == "x":
                reb.prim("cube", "Window bar", dark, ((a0 + a1) / 2, at, z), (a1 - a0, 0.2 if z != (z0 + z1) / 2 else 0.04, 0.06))
            else:
                reb.prim("cube", "Window bar", dark, (at, (a0 + a1) / 2, z), (0.2 if z != (z0 + z1) / 2 else 0.04, a1 - a0, 0.06))
        if not broken:
            reb.prim("cube", "Window glass", glass, ((a0 + a1) / 2, at, (z0 + z1) / 2), (a1 - a0, 0.006, z1 - z0))
            return
        # Shards left in the frame.
        v, f = [], []
        for i in range(7):
            a = rng.uniform(a0 + 0.02, a1 - 0.02)
            base = z0 + 0.03 if i % 2 else z1 - 0.03
            tip = base + (rng.uniform(0.06, 0.2) * (1 if i % 2 else -1))
            k = len(v)
            v += [(at, a - 0.04, base), (at, a + 0.04, base), (at, a + rng.uniform(-0.03, 0.03), tip)]
            f.append((k, k + 1, k + 2))
        reb.mesh_object("Window shards", v, f, glass, smooth=False)

    window("x", Y0 - 0.02, NORTH_WINDOW[0], NORTH_WINDOW[1], NORTH_WINDOW[2], NORTH_WINDOW[3], False)
    window("y", X1 + 0.02, EAST_WINDOW[0], EAST_WINDOW[1], EAST_WINDOW[2], EAST_WINDOW[3], True)
    # Blood on the sill and down the wall.
    reb.prim("cube", "Blood sill", blood, (X1 - 0.03, 3.1, EAST_WINDOW[2] + 0.035), (0.08, 0.3, 0.004))
    for i in range(5):
        reb.prim("cube", "Blood run", blood, (X1 - 0.005, 2.95 + i * 0.07, EAST_WINDOW[2] - 0.1 - i * 0.03), (0.004, 0.02, 0.2 + i * 0.05))
    # Outside: bright morning, so the windows glow.
    sky = reb.mat_emit("Outside", (0.85, 0.9, 1.0), 3.5)
    reb.prim("plane", "Outside north", sky, ((NORTH_WINDOW[0] + NORTH_WINDOW[1]) / 2, Y0 - 2.5, 1.4), (4, 1, 3), rot=(math.pi / 2, 0, 0))
    reb.prim("plane", "Outside east", sky, (X1 + 2.5, 3.05, 1.4), (1, 4, 3), rot=(0, math.pi / 2, 0))

    # ---- Furniture. wall(): blocks her; mask(): may stand in front of her.
    def solid(ob, masked=True):
        reb.wall(ob)
        if masked:
            reb.mask(ob)
        return ob

    def legs(name, mat, x0, x1, y0, y1, h, t=0.05):
        for x in (x0 + t / 2, x1 - t / 2):
            for yy in (y0 + t / 2, y1 - t / 2):
                reb.mask(reb.prim("cube", name, mat, (x, yy, h / 2), (t, t, h)))

    # The desk under the north window, a drawer pedestal on its left.
    solid(reb.prim("cube", "Desk", dark, (3.1, 2.4, 0.74), (1.6, 0.7, 0.04), bevel=0.006))
    legs("Desk leg", dark, 3.35, 3.9, 2.05, 2.75, 0.72)
    reb.mask(reb.prim("cube", "Desk pedestal", dark, (2.55, 2.4, 0.36), (0.46, 0.64, 0.72), bevel=0.005))
    for i in range(3):
        reb.mask(reb.prim("cube", "Drawer", pine, (2.55, 2.73, 0.12 + i * 0.22), (0.4, 0.02, 0.19), bevel=0.004))
        reb.mask(reb.prim("cyl", "Drawer knob", brass, (2.55, 2.75, 0.14 + i * 0.22), (0.025, 0.025, 0.02), rot=(math.pi / 2, 0, 0)))
    # The radio: a field set with dials, a meter and a signal lamp.
    reb.mask(reb.prim("cube", "Radio", olive, (2.75, 2.28, 0.89), (0.46, 0.28, 0.26), bevel=0.01))
    for i, (dx, dz) in enumerate(((-0.15, 0.05), (-0.06, 0.05), (0.04, -0.05), (0.13, -0.05))):
        reb.mask(reb.prim("cyl", "Radio dial", black, (2.75 + dx, 2.425, 0.89 + dz), (0.05, 0.05, 0.025), rot=(math.pi / 2, 0, 0)))
    meter = reb.mat_emit("Radio meter", (1.0, 0.7, 0.3), 2.5)
    reb.prim("cube", "Radio meter", meter, (2.82, 2.422, 0.95), (0.12, 0.01, 0.06))
    signal = reb.mat_emit("Radio signal", (1.0, 0.25, 0.08), 12)
    reb.prim("sphere", "Radio signal lamp", signal, (2.6, 2.425, 0.83), (0.022, 0.022, 0.022))
    reb.prim("cyl", "Radio cable", black, (2.95, 2.18, 0.76), (0.012, 0.012, 0.5), rot=(0, math.pi / 2, 0.3))
    # Microphone on its stand.
    reb.prim("cyl", "Mic base", black, (3.15, 2.52, 0.775), (0.09, 0.09, 0.025))
    reb.prim("cyl", "Mic stem", iron, (3.15, 2.52, 0.86), (0.012, 0.012, 0.16))
    reb.prim("sphere", "Mic head", iron, (3.15, 2.5, 0.95), (0.05, 0.06, 0.07))
    # The logbook lying open, papers, a pencil, a mug, an ashtray.
    for side in (-1, 1):
        reb.prim("cube", "Logbook page", paper, (3.47 + side * 0.11, 2.45, 0.768 + 0.004), (0.21, 0.29, 0.012), rot=(0, side * 0.06, 0.08))
    reb.prim("cube", "Logbook cover", reb.mat_plain("Ledger cloth", (0.12, 0.08, 0.06)), (3.47, 2.45, 0.763), (0.46, 0.31, 0.006), rot=(0, 0, 0.08))
    for i in range(6):
        reb.prim("cube", "Paper", paper, (rng.uniform(2.95, 3.85), rng.uniform(2.2, 2.68), 0.762 + i * 0.002), (0.21, 0.28, 0.002), rot=(0, 0, rng.uniform(-0.6, 0.6)))
    reb.prim("cyl", "Pencil", reb.mat_plain("Pencil", (0.7, 0.55, 0.1)), (3.3, 2.66, 0.768), (0.008, 0.008, 0.17), rot=(0, math.pi / 2, 0.4))
    reb.prim("cyl", "Mug", enamel, (3.78, 2.3, 0.81), (0.085, 0.085, 0.1), segments=20)
    reb.prim("cyl", "Coffee", reb.mat_plain("Coffee", (0.04, 0.02, 0.01), 0.1), (3.78, 2.3, 0.85), (0.075, 0.075, 0.005))
    reb.prim("cyl", "Ashtray", glass, (3.62, 2.64, 0.77), (0.12, 0.12, 0.025), segments=20)
    for i in range(4):
        reb.prim("cyl", "Butt", reb.mat_plain("Butt", (0.75, 0.65, 0.5)), (3.62 + rng.uniform(-0.03, 0.03), 2.64 + rng.uniform(-0.03, 0.03), 0.79), (0.008, 0.008, 0.035), rot=(math.pi / 2, 0, rng.uniform(0, 3)))
    # The desk chair, tucked in under the desk so nothing on it is out of reach.
    chair_at, chair_turn = (3.62, 2.62), math.pi
    def chair(name, at, turn, tipped=False):
        parts = []
        c, s = math.cos(turn), math.sin(turn)
        def p(dx, dy, z):
            return (at[0] + dx * c - dy * s, at[1] + dx * s + dy * c, z)
        if not tipped:
            parts.append(reb.prim("cube", name, pine, p(0, 0, 0.45), (0.42, 0.42, 0.035), rot=(0, 0, turn), bevel=0.004))
            for dx in (-0.18, 0.18):
                for dy in (-0.18, 0.18):
                    parts.append(reb.prim("cube", name + " leg", pine, p(dx, dy, 0.225), (0.035, 0.035, 0.45), rot=(0, 0, turn)))
                parts.append(reb.prim("cube", name + " back post", pine, p(dx, 0.19, 0.68), (0.035, 0.035, 0.46), rot=(0, 0, turn)))
            for z in (0.68, 0.86):
                parts.append(reb.prim("cube", name + " back rail", pine, p(0, 0.19, z), (0.36, 0.025, 0.06), rot=(0, 0, turn)))
        else:
            # On its back: the seat stands up, the back lies on the floor.
            parts.append(reb.prim("cube", name, pine, p(0, 0, 0.21), (0.42, 0.035, 0.42), rot=(0, 0, turn), bevel=0.004))
            for dx in (-0.18, 0.18):
                for dz in (0.03, 0.39):
                    parts.append(reb.prim("cube", name + " leg", pine, p(dx, -0.225, dz), (0.035, 0.45, 0.035), rot=(0, 0, turn)))
                parts.append(reb.prim("cube", name + " back post", pine, p(dx, 0.2, 0.03), (0.035, 0.46, 0.035), rot=(0, 0, turn)))
            parts.append(reb.prim("cube", name + " back rail", pine, p(0, 0.38, 0.03), (0.36, 0.06, 0.025), rot=(0, 0, turn)))
        for ob in parts:
            reb.mask(ob)
        reb.wall(parts[0])
        return parts

    chair("Desk chair", chair_at, chair_turn)

    # The survey map pinned left of the window.
    reb.prim("cube", "Survey map", mapm, (2.45, Y0 + 0.005, 1.4), (0.75, 0.006, 0.55))
    for dx, dz in ((-0.34, 0.25), (0.34, 0.25), (-0.34, -0.25), (0.34, -0.25)):
        reb.prim("sphere", "Pin", red_label, (2.45 + dx, Y0 + 0.012, 1.4 + dz), (0.015, 0.015, 0.015))
    reb.prim("cyl", "Map circle", red_label, (2.62, Y0 + 0.01, 1.28), (0.09, 0.09, 0.004), rot=(math.pi / 2, 0, 0))

    # Shelves right of the desk: tins, jars, books, a lantern, a first aid tin.
    sx0, sx1 = 4.55, 5.85
    for x in (sx0, sx1):
        solid(reb.prim("cube", "Shelf side", dark, (x, 2.2, 0.92), (0.03, 0.36, 1.84)))
    for z in (0.08, 0.55, 1.0, 1.45, 1.82):
        reb.mask(reb.prim("cube", "Shelf", dark, ((sx0 + sx1) / 2, 2.2, z), (sx1 - sx0, 0.36, 0.025)))
    reb.wall(reb.prim("cube", "Shelf body", None, ((sx0 + sx1) / 2, 2.2, 0.01), (sx1 - sx0, 0.36, 0.02))).hide_render = True
    for row, z in enumerate((0.09, 0.56, 1.01, 1.46)):
        x = sx0 + 0.06
        while x < sx1 - 0.08:
            kind = rng.random()
            if row == 2 and kind < 0.6:
                w = rng.uniform(0.03, 0.06)
                hgt = rng.uniform(0.2, 0.3)
                reb.mask(reb.prim("cube", "Book", rng.choice(books), (x + w / 2, 2.22, z + hgt / 2), (w, 0.22, hgt), rot=(0, rng.uniform(-0.05, 0.05), 0)))
                x += w + 0.004
            elif kind < 0.5:
                reb.mask(reb.prim("cyl", "Tin", tin if rng.random() < 0.6 else red_label, (x + 0.045, 2.2, z + 0.06), (0.085, 0.085, 0.12)))
                x += 0.1
            elif kind < 0.8:
                hgt = rng.uniform(0.12, 0.2)
                reb.mask(reb.prim("cyl", "Jar", glass, (x + 0.05, 2.2, z + hgt / 2), (0.09, 0.09, hgt)))
                reb.prim("cyl", "Jar contents", beans if rng.random() < 0.5 else reb.mat_plain("Flour", (0.7, 0.68, 0.6)), (x + 0.05, 2.2, z + hgt / 3), (0.08, 0.08, hgt * 0.6))
                x += 0.11
            else:
                x += rng.uniform(0.05, 0.15)
    reb.mask(reb.prim("cube", "First aid tin", reb.mat_plain("White tin", (0.7, 0.7, 0.66), 0.4), (5.5, 2.2, 1.53), (0.28, 0.18, 0.14), bevel=0.01))
    reb.prim("cube", "First aid cross", red_label, (5.5, 2.105, 1.53), (0.06, 0.004, 0.02))
    reb.prim("cube", "First aid cross", red_label, (5.5, 2.105, 1.53), (0.02, 0.004, 0.06))

    # The table in the middle: breakfast, the lamp, cards laid out for patience.
    tx, ty = 4.5, 4.0
    solid(reb.prim("cube", "Table", pine, (tx, ty, 0.74), (1.1, 0.75, 0.04), bevel=0.006))
    legs("Table leg", pine, tx - 0.5, tx + 0.5, ty - 0.32, ty + 0.32, 0.72, 0.06)
    reb.prim("cyl", "Plate", enamel, (4.2, 3.86, 0.77), (0.24, 0.24, 0.02), segments=24)
    for i in range(18):
        reb.prim("sphere", "Bean", beans, (4.2 + rng.uniform(-0.06, 0.06), 3.86 + rng.uniform(-0.06, 0.06), 0.785), (0.025, 0.018, 0.015), segments=8)
    reb.prim("cube", "Fork", tin, (4.33, 3.95, 0.782), (0.18, 0.015, 0.004), rot=(0, 0, 0.5))
    reb.prim("cyl", "Bean tin", tin, (4.0, 4.12, 0.81), (0.08, 0.08, 0.11))
    reb.prim("cyl", "Bean tin label", red_label, (4.0, 4.12, 0.81), (0.082, 0.082, 0.07))
    reb.prim("cone", "Coffee pot", enamel, (4.95, 4.2, 0.85), (0.14, 0.14, 0.2), top=0.65)
    for i in range(14):
        col, row = i % 7, i // 7
        reb.prim("cube", "Card", cardm, (4.42 + col * 0.075, 4.2 + row * 0.05, 0.762 + row * 0.001), (0.06, 0.09, 0.002), rot=(0, 0, rng.uniform(-0.05, 0.05)))
    # The oil lamp: brass foot, glass font and chimney, a flame inside.
    lx, ly = 4.75, 3.82
    reb.prim("cyl", "Lamp foot", brass, (lx, ly, 0.775), (0.12, 0.12, 0.03), segments=20)
    reb.prim("sphere", "Lamp font", glass, (lx, ly, 0.83), (0.12, 0.12, 0.08), segments=20)
    reb.prim("cyl", "Lamp collar", brass, (lx, ly, 0.88), (0.07, 0.07, 0.03), segments=20)
    reb.prim("cyl", "Lamp chimney", glass, (lx, ly, 0.98), (0.075, 0.075, 0.18), segments=20)
    flame_m = reb.mat_emit("Flame", (1.0, 0.62, 0.22), 40)
    flame = reb.prim("sphere", "Flame", flame_m, (lx, ly, 0.935), (0.018, 0.018, 0.05), segments=10)
    lamp = reb.point("Lamp", (lx, ly, 0.95), 28, (1.0, 0.62, 0.3), 0.02)
    # The chairs: one pulled out, one knocked over.
    chair("Table chair", (3.75, 4.05), -math.pi / 2 + 0.25)
    chair("Fallen chair", (5.45, 4.55), 2.6, tipped=True)
    rugm = reb.cloth("Rug", rug, (4.45, 4.15, 0.004), (2.0, 1.3), cuts=12, lumps=0.006, seed=3)

    # The bunk on the east wall: a rumpled blanket half off it, a pillow, boots.
    bx0, bx1, by0, by1 = 6.05, 6.95, 4.2, 6.0
    solid(reb.prim("cube", "Bunk", dark, ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.22), (bx1 - bx0, by1 - by0, 0.06), bevel=0.01))
    legs("Bunk leg", dark, bx0, bx1, by0, by1, 0.45, 0.07)
    reb.mask(reb.prim("cube", "Mattress", ticking, ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.32), (bx1 - bx0 - 0.04, by1 - by0 - 0.04, 0.14), bevel=0.04))
    reb.mask(reb.prim("cube", "Pillow", ticking, ((bx0 + bx1) / 2, by1 - 0.3, 0.43), (0.55, 0.32, 0.1), bevel=0.04))
    reb.mask(reb.cloth("Blanket", wool, ((bx0 + bx1) / 2 - 0.1, (by0 + by1) / 2 - 0.15, 0.43), (1.05, 1.3), rot=(0, -0.25, 0.1), lumps=0.07, seed=1))
    reb.mask(reb.cloth("Blanket end", wool, (bx0 - 0.08, (by0 + by1) / 2 - 0.1, 0.22), (0.45, 1.1), rot=(0, -1.35, 0), lumps=0.04, seed=2))
    for i, (bxp, byp, rz) in enumerate(((5.75, 5.6, 0.3), (5.62, 5.35, 1.4))):
        reb.prim("cube", "Boot", reb.mat_plain("Leather", (0.08, 0.05, 0.03), 0.6), (bxp, byp, 0.06 if i else 0.15), (0.11, 0.28, 0.12) if i else (0.11, 0.12, 0.3), rot=(0, 0, rz) if not i else (math.pi / 2 * 0.95, 0, rz), bevel=0.02)
    # The item box at the bunk's foot, RE1's own shrunk to a footlocker: the game puts its lid on.
    box_lid = kit.item_box("Item box", (6.5, 3.905), (0, -1), scale=0.65)
    # The typing table in the north-east corner, by the broken window: his
    # typewriter, a report half typed. Where she saves; the game puts the
    # ink ribbons beside it.
    # Not masked: it stands in the corner, where she can't get behind it, and
    # a mask would draw its top over the ribbons the game puts on it.
    solid(kit.table("Typing table", pine, (6.52, 2.24, 0.0), size=(0.85, 0.42, 0.72)), masked=False)
    kit.typewriter("Typewriter", (6.42, 2.24, 0.72))

    # The stove against the west wall, fire behind its grate, the kettle on top.
    sx, sy = 2.42, 4.7
    solid(reb.prim("cube", "Stove", iron, (sx, sy, 0.45), (0.5, 0.6, 0.6), bevel=0.02))
    for dx in (-0.2, 0.2):
        for dy in (-0.24, 0.24):
            reb.mask(reb.prim("cube", "Stove leg", iron, (sx + dx, sy + dy, 0.075), (0.05, 0.05, 0.15)))
    reb.prim("cube", "Stove door", iron, (sx + 0.255, sy, 0.43), (0.02, 0.32, 0.3), bevel=0.01)
    fire_m = reb.mat_emit("Embers", (1.0, 0.35, 0.08), 18)
    for i in range(4):
        reb.prim("cube", "Grate glow", fire_m, (sx + 0.262, sy - 0.09 + i * 0.06, 0.38), (0.004, 0.025, 0.1))
    fire = reb.point("Stove fire", (sx + 0.33, sy, 0.38), 6, (1.0, 0.4, 0.12), 0.05)
    reb.prim("cyl", "Stovepipe", iron, (sx - 0.05, sy, 1.6), (0.15, 0.15, 1.7))
    reb.prim("cyl", "Pipe collar", iron, (sx - 0.05, sy, H - 0.02), (0.24, 0.24, 0.04))
    reb.prim("sphere", "Kettle", enamel, (sx + 0.05, sy + 0.12, 0.8), (0.2, 0.2, 0.15), segments=20)
    reb.prim("cyl", "Kettle spout", enamel, (sx + 0.15, sy + 0.12, 0.83), (0.025, 0.025, 0.12), rot=(0, 1.0, 0))
    # Firewood stacked beside it.
    for i in range(16):
        layer, k = divmod(i, 5)
        reb.mask(reb.wall(reb.prim("cyl", "Firewood", pine, (2.3 + k * 0.1 + (layer % 2) * 0.05, 5.5, 0.06 + layer * 0.11), (0.1 + rng.uniform(-0.02, 0.02), 0.1, 0.45), rot=(math.pi / 2, 0, rng.uniform(-0.1, 0.1)), segments=8)))

    # By the door: pegs with the ranger's hat (his coat is gone), the key board.
    for i, x in enumerate((4.6, 4.85)):
        reb.prim("cyl", "Peg", pine, (x, Y1 - 0.06, 1.75), (0.03, 0.03, 0.12), rot=(math.pi / 2, 0, 0))
    reb.prim("cyl", "Hat brim", felt, (4.6, Y1 - 0.14, 1.8), (0.36, 0.36, 0.015), rot=(0.35, 0, 0), segments=24)
    reb.prim("cyl", "Hat crown", felt, (4.6, Y1 - 0.13, 1.86), (0.19, 0.19, 0.13), rot=(0.35, 0, 0), segments=24)
    reb.prim("cube", "Key board", pine, (3.28, Y1 - 0.015, 1.45), (0.24, 0.02, 0.14), bevel=0.004)
    for i in range(3):
        reb.prim("cyl", "Key hook", brass, (3.2 + i * 0.08, Y1 - 0.04, 1.42), (0.008, 0.008, 0.04), rot=(math.pi / 2, 0, 0))
    # The rifle rack, empty, and an opened box of cartridges below it.
    for z in (1.25, 1.55):
        for x in (5.15, 5.85):
            reb.prim("cube", "Rack bracket", dark, (x, Y1 - 0.05, z), (0.06, 0.1, 0.05))
    reb.prim("cube", "Rack shelf", dark, (5.5, Y1 - 0.09, 0.95), (0.7, 0.18, 0.03))
    reb.prim("cube", "Cartridge box", reb.mat_plain("Cardboard", (0.4, 0.25, 0.1)), (5.4, Y1 - 0.09, 0.995), (0.14, 0.09, 0.06))
    for i in range(6):
        reb.prim("cyl", "Cartridge", brass, (5.55 + i * 0.025, Y1 - 0.08 + rng.uniform(-0.03, 0.03), 0.975), (0.012, 0.012, 0.06), rot=(math.pi / 2, 0, rng.uniform(-0.4, 0.4)))
    # A calendar for July 1998 on the south wall.
    reb.prim("cube", "Calendar", paper, (X0 + 0.005, 3.2, 1.6), (0.006, 0.32, 0.42))
    reb.prim("cube", "Calendar picture", reb.mat_surface("Calendar picture", [(0.0, (0.15, 0.3, 0.2)), (1.0, (0.4, 0.5, 0.6))], scale=12), (X0 + 0.01, 3.2, 1.72), (0.004, 0.28, 0.16))

    # On the floor: glass under the window, a trail of blood to the door, the
    # cases from his rifle, mud from his boots.
    for i in range(14):
        reb.prim("cube", "Floor shard", glass, (rng.uniform(6.55, 6.95), rng.uniform(2.65, 3.5), 0.003), (rng.uniform(0.02, 0.06), rng.uniform(0.02, 0.05), 0.003), rot=(0, 0, rng.uniform(0, 3)))
    a, b = Vector((6.75, 3.1)), Vector((3.95, 5.8))
    for i in range(18):
        t = i / 17
        p = a.lerp(b, t) + Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12)))
        d = rng.uniform(0.02, 0.06) * (1.4 - t)
        reb.prim("cyl", "Blood drop", blood, (p.x, p.y, 0.002), (d, d * rng.uniform(0.7, 1.3), 0.002), segments=10)
    for i in range(5):
        reb.prim("cyl", "Spent case", brass, (rng.uniform(4.3, 5.0), rng.uniform(5.3, 5.85), 0.008), (0.012, 0.012, 0.05), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=8)
    mud = reb.mat_plain("Mud", (0.05, 0.035, 0.02), 0.9)
    for i in range(8):
        reb.prim("cyl", "Muddy print", mud, (4.1 + i * 0.13 + (i % 2) * 0.06, 5.6 - i * 0.17, 0.002), (0.09, 0.22, 0.002), rot=(0, 0, -0.6), segments=12)

    # The curtain at the broken window, stirring in the draught.
    cv, cf = [], []
    cols, rows = 10, 12
    # One curtain, drawn half across from the north side.
    cy0, cy1, cz0, cz1 = EAST_WINDOW[0] - 0.12, EAST_WINDOW[0] + 0.42, EAST_WINDOW[2] - 0.2, EAST_WINDOW[3] + 0.12
    for j in range(rows + 1):
        for i in range(cols + 1):
            pleat = 0.035 * math.sin(i * math.pi / 1.5)
            cv.append((X1 - 0.08 + pleat, cy0 + (cy1 - cy0) * i / cols, cz1 - (cz1 - cz0) * j / rows))
    for j in range(rows):
        for i in range(cols):
            k = j * (cols + 1) + i
            cf.append((k, k + 1, k + cols + 2, k + cols + 1))
    curtain = reb.mesh_object("Curtain", cv, cf, curtain_m)
    rest = [Vector(v) for v in cv]
    reb.prim("cyl", "Curtain rod", iron, (X1 - 0.08, (EAST_WINDOW[0] + EAST_WINDOW[1]) / 2, cz1 + 0.02), (0.02, 0.02, EAST_WINDOW[1] - EAST_WINDOW[0] + 0.3), rot=(math.pi / 2, 0, 0))

    # ---- Light: morning through the windows, sun through the broken one, the lamp, the stove.
    reb.light_for("morning")
    reb.spot("Sun through the east window", (X1 + 2.0, 2.4, 2.4), (5.6, 3.6, 0.0), 1800, (1.0, 0.88, 0.7), 40, 0.5, 0.15)
    reb.spot("Daylight from the north window", ((NORTH_WINDOW[0] + NORTH_WINDOW[1]) / 2, Y0 - 0.6, 1.5), (3.6, 3.5, 0.3), 700, (0.8, 0.88, 1.0), 110, 1.0, 0.8)
    reb.point("Fill", (4.5, 4.2, 2.1), 70, (0.75, 0.8, 0.95), 1.5)
    reb.point("Fill west", (3.0, 5.0, 1.9), 30, (0.95, 0.85, 0.75), 1.0)

    # ---- What moves: one loop of FRAMES frames.
    frng = random.Random(5)
    lamp_flicker = [1.0] + [1.0 + frng.uniform(-0.14, 0.1) for _ in range(FRAMES - 1)]
    fire_flicker = [1.0] + [1.0 + frng.uniform(-0.35, 0.25) for _ in range(FRAMES - 1)]

    def pose(k):
        lamp.data.energy = 28 * lamp_flicker[k]
        reb.emit_strength(flame_m, 40 * lamp_flicker[k])
        flame.scale = (1.0, 1.0, 0.85 + 0.15 * lamp_flicker[k] + (0.1 if k % 3 == 1 else 0))
        fire.data.energy = 6 * fire_flicker[k]
        reb.emit_strength(fire_m, 18 * fire_flicker[k])
        reb.emit_strength(signal, 12 if (k // 4) % 2 == 0 else 0.4)
        phase = 2 * math.pi * k / FRAMES
        for idx, v in enumerate(curtain.data.vertices):
            base = rest[idx]
            down = (cz1 - base.z) / (cz1 - cz0)
            across = (base.y - cy0) / (cy1 - cy0)
            billow = 0.1 * down * (0.6 + 0.4 * math.sin(phase + across * 2.5))
            v.co = (base.x - billow - 0.02 * down * math.sin(2 * phase + across * 6), base.y + 0.03 * down * math.sin(phase + 1.3), base.z + 0.01 * down * math.cos(phase))
        curtain.data.update()

    room_box = {"x0": reb.g(X0), "z0": reb.g(Y0), "x1": reb.g(X1), "z1": reb.g(Y1)}
    door_gap = {"x0": reb.g(DOOR[0]), "z0": reb.g(Y1) - 10, "x1": reb.g(DOOR[1]), "z1": reb.g(Y1 + 0.6)}
    # Where she saves, for the builder; room.c places the lid and the zones.
    saves = {"lid": box_lid}
    reb.export(CAMERAS, OUT, samples=768, extra={"bounds": room_box, "exit": door_gap, "saves": saves}, anim={"frames": FRAMES, "ticks": 3, "set": pose})


build()
