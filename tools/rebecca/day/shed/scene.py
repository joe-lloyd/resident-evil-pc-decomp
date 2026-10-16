"""The ranger's tool shed, inside. Plank walls, a dusty window, a workbench.

The ranger meant to cut the fallen pine up first: his chainsaw lies in
pieces on the bench, the chain off, a spark plug in the vise. He gave up and
meant to winch it instead. The winch's crank is on the bench. Tools on a
pegboard, cans of fuel, a coil of rope, a bare bulb on its flex.

Metres, real sizes: the floor is x 1.0-3.6, y 1.0-3.2, the door in the east
wall at y 1.7-2.5 (the yard has the shed at x 2.8-5.4, y 6.6-8.8).

Moving: the bulb swings a little on its flex and flickers.
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
X0, X1, Y0, Y1, H = 1.0, 3.6, 1.0, 3.2, 2.15
DOOR = (1.7, 2.5)
FRAMES = 16
CRANK = (1.38, 2.25, 0.93)


def G(x, y, z=0.0):
    return (reb.g(x), -reb.g(z), reb.g(y))


CAMERAS = [
    # 0: high by the door, down at the bench and the pegboard.
    {"from": G(3.45, 3.05, 2.0), "to": G(1.4, 1.7, 0.5), "fov": 190},
    # 1: high over the bench, at the door.
    {"from": G(1.15, 1.15, 2.0), "to": G(3.4, 2.6, 0.6), "fov": 190},
]


def build():
    rng = random.Random(31)
    reb.clear_scene()
    planks = reb.mat_wood("Weathered planks", (0.24, 0.2, 0.15))
    floor_m = reb.mat_wood("Shed floor", (0.13, 0.1, 0.07))
    bench_m = reb.mat_wood("Bench", (0.22, 0.15, 0.09))
    iron = reb.mat_metal("Iron", (0.06, 0.055, 0.05), 0.55)
    steel = reb.mat_metal("Steel", (0.45, 0.45, 0.45), 0.3)
    rust = reb.mat_surface("Rust", [(0.0, (0.15, 0.06, 0.02)), (1.0, (0.3, 0.14, 0.05))], scale=20, rough=0.8)
    orange = reb.mat_plain("Saw orange", (0.55, 0.18, 0.03), 0.45)
    red = reb.mat_plain("Can red", (0.35, 0.04, 0.03), 0.5)
    peg = reb.mat_surface("Pegboard", [(0.0, (0.35, 0.28, 0.18)), (1.0, (0.42, 0.34, 0.22))], scale=40, bump=0.3)
    rope = reb.mat_surface("Rope", [(0.0, (0.35, 0.3, 0.2)), (1.0, (0.5, 0.42, 0.28))], scale=80, bump=0.8)
    glass = reb.mat_surface("Dusty glass", [(0.0, (0.5, 0.52, 0.45)), (1.0, (0.7, 0.7, 0.62))], scale=30, rough=0.6)
    web = reb.mat_plain("Web", (0.6, 0.6, 0.6), 0.9)
    oil = reb.mat_plain("Oil stain", (0.06, 0.05, 0.04), 0.3)

    # Walls of vertical boards with gaps of daylight, a floor of boards, rafters.
    def boards(axis, at, a0, a1, holes=()):
        a = a0
        while a < a1 - 0.01:
            w = rng.choice((0.17, 0.19, 0.21))
            mid = a + w / 2
            if not any(h0 < mid < h1 for h0, h1 in holes):
                if axis == "x":
                    reb.prim("cube", "Board", planks, (mid, at, H / 2), (w - 0.005, 0.025, H + 0.1))
                else:
                    reb.prim("cube", "Board", planks, (at, mid, H / 2), (0.025, w - 0.005, H + 0.1))
            a += w
    boards("x", Y0 - 0.02, X0 - 0.05, X1 + 0.05)
    boards("x", Y1 + 0.02, X0 - 0.05, X1 + 0.05, holes=((2.2, 2.8),))
    boards("y", X0 - 0.02, Y0, Y1)
    boards("y", X1 + 0.02, Y0, Y1, holes=(DOOR,))
    # The door, shut, and the window in the south wall.
    reb.prim("cube", "Door", planks, (X1 + 0.04, (DOOR[0] + DOOR[1]) / 2, 1.0), (0.04, DOOR[1] - DOOR[0], 2.0))
    reb.prim("cube", "Door brace", planks, (X1 + 0.01, (DOOR[0] + DOOR[1]) / 2, 1.0), (0.03, 0.1, 1.5), rot=(0.45, 0, 0))
    reb.prim("cube", "Door latch", iron, (X1 + 0.0, DOOR[0] + 0.1, 1.05), (0.03, 0.12, 0.03))
    reb.prim("cube", "Window", glass, (2.5, Y1 + 0.02, 1.4), (0.6, 0.01, 0.45))
    for z in (1.17, 1.63):
        reb.prim("cube", "Window frame", planks, (2.5, Y1 + 0.01, z), (0.66, 0.04, 0.05))
    for x in (2.2, 2.8):
        reb.prim("cube", "Window frame", planks, (x, Y1 + 0.01, 1.4), (0.05, 0.04, 0.5))
    reb.prim("cube", "Wall under window", planks, (2.5, Y1 + 0.02, 0.58), (0.6, 0.025, 1.17))
    reb.prim("cube", "Wall over window", planks, (2.5, Y1 + 0.02, 1.9), (0.6, 0.025, 0.55))
    y = Y0 - 0.1
    while y < Y1 + 0.1:
        w = rng.choice((0.12, 0.14, 0.16))
        reb.prim("cube", "Floor board", floor_m, ((X0 + X1) / 2, y + w / 2, -0.012), (0.024, w - 0.008, X1 - X0 + 0.3), rot=(0, math.pi / 2, 0))
        y += w
    reb.prim("cube", "Under floor", reb.mat_plain("Void", (0.01, 0.008, 0.006)), ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.04), (X1 - X0 + 1, Y1 - Y0 + 1, 0.02))
    reb.prim("cube", "Roof", reb.mat_surface("Tin underside", [(0.0, (0.1, 0.1, 0.1)), (1.0, (0.2, 0.18, 0.16))], scale=4), ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.08), (X1 - X0 + 0.4, Y1 - Y0 + 0.4, 0.02), rot=(0, -0.06, 0))
    for x in (1.5, 2.3, 3.1):
        reb.prim("cube", "Rafter", planks, (x, (Y0 + Y1) / 2, H - 0.05), (0.08, Y1 - Y0 + 0.2, 0.12))
    for i in range(2):
        reb.prim("cyl", "Oil stain", oil, (rng.uniform(2.0, 3.0), rng.uniform(1.6, 2.6), 0.001), (rng.uniform(0.12, 0.25), rng.uniform(0.1, 0.2), 0.001), segments=16)

    # The workbench along the west wall: the chainsaw in pieces, a vise, the crank.
    bx0, bx1, by0, by1 = X0, X0 + 0.65, Y0 + 0.15, Y1 - 0.15
    reb.mask(reb.wall(reb.prim("cube", "Bench top", bench_m, ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.88), (bx1 - bx0, by1 - by0, 0.06), bevel=0.006)))
    for x in (bx0 + 0.05, bx1 - 0.05):
        for y in (by0 + 0.05, by1 - 0.05):
            reb.mask(reb.prim("cube", "Bench leg", bench_m, (x, y, 0.43), (0.07, 0.07, 0.86)))
    reb.mask(reb.prim("cube", "Bench shelf", bench_m, ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.18), (bx1 - bx0 - 0.04, by1 - by0 - 0.04, 0.03)))
    # The chainsaw: body, bar, the chain coiled beside it, the cover off.
    reb.prim("cube", "Saw body", orange, (1.3, 1.55, 1.0), (0.32, 0.22, 0.2), bevel=0.03)
    reb.prim("cube", "Saw handle", iron, (1.3, 1.55, 1.14), (0.22, 0.04, 0.05), bevel=0.01)
    reb.prim("cube", "Saw bar", steel, (1.33, 1.85, 0.93), (0.07, 0.45, 0.012), rot=(0, 0, 0.1))
    reb.prim("cube", "Saw cover", orange, (1.2, 2.0, 0.92), (0.15, 0.12, 0.03), rot=(0, 0, 0.7))
    for i in range(18):
        a = 2 * math.pi * i / 18
        reb.prim("cube", "Chain link", steel, (1.42 + 0.09 * math.cos(a), 1.3 + 0.07 * math.sin(a), 0.915), (0.02, 0.01, 0.008), rot=(0, 0, a))
    for i in range(6):
        reb.prim("cyl", "Screw", steel, (1.15 + rng.uniform(0, 0.3), 1.65 + rng.uniform(0, 0.25), 0.915), (0.008, 0.008, 0.02), rot=(math.pi / 2, 0, rng.uniform(0, 3)))
    # The vise at the bench's end with a spark plug in its jaws.
    reb.prim("cube", "Vise", iron, (1.3, 2.85, 0.98), (0.14, 0.24, 0.14), bevel=0.01)
    reb.prim("cyl", "Vise screw", steel, (1.3, 3.02, 0.98), (0.025, 0.025, 0.2), rot=(math.pi / 2, 0, 0))
    reb.prim("cyl", "Spark plug", reb.mat_plain("Porcelain", (0.8, 0.78, 0.72), 0.3), (1.3, 2.85, 1.08), (0.022, 0.022, 0.08))
    # A rag, a coffee can of nails, a wrench.
    reb.cloth("Oily rag", reb.mat_plain("Rag", (0.3, 0.25, 0.18), 0.9), (1.25, 2.55, 0.915), (0.3, 0.25), lumps=0.02, seed=2)
    reb.prim("cyl", "Nail can", rust, (1.5, 2.65, 0.98), (0.12, 0.12, 0.14), segments=16)
    reb.prim("cube", "Wrench", steel, (1.48, 2.1, 0.917), (0.25, 0.03, 0.01), rot=(0, 0, -0.4))
    # Pegboard on the north wall with tools, and gaps where some are missing.
    reb.prim("cube", "Pegboard", peg, (2.4, Y0 + 0.01, 1.45), (1.6, 0.012, 0.9))
    reb.prim("cube", "Bow saw", steel, (1.9, Y0 + 0.04, 1.6), (0.6, 0.01, 0.03))
    reb.prim("cube", "Bow saw frame", orange, (1.9, Y0 + 0.04, 1.72), (0.6, 0.02, 0.02))
    reb.prim("cube", "Hammer", iron, (2.4, Y0 + 0.04, 1.62), (0.03, 0.02, 0.3))
    reb.prim("cube", "Hammer head", iron, (2.4, Y0 + 0.04, 1.77), (0.12, 0.03, 0.035))
    for i, x in enumerate((2.6, 2.75, 2.9)):
        reb.prim("cube", f"Spanner {i}", steel, (x, Y0 + 0.04, 1.55), (0.025, 0.01, 0.18 + i * 0.03))
    for x in (2.15, 3.05):
        reb.prim("cube", "Tool outline", reb.mat_plain("Outline", (0.12, 0.1, 0.06)), (x, Y0 + 0.018, 1.45), (0.12, 0.004, 0.45))
    # A coil of rope on a hook, fuel cans, an empty sack, a shovel in the corner.
    for k in range(5):
        a = Vector((3.2, Y0 + 0.08, 1.5))
        reb.prim("cyl", "Rope coil", rope, a, (0.38 - k * 0.02, 0.38 - k * 0.02, 0.035), rot=(math.pi / 2, 0, 0), segments=24)
    for i, (x, y) in enumerate(((3.25, 2.95), (2.95, 3.0))):
        reb.mask(reb.wall(reb.prim("cube", "Fuel can", red, (x, y, 0.22), (0.3, 0.18, 0.44), bevel=0.02)))
        reb.prim("cyl", "Fuel spout", red, (x + 0.08, y, 0.48), (0.04, 0.04, 0.1))
    reb.prim("cube", "Shovel handle", reb.mat_wood("Handle", (0.35, 0.25, 0.12)), (X0 + 0.12, Y1 - 0.12, 0.75), (0.035, 0.035, 1.3), rot=(0.12, -0.08, 0))
    reb.prim("cube", "Shovel blade", rust, (X0 + 0.08, Y1 - 0.08, 0.15), (0.22, 0.03, 0.28))
    reb.cloth("Sack", reb.mat_plain("Burlap", (0.35, 0.28, 0.17), 0.95), (2.0, 3.0, 0.03), (0.6, 0.35), lumps=0.05, seed=5)
    # A web in the corner over the door.
    wv, wf = [], []
    c = Vector((X1 - 0.02, Y0 + 0.02, H - 0.02))
    for i in range(9):
        a = i * math.pi / 16
        d = Vector((-math.cos(a) * 0.35, math.sin(a) * 0.35, -0.3))
        k = len(wv)
        wv += [tuple(c), tuple(c + d), tuple(c + d + Vector((0, 0, 0.004)))]
        wf.append((k, k + 1, k + 2))
    reb.mesh_object("Web", wv, wf, web, smooth=False)

    # Light: daylight through the window and the gaps, the bulb on its flex.
    reb.light_for("morning")
    reb.spot("Daylight through the window", (2.5, Y1 + 1.2, 2.2), (2.2, 2.0, 0.0), 260, (1.0, 0.92, 0.78), 50, 0.6, 0.2)
    bulb_m = reb.mat_emit("Bulb", (1.0, 0.8, 0.55), 30)
    flex = reb.prim("cyl", "Flex", reb.mat_plain("Flex", (0.02, 0.02, 0.02), 0.5), (2.3, 2.1, H - 0.3), (0.012, 0.012, 0.6))
    bulb = reb.prim("sphere", "Bulb", bulb_m, (2.3, 2.1, H - 0.62), (0.07, 0.07, 0.1), segments=12)
    lamp = reb.point("Bulb light", (2.3, 2.1, H - 0.64), 22, (1.0, 0.78, 0.5), 0.03)
    reb.point("Fill", (2.3, 2.1, 1.6), 6, (0.7, 0.75, 0.9), 0.8)

    frng = random.Random(9)
    flick = [1.0] + [1.0 + frng.uniform(-0.12, 0.06) if i % 5 else 0.55 for i in range(1, FRAMES)]

    def pose(k):
        swing = 0.05 * math.sin(2 * math.pi * k / FRAMES)
        drift = 0.02 * math.sin(4 * math.pi * k / FRAMES + 1)
        top = Vector((2.3, 2.1, H))
        end = top + Vector((swing, drift, -0.62))
        flex.location = (top + end) / 2
        flex.rotation_euler = (end - top).to_track_quat("-Z", "Y").to_euler()
        bulb.location = end
        lamp.location = end - Vector((0, 0, 0.02))
        lamp.data.energy = 22 * flick[k]
        reb.emit_strength(bulb_m, 30 * flick[k])

    # The kit's worn, bitty surfaces, as every kit room has.

    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))

    reb.export(
        CAMERAS,
        OUT,
        samples=512,
        extra={
            "bounds": {"x0": reb.g(X0), "z0": reb.g(Y0), "x1": reb.g(X1), "z1": reb.g(Y1)},
            "exit": {"x0": reb.g(X1) - 10, "z0": reb.g(DOOR[0]), "x1": reb.g(X1 + 0.6), "z1": reb.g(DOOR[1])},
            "crank": G(*CRANK),
        },
        anim={"frames": FRAMES, "ticks": 3, "set": pose},
    )


build()
