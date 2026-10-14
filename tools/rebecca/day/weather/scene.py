"""The weather station on the summit, afternoon: one room, and a radio that still works.

What it tells: the observer lives up here alone, and he kept his hours to
the minute: every reading in the station log, the barograph still drawing.
This morning the police band said S.T.A.R.S. Alpha would fly up at dusk to
look for Bravo, and he wrote it down. Then the crows came. One hit the east
window so hard it came through and died on his desk among the glass, and
he got up so fast the chair rolled off and the pencil went on the floor.
His tea is still there, cold. He went out with his clipboard to read the
screen and never came back in: his coat is on its hook, his bed is as he
left it, and the door stands open on the summit. The radio is still on,
its dial lit, hissing.

Metres: the floor is x 1.0-4.8, y 1.0-4.0, 2.4 high. The door is in the
south wall at x 2.5-3.4, out onto the summit. A window in the north wall at
x 1.7-2.9 looks along the ridge to the mast, the anemometer just outside
it. A window in the east wall at y 1.8-3.1, over the radio desk, looks at
the instrument screen. The bunk is along the west wall, the instrument
bench under the north window, the stove in the south-west corner.

Moving: the barograph's drum turning, the anemometer's cups spinning
outside, the radio's dial flickering, flies over the dead crow, a crow on
the north sill outside, ducking its head.
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

X0, X1, Y0, Y1, H = 1.0, 4.8, 1.0, 4.0, 2.4
DOOR = (2.5, 3.4)
NWIN = (1.7, 2.9, 1.05, 1.75)   # x0, x1, z0, z1 in the north wall
EWIN = (1.8, 3.1, 1.0, 1.8)     # y0, y1, z0, z1 in the east wall


def outside(x, y):
    """The summit round the hut: flat rock, falling away east."""
    n = noise.noise(Vector((x * 0.15, y * 0.15, 3.0)))
    h = -0.05 + 0.25 * n * min(1.0, max(0.0, (abs(x - 3) + abs(y - 2.5) - 4) / 4))
    if x > 18.0:
        h -= (x - 18.0) * 0.9
    if x < -4.0:
        h -= (-4.0 - x) * 0.9
    return h


def build():
    rng = random.Random(1998)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((1.15, 3.85, 2.2), (4.2, 1.6, 0.75), 200, "high in the south-west corner: the instrument bench, the radio desk under the broken window")
    room.camera((4.65, 1.15, 2.2), (1.7, 3.6, 0.5), 200, "high in the north-east corner: the bunk, the stove, the coat on its hook, the open door")
    room.camera((1.15, 1.15, 2.2), (4.3, 3.7, 0.55), 195, "high in the north-west corner: the radio and the log, the chair rolled off, the door")

    paint = kit.dirtied(kit.boards("Hut panelling", (0.24, 0.27, 0.22), width=0.13, grime=0.5), 0.4)
    lino = reb.mat_surface("Lino", [(0.0, (0.06, 0.05, 0.04)), (0.5, (0.14, 0.11, 0.07)), (1.0, (0.09, 0.07, 0.05))], scale=4, rough=0.5, bump=0.2)
    ceiling = kit.boards("Ceiling boards", (0.3, 0.28, 0.22), width=0.12)
    desk_wood = reb.mat_wood("Desk", (0.2, 0.13, 0.07))
    olive = reb.mat_surface("Radio olive", [(0.0, (0.05, 0.06, 0.035)), (1.0, (0.09, 0.1, 0.06))], scale=10, rough=0.5, bump=0.1)
    brass = reb.mat_metal("Brass", (0.45, 0.33, 0.12), 0.35)
    chart = reb.mat_stripes("Chart paper", [(0.62, 0.6, 0.52), (0.62, 0.6, 0.52), (0.62, 0.6, 0.52), (0.35, 0.3, 0.45)], across=60, axis="Z")
    frame_m = reb.mat_wood("Frame", (0.15, 0.1, 0.06))

    # ---- The shell.
    kit.walls(X0, Y0, X1, Y1, H, paint, openings=[
        ("s", DOOR[0], DOOR[1], 0.0, 2.0),
        ("n", NWIN[0], NWIN[1], NWIN[2], NWIN[3]),
        ("e", EWIN[0], EWIN[1], EWIN[2], EWIN[3]),
    ], floor=lino, ceiling=ceiling)
    for x in (1.9, 2.9, 3.9):
        reb.prim("cube", "Ceiling joist", frame_m, (x, (Y0 + Y1) / 2, H - 0.05), (0.08, Y1 - Y0 + 0.2, 0.1))
    reb.prim("cube", "Skirting", frame_m, ((X0 + X1) / 2, Y0 + 0.01, 0.06), (X1 - X0, 0.02, 0.12))
    reb.prim("cube", "Skirting", frame_m, (X0 + 0.01, (Y0 + Y1) / 2, 0.06), (0.02, Y1 - Y0, 0.12))
    reb.prim("cube", "Skirting", frame_m, (X1 - 0.01, (Y0 + Y1) / 2, 0.06), (0.02, Y1 - Y0, 0.12))
    for x0, x1 in ((NWIN[0], NWIN[1]),):
        reb.prim("cube", "North window glass", reb.mat_glass("Window glass", (0.55, 0.6, 0.6)), ((x0 + x1) / 2, Y0 - 0.06, (NWIN[2] + NWIN[3]) / 2), (x1 - x0, 0.01, NWIN[3] - NWIN[2]))
        reb.prim("cube", "North window bar", frame_m, ((x0 + x1) / 2, Y0 - 0.06, (NWIN[2] + NWIN[3]) / 2), (0.04, 0.04, NWIN[3] - NWIN[2]))
        reb.prim("cube", "North sill", frame_m, ((x0 + x1) / 2, Y0 + 0.03, NWIN[2] - 0.02), (x1 - x0 + 0.1, 0.14, 0.04))
    # The east window, holed: the crow came through it.
    ey0, ey1 = EWIN[0], EWIN[1]
    reb.prim("cube", "East window glass", reb.mat_glass("Window glass", (0.55, 0.6, 0.6)), (X1 + 0.06, (ey0 + ey1) / 2 - 0.3, (EWIN[2] + EWIN[3]) / 2), (0.01, (ey1 - ey0) / 2, EWIN[3] - EWIN[2]))
    reb.prim("cube", "East window bar", frame_m, (X1 + 0.06, (ey0 + ey1) / 2, (EWIN[2] + EWIN[3]) / 2), (0.04, 0.04, EWIN[3] - EWIN[2]))
    reb.prim("cube", "East sill", frame_m, (X1 - 0.03, (ey0 + ey1) / 2, EWIN[2] - 0.02), (0.14, ey1 - ey0 + 0.1, 0.04))
    hub = Vector((X1 + 0.06, (ey0 + ey1) / 2 + 0.32, 1.45))
    kit.splat("Hole in the pane", mat("black"), tuple(hub), 0.1, rot=(0, math.pi / 2, 0), seed=4, lumps=0.8)
    for i in range(9):
        a = 2 * math.pi * i / 9 + rng.uniform(-0.25, 0.25)
        d = Vector((0, math.cos(a), math.sin(a))) * rng.uniform(0.12, 0.3)
        kit.rod("Crack", reb.mat_plain("Crack", (0.75, 0.78, 0.8), 0.3), hub, hub + d, 0.002, 4)
    reb.prim("cube", "Pane left in", reb.mat_glass("Window glass", (0.55, 0.6, 0.6)), (X1 + 0.06, (ey0 + ey1) / 2 + 0.45, EWIN[3] - 0.15), (0.01, 0.25, 0.25), rot=(0.4, 0, 0))
    kit.splat("Blood on the glass", mat("blood"), (X1 + 0.055, (ey0 + ey1) / 2 + 0.2, 1.4), 0.06, rot=(0, math.pi / 2, 0), seed=6, stretch=(0.7, 1.6))

    # ---- The radio desk under the east window.
    desk = kit.table("Radio desk", desk_wood, (X1 - 0.33, 2.6, 0.0), size=(0.6, 1.7, 0.76))
    reb.mask(reb.wall(desk))
    radio = reb.prim("cube", "Radio set", olive, (X1 - 0.25, 2.9, 0.98), (0.36, 0.62, 0.42), bevel=0.012)
    reb.prim("cube", "Radio face", reb.mat_plain("Radio face", (0.03, 0.03, 0.025), 0.4), (X1 - 0.435, 2.9, 1.0), (0.01, 0.58, 0.36))
    dial_m = reb.mat_emit("Radio dial", (1.0, 0.55, 0.15), 8)
    reb.prim("cube", "Radio dial", dial_m, (X1 - 0.442, 2.82, 1.1), (0.006, 0.3, 0.07))
    reb.prim("cube", "Dial needle", mat("red paint"), (X1 - 0.446, 2.88, 1.1), (0.004, 0.006, 0.07))
    for i, y in enumerate((2.68, 2.82, 2.96, 3.1)):
        reb.prim("cyl", f"Radio knob {i}", mat("black"), (X1 - 0.455, y, 0.92), (0.05, 0.05, 0.03), rot=(0, math.pi / 2, 0), segments=12)
    lamp_m = reb.mat_emit("Signal lamp", (0.3, 1.0, 0.3), 6)
    reb.prim("sphere", "Signal lamp", lamp_m, (X1 - 0.445, 3.15, 1.12), (0.02, 0.02, 0.02), segments=8)
    reb.prim("cube", "Speaker grille", mat("iron"), (X1 - 0.443, 3.08, 1.03), (0.004, 0.08, 0.12))
    kit.rod("Mic stand", mat("steel"), (X1 - 0.45, 2.3, 0.76), (X1 - 0.45, 2.3, 0.92), 0.01)
    reb.prim("cube", "Microphone", mat("black"), (X1 - 0.47, 2.3, 0.96), (0.06, 0.05, 0.1), bevel=0.01)
    reb.prim("cube", "Headphones", mat("black"), (X1 - 0.3, 3.35, 0.79), (0.18, 0.06, 0.04), rot=(0, 0, 0.5))
    # The log, open, his tea, the crow dead in the glass.
    reb.prim("cube", "Station log", reb.mat_plain("Log cover", (0.08, 0.1, 0.18), 0.7), (X1 - 0.4, 2.15, 0.765), (0.32, 0.46, 0.02), rot=(0, 0, 0.12))
    reb.prim("cube", "Log pages", mat("paper"), (X1 - 0.4, 2.15, 0.78), (0.3, 0.44, 0.01), rot=(0, 0, 0.12))
    for i in range(9):
        reb.prim("cube", "Log line", reb.mat_plain("Ink", (0.04, 0.05, 0.12), 0.5), (X1 - 0.4 + rng.uniform(-0.03, 0.03), 1.97 + i * 0.042, 0.786), (0.2 + rng.uniform(-0.05, 0.03), 0.004, 0.001), rot=(0, 0, 0.12))
    mug = reb.prim("cyl", "Tea mug", reb.mat_plain("Enamel", (0.55, 0.58, 0.6), 0.35), (X1 - 0.45, 1.85, 0.81), (0.09, 0.09, 0.1), segments=14)
    reb.prim("cyl", "Tea", reb.mat_plain("Cold tea", (0.12, 0.06, 0.02), 0.1), (X1 - 0.45, 1.85, 0.855), (0.08, 0.08, 0.002), segments=14)
    kit.rod("Mug handle", reb.mat_plain("Enamel", (0.55, 0.58, 0.6), 0.35), (X1 - 0.51, 1.85, 0.79), (X1 - 0.51, 1.85, 0.84), 0.01, 6)
    kit.shards("Glass on the desk", (X1 - 0.3, 2.5, 0.77), spread=0.35, count=20, seed=7)
    kit.shards("Glass on the floor", (X1 - 0.6, 2.4, 0.0), spread=0.5, count=14, seed=8)
    dead_crow, dead_wings = kit.crow("Dead crow on the desk", (X1 - 0.25, 2.45, 0.8), heading=2.2, perched=False)
    dead_crow.rotation_euler = (math.pi * 0.9, 0, 2.2)
    dead_crow.location.z = 0.9
    kit.splat("Crow blood", mat("blood"), (X1 - 0.3, 2.5, 0.765), 0.08, seed=9)
    for i in range(5):
        reb.prim("cube", f"Feather {i}", mat("feathers"), (X1 - 0.3 + rng.uniform(-0.5, 0.2), 2.5 + rng.uniform(-0.4, 0.4), 0.004 if i > 1 else 0.77), (0.12, 0.025, 0.003), rot=(0, 0, rng.uniform(0, 3)))
    # The chair rolled back, the pencil on the floor.
    kit.chair("Observer's chair", reb.mat_wood("Chair", (0.22, 0.15, 0.09)), (3.75, 2.75, 0.0), rot=math.pi - 0.6)
    reb.prim("cyl", "Dropped pencil", mat("yellow paint"), (3.55, 2.2, 0.006), (0.012, 0.012, 0.17), rot=(math.pi / 2, 0, 0.7), segments=6)
    # A lamp on the desk, on.
    kit.rod("Desk lamp stem", brass, (X1 - 0.2, 3.35, 0.76), (X1 - 0.2, 3.35, 1.1), 0.012)
    shade_m = reb.mat_plain("Lamp shade", (0.05, 0.18, 0.08), 0.4)
    reb.prim("cone", "Lamp shade", shade_m, (X1 - 0.25, 3.3, 1.12), (0.22, 0.22, 0.12), segments=16, top=0.4)
    desk_lamp = reb.point("Desk lamp", (X1 - 0.25, 3.3, 1.02), 14, (1.0, 0.72, 0.4), 0.04)

    # ---- The instrument bench under the north window: the barograph, the thermograph, the barometer.
    bench = kit.table("Instrument bench", desk_wood, (2.75, Y0 + 0.3, 0.0), size=(1.9, 0.5, 0.82))
    reb.mask(reb.wall(bench))
    # A plan chest in the corner, its drawers of old charts, rolls on top.
    chest = reb.prim("cube", "Plan chest", desk_wood, (X0 + 0.38, Y0 + 0.27, 0.5), (0.74, 0.52, 1.0), bevel=0.01)
    reb.wall(chest)
    for i in range(4):
        reb.prim("cube", f"Chest drawer {i}", frame_m, (X0 + 0.38, Y0 + 0.535, 0.15 + i * 0.23), (0.66, 0.01, 0.18))
        reb.prim("cube", f"Drawer pull {i}", brass, (X0 + 0.38, Y0 + 0.545, 0.2 + i * 0.23), (0.12, 0.012, 0.02))
    reb.prim("cube", "Drawer pulled out", frame_m, (X0 + 0.38, Y0 + 0.7, 0.61), (0.66, 0.35, 0.16))
    kit.papers("Charts in the drawer", (X0 + 0.38, Y0 + 0.7, 0.68), spread=0.15, count=3, seed=11)
    for i in range(4):
        reb.prim("cyl", f"Rolled chart {i}", mat("old paper"), (X0 + 0.38, Y0 + 0.15 + i * 0.09, 1.04), (0.07, 0.07, 0.6), rot=(0, math.pi / 2, rng.uniform(-0.2, 0.2)), segments=10)
    reb.prim("cube", "Barograph base", desk_wood, (2.1, Y0 + 0.3, 0.86), (0.36, 0.2, 0.08))
    drum = reb.prim("cyl", "Barograph drum", chart, (1.98, Y0 + 0.3, 0.98), (0.11, 0.11, 0.14), segments=20)
    tv, tf = [], []
    for i in range(18):
        a0, a1 = 2 * math.pi * i / 24, 2 * math.pi * (i + 1) / 24
        z0 = 0.01 * math.sin(i * 0.9) - 0.01 * i / 18
        z1 = 0.01 * math.sin((i + 1) * 0.9) - 0.01 * (i + 1) / 18
        k = len(tv)
        for a, z in ((a0, z0), (a1, z1)):
            tv.append((math.cos(a) * 0.057, math.sin(a) * 0.057, z - 0.004))
            tv.append((math.cos(a) * 0.057, math.sin(a) * 0.057, z + 0.004))
        tf.append((k, k + 1, k + 3, k + 2))
    trace = reb.mesh_object("Pen trace", tv, tf, reb.mat_plain("Purple ink", (0.25, 0.05, 0.35), 0.5), smooth=False)
    trace.parent = drum
    seam = reb.prim("cube", "Chart clip", brass, (0.057, 0, 0), (0.006, 0.012, 0.14))
    seam.parent = drum
    kit.rod("Pen arm", brass, (2.25, Y0 + 0.3, 0.98), (2.04, Y0 + 0.3, 0.985), 0.004, 4)
    reb.prim("cube", "Aneroid stack", brass, (2.22, Y0 + 0.3, 0.93), (0.1, 0.1, 0.06))
    reb.prim("cube", "Barograph cover", reb.mat_glass("Cover glass", (0.7, 0.75, 0.75)), (2.1, Y0 + 0.3, 1.0), (0.38, 0.22, 0.22))
    reb.prim("cube", "Thermograph", reb.mat_plain("Thermograph green", (0.08, 0.14, 0.08), 0.5), (2.75, Y0 + 0.3, 0.92), (0.3, 0.18, 0.2), bevel=0.01)
    reb.prim("cyl", "Rain gauge", mat("steel"), (3.35, Y0 + 0.3, 1.0), (0.13, 0.13, 0.36), segments=14)
    kit.papers("Charts on the bench", (3.1, Y0 + 0.35, 0.82), spread=0.25, count=4, seed=3)
    reb.prim("cyl", "Barometer", brass, (3.55, Y0 + 0.02, 1.5), (0.26, 0.26, 0.04), rot=(math.pi / 2, 0, 0), segments=20)
    reb.prim("cyl", "Barometer face", mat("paper"), (3.55, Y0 + 0.045, 1.5), (0.22, 0.22, 0.01), rot=(math.pi / 2, 0, 0), segments=20)
    reb.prim("cube", "Barometer needle", mat("black"), (3.55, Y0 + 0.052, 1.52), (0.005, 0.002, 0.09), rot=(0, -0.7, 0))
    kit.text("Barometer word", "STORMY", mat("black"), (3.55, Y0 + 0.052, 1.43), size=0.025, rot=(math.pi / 2, 0, math.pi))
    # Charts pinned up: the day's synoptic chart, a survey map of the mountain.
    reb.prim("cube", "Synoptic chart", mat("old paper"), (4.25, Y0 + 0.015, 1.5), (0.6, 0.006, 0.45), rot=(0, 0.03, 0))
    for i in range(5):
        r = 0.08 + i * 0.04
        pts = [(4.25 + math.cos(2 * math.pi * j / 14) * r * 1.3, Y0 + 0.02, 1.5 + math.sin(2 * math.pi * j / 14) * r * 0.8) for j in range(15)]
        for a, b in zip(pts, pts[1:]):
            kit.rod("Isobar", reb.mat_plain("Pencil", (0.1, 0.1, 0.12), 0.6), a, b, 0.002, 3)
    kit.text("Chart L", "L", mat("red paint"), (4.25, Y0 + 0.022, 1.5), size=0.08, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Survey map", reb.mat_surface("Map", [(0.0, (0.35, 0.4, 0.3)), (0.6, (0.5, 0.5, 0.4)), (1.0, (0.55, 0.52, 0.42))], scale=10, bump=0.02), (X0 + 0.015, 2.0, 1.6), (0.006, 0.8, 0.6))
    kit.text("Map words", "ARKLAY MTNS", mat("black"), (X0 + 0.02, 2.0, 1.85), size=0.05, rot=(math.pi / 2, 0, math.pi / 2))
    kit.splat("Estate on the map", mat("red paint"), (X0 + 0.02, 2.2, 1.45), 0.04, rot=(0, math.pi / 2, 0), seed=2)
    reb.prim("cyl", "Wall clock", mat("black"), (2.95, Y0 + 0.02, 2.05), (0.24, 0.24, 0.04), rot=(math.pi / 2, 0, 0), segments=20)
    reb.prim("cyl", "Clock face", mat("paper"), (2.95, Y0 + 0.045, 2.05), (0.2, 0.2, 0.01), rot=(math.pi / 2, 0, 0), segments=20)
    reb.prim("cube", "Second hand", mat("red paint"), (2.95, Y0 + 0.054, 2.08), (0.004, 0.002, 0.07), rot=(0, 0.4, 0))
    reb.prim("cube", "Hour hand", mat("black"), (2.97, Y0 + 0.053, 2.06), (0.006, 0.002, 0.06), rot=(0, 2.2, 0))

    # ---- West: his bunk, the stove, his kit. South: the coat on its hook, the calendar.
    bed = kit.bunk("Observer's bed", mat("iron"), (X0 + 0.45, 2.45, 0.0), rot=math.pi / 2, levels=1, seed=5)[0]
    bed.scale = (1.0, 1.0, 1.0)
    reb.wall(bed)
    reb.prim("cube", "Pillow", mat("sheet"), (X0 + 0.45, 1.7, 0.55), (0.5, 0.3, 0.1), bevel=0.04)
    reb.prim("cube", "Boot by the bed", mat("rubber"), (X0 + 1.0, 3.2, 0.07), (0.3, 0.12, 0.14), rot=(0, 0, 1.2), bevel=0.03)
    reb.prim("cube", "Boot by the bed", mat("rubber"), (X0 + 1.05, 3.45, 0.06), (0.3, 0.12, 0.12), rot=(1.4, 0, 0.3), bevel=0.03)
    reb.prim("cube", "Kit bag", mat("khaki"), (1.95, 3.72, 0.2), (0.5, 0.35, 0.4), rot=(0, 0, 0.2), bevel=0.08)
    reb.prim("cube", "Shelf", frame_m, (X0 + 0.15, 2.6, 1.6), (0.25, 1.4, 0.03))
    for i in range(6):
        reb.prim("cyl", f"Tin {i}", mat("rust") if i % 2 else mat("steel"), (X0 + 0.15, 2.05 + i * 0.22, 1.68), (0.09, 0.09, 0.13), segments=10)
    reb.prim("cube", "Photo of a woman", reb.mat_plain("Photo", (0.5, 0.45, 0.38), 0.5), (X0 + 0.015, 1.75, 1.0), (0.006, 0.14, 0.1))
    stove = reb.prim("cyl", "Paraffin stove", reb.mat_plain("Stove enamel", (0.2, 0.05, 0.03), 0.4), (X0 + 0.35, Y1 - 0.33, 0.25), (0.4, 0.4, 0.5), segments=16)
    reb.wall(stove, "circle")
    reb.prim("cyl", "Stove top", mat("iron"), (X0 + 0.35, Y1 - 0.33, 0.51), (0.42, 0.42, 0.03), segments=16)
    stove_m = reb.mat_emit("Stove glow", (1.0, 0.35, 0.08), 3)
    reb.prim("cube", "Stove window", stove_m, (X0 + 0.55, Y1 - 0.33, 0.2), (0.01, 0.12, 0.06), rot=(0, 0, 0))
    stove_light = reb.point("Stove glow light", (X0 + 0.7, Y1 - 0.33, 0.2), 1.5, (1.0, 0.35, 0.08), 0.05)
    reb.prim("cyl", "Kettle", mat("steel"), (X0 + 0.35, Y1 - 0.33, 0.62), (0.2, 0.2, 0.18), segments=14)
    reb.prim("cone", "Kettle spout", mat("steel"), (X0 + 0.5, Y1 - 0.33, 0.66), (0.04, 0.04, 0.14), rot=(0, 1.0, 0), segments=8, top=0.4)
    reb.prim("cube", "Coat hooks", frame_m, (1.8, Y1 - 0.02, 1.7), (0.7, 0.03, 0.08))
    reb.cloth("Oilskin coat", reb.mat_plain("Oilskin", (0.35, 0.28, 0.05), 0.45), (1.65, Y1 - 0.1, 1.25), (0.5, 0.85), rot=(math.pi / 2, 0, 0), cuts=12, lumps=0.05, seed=2)
    reb.prim("cube", "Calendar", mat("paper"), (4.25, Y1 - 0.015, 1.45), (0.35, 0.006, 0.45))
    kit.text("Calendar month", "JULY 1998", mat("red paint"), (4.25, Y1 - 0.02, 1.62), size=0.045)
    for d in range(23):
        x = 4.1 + (d % 7) * 0.045
        z = 1.52 - (d // 7) * 0.06
        kit.rod("Day crossed off", mat("black"), (x - 0.015, Y1 - 0.021, z - 0.015), (x + 0.015, Y1 - 0.021, z + 0.015), 0.002, 3)
    kit.drag_trail("Mud from the door", mat("mud"), [(2.95, Y1 - 0.1), (3.2, 3.1), (3.6, 2.6)], width=0.12, seed=4)
    reb.cloth("Rag rug", reb.mat_stripes("Rag rug", [(0.3, 0.08, 0.05), (0.12, 0.12, 0.2), (0.25, 0.22, 0.15)], across=14), (2.1, 2.8, 0.008), (1.1, 0.7), cuts=8, lumps=0.006, seed=6)
    kit.web("Web", (X1 - 0.02, Y1 - 0.02, H - 0.02), 0.25, (-1, -1))

    # ---- Outside: the summit, the anemometer by the north window, the screen past the east, the ridge to the mast.
    reb.terrain("Summit", kit.dirtied(mat("rock"), 0.5, scale=0.5), (-40, 50), (-60, 40), outside, step=1.0)
    reb.prim("cube", "Hut underside", mat("dark wood"), ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.1), (X1 - X0 + 0.4, Y1 - Y0 + 0.4, 0.16))
    reb.prim("cube", "Hut roof", mat("tin"), ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.15), (X1 - X0 + 0.6, Y1 - Y0 + 0.6, 0.08))
    kit.rod("Anemometer pole", mat("steel"), (5.7, 0.5, -0.05), (5.7, 0.5, 5.0), 0.04)
    cups = reb.prim("cyl", "Anemometer hub", mat("steel"), (5.7, 0.5, 2.6), (0.06, 0.06, 0.1), segments=10)
    for i in range(3):
        a = 2 * math.pi * i / 3
        arm = kit.rod("Anemometer arm", mat("steel"), (0, 0, 0), (math.cos(a) * 0.32, math.sin(a) * 0.32, 0), 0.008, 4)
        arm.parent = cups
        cup = reb.prim("sphere", "Anemometer cup", mat("white paint"), (math.cos(a) * 0.32, math.sin(a) * 0.32, 0), (0.12, 0.12, 0.12), segments=10)
        cup.parent = cups
    kit.rod("Anemometer stay", mat("iron"), (5.7, 0.5, 2.5), (7.2, -0.9, -0.05), 0.006, 4)
    sill_crow, _ = kit.crow("Crow on the north sill", (2.5, Y0 - 0.25, NWIN[2] - 0.05), heading=math.pi / 2 + 0.3)
    reb.prim("cube", "Outside sill", frame_m, (2.3, Y0 - 0.2, NWIN[2] - 0.07), (1.3, 0.2, 0.04))
    # The instrument screen out of the east window, its door open.
    for dx in (-0.25, 0.25):
        for dy in (-0.2, 0.2):
            kit.rod("Screen leg", mat("dark wood"), (6.9 + dx, 2.7 + dy, -0.05), (6.9 + dx, 2.7 + dy, 1.1), 0.03)
    reb.prim("cube", "Instrument screen", reb.mat_plain("Screen white", (0.5, 0.5, 0.46), 0.7), (6.9, 2.7, 1.35), (0.65, 0.5, 0.55))
    reb.prim("cube", "Screen door", reb.mat_plain("Screen white", (0.5, 0.5, 0.46), 0.7), (6.98, 3.2, 1.35), (0.5, 0.02, 0.5), rot=(0, 0, 1.0))
    for (x, y, n) in ((9.0, 6.9, 5), (10.6, 3.5, 4), (9.9, 0.6, 6)):
        cv, cf = [], []
        z = outside(x, y) - 0.05
        for i in range(n):
            r = 0.34 - i * 0.04
            reb.boulder(rng, (x, y, z + r * 0.4), r, cv, cf, squash=0.45)
            z += r * 0.8
        reb.mesh_object("Cairn", cv, cf, mat("rock"))
    rv, rf = [], []
    for _ in range(60):
        x, y = rng.uniform(-20, 30), rng.uniform(-40, 30)
        if -1 < x < 7 and -1 < y < 6:
            continue
        reb.boulder(rng, (x, y, outside(x, y)), rng.uniform(0.2, 1.2), rv, rf)
    reb.mesh_object("Boulders", rv, rf, mat("rock"))
    reb.prim("cube", "Head house", kit.boards("Head house boards", (0.2, 0.14, 0.09), width=0.2), (14.8, 11.3, 1.5), (4.0, 3.6, 3.0))
    deer_m = reb.mat_plain("Deer", (0.2, 0.11, 0.06), 0.8)
    reb.prim("sphere", "Deer far off", deer_m, (10.9, 6.1, 0.2), (1.2, 0.45, 0.45))
    mx, my = 9.3, -47.5
    segs = []
    legs = [(mx - 1.2, my - 1.2), (mx + 1.2, my - 1.2), (mx + 1.2, my + 1.2), (mx - 1.2, my + 1.2)]
    for lx, ly in legs:
        kit.rod("Far mast leg", mat("red paint"), (lx, ly, outside(lx, ly)), (mx + (lx - mx) * 0.2, my + (ly - my) * 0.2, 34), 0.1, 4)
    beacon_m = reb.mat_emit("Far beacon", (1.0, 0.05, 0.02), 40)
    reb.prim("sphere", "Far beacon", beacon_m, (mx, my, 34.5), (0.6, 0.6, 0.6), segments=10)
    kit.vista(rng, (3.0, 2.5), (1.0, 0.0), below=-170.0)
    kit.vista(rng, (3.0, 2.5), (0.0, -1.0), below=-170.0, ridges=2)
    kit.vista(rng, (3.0, 2.5), (0.0, 1.0), below=-170.0, ridges=2)

    # ---- Light: the afternoon sun in the south-west, a hard shaft through the door; the desk lamp, the dial.
    kit.time_light("afternoon", sun_heading=235, sun_energy=4.0, sky=((0.52, 0.5, 0.48), (0.2, 0.25, 0.34), 0.6))
    reb.spot("Daylight through the north window", (2.3, Y0 - 3.0, 2.4), (2.4, 2.5, 0.0), 120, (0.75, 0.82, 1.0), 45, 0.8, 0.5)
    reb.spot("Daylight through the east window", (X1 + 3.0, 2.4, 2.2), (2.6, 2.6, 0.2), 90, (0.75, 0.82, 1.0), 45, 0.8, 0.5)
    dial_light = reb.point("Radio dial light", (X1 - 0.55, 2.85, 1.1), 2.5, (1.0, 0.55, 0.15), 0.03)

    anim = kit.Anim(16)
    anim.spin(drum, axis=2, turns=1)
    anim.spin(cups, axis=2, turns=1, symmetry=3)
    anim.flicker(dial_light, dial_m, depth=0.3, dropouts=1)
    anim.blink(reb.point("Signal lamp light", (X1 - 0.47, 3.15, 1.12), 0.2, (0.3, 1.0, 0.3), 0.01), lamp_m, on=(0, 4))
    anim.flicker(stove_light, stove_m, depth=0.2, dropouts=0)
    anim.flies((X1 - 0.3, 2.45, 0.85), count=6, radius=0.2)
    anim.custom(lambda k: setattr(sill_crow, "rotation_euler", (0, 0.45 * max(0.0, math.sin(anim.phase(k, 2))), math.pi / 2 + 0.3)))

    # ---- What the game needs.
    room.door("summit-trail", (DOOR[0], Y1 - 0.4, DOOR[1], Y1), arrive=(2.95, 3.3), face=(0, -1))
    room.check((X1 - 0.75, 2.6, X1, 3.3), "The radio's still on. Through the hiss, a voice on the police band:\n'...Alpha team will fly the Arklay range at dusk... searching for Bravo...'\nThey're coming. Tonight.")
    room.check((X1 - 0.75, 1.8, X1, 2.6), "The station log. Every hour, to the minute.\n0815 POLICE BAND. STARS ALPHA TO FLY AT DUSK. ASKED WIND ON RIDGE.\n0840 CROWS AT THE GLASS AGAIN. HUNDREDS.\nHis tea's beside it, cold. A crow came through the window and died on his desk.")
    room.check((1.6, Y0, 2.5, Y0 + 0.65), "A barograph. The pen is still drawing.\nThe pressure's falling.")
    room.check((X0, 1.8, X0 + 0.9, 3.3), "His bed. Unmade. A photo of a woman by the pillow.")
    room.check((1.2, Y1 - 0.5, 2.3, Y1), "His coat's still on the hook. Wherever he went, he went in a hurry.")
    room.check((3.3, 1.9, 4.1, 2.6), "A pencil, dropped on the floor.")
    room.check((3.9, Y1 - 0.5, X1, Y1), "July. Every day crossed off up to yesterday.")
    room.entry = "A radio. It's on. Someone could hear me."
    room.export(anim)


build()
