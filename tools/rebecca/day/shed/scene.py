"""The ranger's tool shed, inside. Plank walls, a dusty window, a workbench.

The ranger meant to cut the fallen pine up first: his chainsaw lies in
pieces on the bench, the chain off, a spark plug in the vise. He gave up and
meant to winch it instead. The winch's crank is on the bench. Tools on a
pegboard and a board over the bench, a toolbox and junk under them, cans of
fuel, a bare bulb on a short flex.

Metres, real sizes: the floor is x 1.0-3.6, y 1.0-3.2, the door in the east
wall at y 1.7-2.5 (the yard has the shed at x 2.8-5.4, y 6.6-8.8).

Moving: the bulb, on a short flex up under the roof, holds still. A bad
connection makes it stutter now and then, and its fitting buzzes.
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
FRAMES = 96
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
    # A full ledged and braced door, seated inside a timber jamb.
    # Side infill covers the board generator's uneven opening edges.
    for y in DOOR:
        reb.mask(reb.prim("cube", "Door jamb", bench_m, (X1 - 0.015, y, 1.025), (0.14, 0.11, 2.05), bevel=0.007))
        reb.prim("cube", "Door side infill", planks, (X1 + 0.025, y + (-0.095 if y == DOOR[0] else 0.095), H / 2), (0.035, 0.22, H))
    reb.mask(reb.prim("cube", "Door header", bench_m, (X1 - 0.015, sum(DOOR) / 2, 2.045), (0.14, 0.91, 0.16), bevel=0.008))
    reb.prim("cube", "Over door infill", planks, (X1 + 0.035, sum(DOOR) / 2, H + 0.04), (0.04, 0.9, 0.18))
    reb.prim("cube", "Door shadow backing", iron, (X1 + 0.065, sum(DOOR) / 2, 1.0), (0.02, 0.82, 2.0))
    for i in range(5):
        reb.prim("cube", "Door plank", bench_m, (X1 + 0.025, DOOR[0] + 0.055 + (i + 0.5) * 0.138, 1.005), (0.055, 0.135, 1.95), bevel=0.003)
    for z in (0.25, 1.0, 1.76):
        reb.prim("cube", "Door ledge", planks, (X1 - 0.018, 2.1, z), (0.045, 0.67, 0.105), bevel=0.004)
    kit.rod("Door diagonal brace", bench_m, (X1 - 0.045, 1.82, 0.3), (X1 - 0.045, 2.38, 1.7), 0.045)
    # Two long strap hinges in rusted iron across the planks between the
    # ledges, hung on pintles in the jamb.
    hinge_m = reb.mat_surface("Hinge rust", [(0.0, (0.3, 0.12, 0.04)), (1.0, (0.6, 0.28, 0.1))], scale=25, rough=0.6, bump=0.3)
    for z in (0.5, 1.5):
        reb.mesh_object("Strap hinge", [(X1 - 0.03, 1.73, z - 0.06), (X1 - 0.03, 2.36, z - 0.03), (X1 - 0.03, 2.36, z + 0.03), (X1 - 0.03, 1.73, z + 0.06)], [(0, 1, 2, 3), (3, 2, 1, 0)], hinge_m, smooth=False)
        reb.prim("cyl", "Hinge knuckle", hinge_m, (X1 - 0.035, 1.725, z), (0.06, 0.06, 0.16), segments=12)
        reb.prim("cube", "Pintle plate", hinge_m, (X1 - 0.075, 1.66, z), (0.012, 0.09, 0.2), bevel=0.004)
        for y in (1.82, 1.98, 2.14, 2.27):
            reb.prim("sphere", "Hinge bolt", steel, (X1 - 0.033, y, z), (0.024, 0.024, 0.024), segments=8)
    reb.prim("cube", "Latch plate", iron, (X1 - 0.06, 2.38, 1.02), (0.025, 0.09, 0.17), bevel=0.008)
    kit.rod("Door pull", iron, (X1 - 0.11, 2.38, 0.97), (X1 - 0.11, 2.38, 1.09), 0.014)
    reb.prim("cube", "Threshold", bench_m, (X1, 2.1, 0.012), (0.22, 0.87, 0.024), bevel=0.004)
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
    # ---- The tool walls. Thirty years of a ranger's tools, hung where they
    # fit: the pegboard on the north wall, a second board over the bench.
    handle = reb.mat_wood("Worn tool handles", (0.32, 0.18, 0.07))
    yellow = reb.mat_plain("Yellow enamel", (0.6, 0.42, 0.04), 0.5)
    green = reb.mat_plain("Green enamel", (0.08, 0.2, 0.1), 0.5)
    cord = reb.mat_plain("Orange cord", (0.6, 0.2, 0.03), 0.6)
    tins = [reb.mat_plain(f"Tin label {i}", c, 0.6) for i, c in enumerate([(0.45, 0.32, 0.12), (0.12, 0.2, 0.32), (0.4, 0.08, 0.05), (0.3, 0.3, 0.26)])]

    def wall_rack(name, at, along, out):
        """Hang tools on a wall: P(u, z, d) is the point u along the wall from
        `at`, z up, d out from the board. along and out are unit (x, y)."""
        def P(u, z, d=0.03):
            return (at[0] + along[0] * u + out[0] * d, at[1] + along[1] * u + out[1] * d, z)

        def slab(part, m, u, z, wu, hz, depth=0.02, d=0.03, bevel=0.004):
            size = (abs(along[0]) * wu + abs(out[0]) * depth, abs(along[1]) * wu + abs(out[1]) * depth, hz)
            return reb.prim("cube", f"{name} {part}", m, P(u, z, d), size, bevel=bevel)

        def rod(part, m, u0, z0, u1, z1, r, d=0.03):
            return kit.rod(f"{name} {part}", m, P(u0, z0, d), P(u1, z1, d), r)

        def hammer(u, z, claw=True):
            rod("hammer handle", handle, u, z - 0.2, u, z + 0.1, 0.017)
            slab("hammer head", iron, u + (0.02 if claw else 0), z + 0.12, 0.15, 0.045, 0.04)

        def wrench(u, z, length):
            rod("spanner", steel, u, z - length / 2, u, z + length / 2, 0.011)
            for zz in (z - length / 2, z + length / 2):
                slab("spanner jaw", steel, u, zz, 0.05, 0.035, 0.012)

        def driver(u, z, m):
            slab("screwdriver grip", m, u, z, 0.032, 0.11, 0.032, bevel=0.008)
            rod("screwdriver shaft", steel, u, z - 0.06, u, z - 0.24, 0.005)

        def pliers(u, z, m):
            for sign in (-1, 1):
                rod("pliers grip", m, u + sign * 0.045, z - 0.2, u, z, 0.015)
                rod("pliers jaw", steel, u, z, u + sign * 0.02, z + 0.09, 0.01)

        def chisel(u, z):
            slab("chisel grip", handle, u, z, 0.03, 0.1, 0.03, bevel=0.006)
            slab("chisel blade", steel, u, z - 0.12, 0.022, 0.14, 0.006)

        def handsaw(u, z, length=0.55):
            reb.mesh_object(f"{name} hand saw", [P(u, z - 0.06), P(u + length, z - 0.03), P(u + length, z + 0.05), P(u, z + 0.1)], [(0, 1, 2, 3)], steel, smooth=False)
            slab("saw grip", handle, u - 0.05, z + 0.02, 0.11, 0.16, 0.035, bevel=0.015)

        def clamp(u, z, m):
            slab("clamp back", m, u, z, 0.035, 0.22, 0.03)
            for zz in (z - 0.1, z + 0.1):
                slab("clamp jaw", m, u + 0.06, zz, 0.12, 0.03, 0.03)
            rod("clamp screw", steel, u + 0.11, z - 0.1, u + 0.11, z + 0.07, 0.007)

        def coil(u, z, r, m, turns=5):
            for k in range(turns):
                c = Vector(P(u + k * 0.006, z - k * 0.012, 0.04))
                reb.prim("cyl", f"{name} coil", m, c, (2 * (r - k * 0.008), 2 * (r - k * 0.008), 0.03), rot=(math.pi / 2, 0, math.atan2(out[1], out[0]) - math.pi / 2), segments=20)

        return P, slab, rod, hammer, wrench, driver, pliers, chisel, handsaw, clamp, coil

    # The north pegboard, wall to wall above the clutter.
    reb.prim("cube", "Pegboard", peg, (2.55, Y0 + 0.01, 1.45), (1.8, 0.012, 0.95))
    P, slab, rod, hammer, wrench, driver, pliers, chisel, handsaw, clamp, coil = wall_rack("North rack", (1.65, Y0 + 0.016), (1, 0), (0, 1))
    reb.prim("cube", "Bow saw", steel, (1.98, Y0 + 0.04, 1.72), (0.55, 0.01, 0.03))
    kit.rod("Bow saw frame", orange, (1.72, Y0 + 0.045, 1.72), (1.85, Y0 + 0.045, 1.86), 0.014)
    kit.rod("Bow saw frame", orange, (1.85, Y0 + 0.045, 1.86), (2.12, Y0 + 0.045, 1.86), 0.014)
    kit.rod("Bow saw frame", orange, (2.12, Y0 + 0.045, 1.86), (2.25, Y0 + 0.045, 1.72), 0.014)
    for i, u in enumerate((0.2, 0.36)):
        hammer(u, 1.4 - i * 0.05)
    slab("level", yellow, 1.01, 1.88, 0.62, 0.05, 0.035)
    for i in range(6):
        wrench(0.55 + i * 0.07, 1.5, 0.16 + i * 0.03)
    for i, m in enumerate((red, handle, yellow, red, handle, green, red)):
        driver(1.0 + i * 0.055, 1.62, m)
    pliers(1.45, 1.5, red)
    pliers(1.6, 1.5, green)
    handsaw(0.55, 1.15, 0.5)
    for i in range(4):
        chisel(1.22 + i * 0.05, 1.22)
    clamp(1.45, 1.2, red)
    clamp(1.62, 1.2, red)
    reb.prim("cyl", "Tape measure", yellow, P(1.12, 1.18, 0.04), (0.08, 0.08, 0.04), rot=(math.pi / 2, 0, 0), segments=16)
    rod("crowbar", iron, 0.05, 1.0, 0.07, 1.62, 0.013)
    rod("crowbar claw", iron, 0.07, 1.62, 0.13, 1.68, 0.013)
    coil(1.6, 1.78, 0.12, cord)
    # The board over the bench: hammers, spanners, a hacksaw, files and the
    # winch's own spares.
    reb.prim("cube", "Bench tool board", peg, (X0 + 0.025, 2.05, 1.55), (0.025, 1.75, 0.85))
    P, slab, rod, hammer, wrench, driver, pliers, chisel, handsaw, clamp, coil = wall_rack("Bench rack", (X0 + 0.04, 1.2), (0, 1), (1, 0))
    hammer(0.12, 1.55)
    hammer(0.3, 1.5, claw=False)
    for i in range(5):
        wrench(0.48 + i * 0.065, 1.62, 0.18 + i * 0.035)
    pliers(0.86, 1.6, red)
    pliers(0.98, 1.62, handle)
    for i, m in enumerate((handle, red, yellow, handle, red)):
        driver(1.14 + i * 0.055, 1.66, m)
    handsaw(1.15, 1.3, 0.45)
    for i in range(3):
        rod("file", iron, 0.17 + i * 0.05, 1.12, 0.17 + i * 0.05, 1.27, 0.009)
    rod("hacksaw frame", steel, 0.4, 1.22, 0.85, 1.22, 0.01)
    rod("hacksaw frame", steel, 0.4, 1.22, 0.4, 1.32, 0.01)
    rod("hacksaw frame", steel, 0.85, 1.22, 0.85, 1.32, 0.01)
    slab("hacksaw grip", red, 0.9, 1.29, 0.05, 0.1, 0.03)
    coil(1.55, 1.82, 0.1, rope)
    clamp(1.42, 1.58, green)

    # Sweepings: offcuts by the south wall, sawdust under the bench, nails,
    # torn packaging, a rag dropped and walked on.
    for i in range(16):
        reb.prim("cube", "Timber offcut", bench_m, (rng.uniform(1.82, 3.2), rng.uniform(3.03, 3.16), 0.02 + (i % 3) * 0.025), (rng.uniform(0.1, 0.35), 0.045, 0.025), rot=(0, 0, rng.uniform(-0.7, 0.7)))
    for i in range(8):
        kit.splat("Sawdust", reb.mat_plain("Sawdust", (0.22, 0.16, 0.08), 1), (1.8 + rng.uniform(0, 0.35), 1.3 + i * 0.22, 0), 0.09, stretch=(0.6, 1.4), seed=100 + i)
    for i in range(30):
        reb.prim("cyl", "Dropped nail", steel, (rng.uniform(1.7, 2.6), rng.uniform(1.4, 2.9), 0.004), (0.006, 0.006, 0.06), rot=(math.pi / 2, 0, rng.uniform(0, math.pi)), segments=6)
    kit.papers("Torn packaging", (2.8, 2.87, 0.0), spread=0.25, count=4, seed=17)
    reb.cloth("Trodden rag", reb.mat_plain("Oily rag", (0.12, 0.09, 0.06), 0.95), (2.4, 2.45, 0.01), (0.26, 0.2), rot=(0, 0, 0.6), lumps=0.03, seed=9)
    # Under the pegboard: his toolbox, a crate of junk, paint, a bucket.
    tb = reb.mask(reb.wall(reb.prim("cube", "Toolbox", red, (1.98, Y0 + 0.2, 0.13), (0.5, 0.24, 0.26), bevel=0.012)))
    kit.rod("Toolbox handle", iron, (1.83, Y0 + 0.2, 0.29), (2.13, Y0 + 0.2, 0.29), 0.012)
    reb.prim("cube", "Toolbox lid", red, (1.98, Y0 + 0.08, 0.38), (0.5, 0.02, 0.24), rot=(0.25, 0, 0))
    reb.mask(reb.wall(reb.prim("cube", "Junk crate", bench_m, (2.55, Y0 + 0.22, 0.18), (0.45, 0.32, 0.36), bevel=0.006)))
    for i in range(5):
        kit.rod("Crate junk", [steel, handle, iron, rope, cord][i], (2.4 + i * 0.07, Y0 + 0.15, 0.3), (2.38 + i * 0.08, Y0 + 0.3, 0.58 - (i % 2) * 0.1), 0.014)
    for i, (x, m) in enumerate(((2.95, green), (3.1, tins[1]), (3.02, tins[3]))):
        reb.mask(reb.wall(reb.prim("cyl", "Paint can", m, (x, Y0 + 0.16 + (i // 2) * 0.12, 0.1 + (i // 2) * 0.0), (0.17, 0.17, 0.2), segments=16), "circle"))
        reb.prim("cyl", "Paint can rim", steel, (x, Y0 + 0.16 + (i // 2) * 0.12, 0.205), (0.17, 0.17, 0.012), segments=16)
    reb.mask(reb.wall(reb.prim("cone", "Bucket", reb.mat_metal("Galvanised", (0.32, 0.32, 0.3), 0.5), (3.38, Y0 + 0.22, 0.16), (0.26, 0.26, 0.32), top=1.25, segments=18), "circle"))
    kit.rod("Broom handle", handle, (3.5, 1.12, 0.12), (3.42, 1.28, 1.45), 0.014)
    reb.prim("cube", "Broom head", reb.mat_plain("Bristle", (0.35, 0.28, 0.14), 0.95), (3.5, 1.12, 0.07), (0.08, 0.3, 0.12), rot=(0, 0, 0.4))
    # A worn tyre under the window.
    reb.mask(reb.wall(reb.prim("cyl", "Tyre", reb.mat_plain("Rubber", (0.025, 0.025, 0.025), 0.85), (2.5, Y1 - 0.12, 0.33), (0.62, 0.62, 0.2), rot=(math.pi / 2, 0, 0), segments=24)))
    reb.prim("cyl", "Tyre rim", rust, (2.5, Y1 - 0.13, 0.33), (0.34, 0.34, 0.205), rot=(math.pi / 2, 0, 0), segments=20)
    # Fuel cans, an empty sack, a shovel in the corner.
    for i, (x, y) in enumerate(((3.25, 2.95), (2.95, 3.0))):
        reb.mask(reb.wall(reb.prim("cube", "Fuel can", red, (x, y, 0.22), (0.3, 0.18, 0.44), bevel=0.02)))
        reb.prim("cyl", "Fuel spout", red, (x + 0.08, y, 0.48), (0.04, 0.04, 0.1))
    reb.prim("cube", "Shovel handle", reb.mat_wood("Handle", (0.35, 0.25, 0.12)), (X0 + 0.12, Y1 - 0.12, 0.75), (0.035, 0.035, 1.3), rot=(0.12, -0.08, 0))
    reb.prim("cube", "Shovel blade", rust, (X0 + 0.08, Y1 - 0.08, 0.15), (0.22, 0.03, 0.28))
    reb.cloth("Sack", reb.mat_plain("Burlap", (0.35, 0.28, 0.17), 0.95), (2.0, 3.0, 0.03), (0.6, 0.35), lumps=0.05, seed=5)
    # A cobweb in the north-east corner over the door: its threads run from a
    # hub out to both walls, the corner and the rafters, with a dusty sheet.
    hub = Vector((X1 - 0.15, Y0 + 0.15, H - 0.3))
    anchors = [Vector(p) for p in (
        (X1 - 0.5, Y0, H - 0.08), (X1 - 0.55, Y0, H - 0.4), (X1 - 0.32, Y0, H - 0.62),
        (X1, Y0, H - 0.68),
        (X1, Y0 + 0.32, H - 0.62), (X1, Y0 + 0.55, H - 0.4), (X1, Y0 + 0.5, H - 0.08),
        (X1 - 0.2, Y0 + 0.2, H - 0.06))]
    for end in anchors:
        kit.rod("Web spoke", web, hub, end, 0.003)
    ring = anchors + anchors[:1]
    for t in (0.25, 0.45, 0.65, 0.85):
        for a, b in zip(ring, ring[1:]):
            kit.rod("Web thread", web, hub.lerp(a, t), hub.lerp(b, t), 0.002)
    sheet = reb.mat_plain("Web sheet", (0.55, 0.55, 0.52), 0.9)
    sheet.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.22
    reb.mesh_object("Web sheet", [tuple(hub)] + [tuple(hub.lerp(a, 0.85)) for a in anchors], [(0, i + 1, (i + 1) % len(anchors) + 1) for i in range(len(anchors))], sheet, smooth=False)

    # Light: daylight through the window and the gaps, the bulb on its flex.
    reb.light_for("morning")
    reb.spot("Daylight through the window", (2.5, Y1 + 1.2, 2.2), (2.2, 2.0, 0.0), 260, (1.0, 0.92, 0.78), 50, 0.6, 0.2)
    bulb_m = reb.mat_emit("Bulb", (1.0, 0.75, 0.45), 14)
    reb.prim("cyl", "Flex", reb.mat_plain("Flex", (0.02, 0.02, 0.02), 0.5), (2.3, 2.1, H - 0.07), (0.012, 0.012, 0.14))
    reb.prim("cyl", "Bulb socket", iron, (2.3, 2.1, H - 0.16), (0.045, 0.045, 0.05))
    reb.prim("sphere", "Bulb", bulb_m, (2.3, 2.1, H - 0.22), (0.07, 0.07, 0.1), segments=12)
    lamp = reb.point("Bulb light", (2.3, 2.1, H - 0.24), 28, (1.0, 0.78, 0.5), 0.03)
    reb.point("Fill", (2.3, 2.1, 1.6), 6, (0.7, 0.75, 0.9), 0.8)

    # A bad connection: long steady stretches, then the bulb stutters for a
    # few game frames, nearly out and back, then once more briefly. Frames last 2 game frames,
    # so the loop is 6.4 seconds.
    flick = [1.0] * FRAMES
    for k, level in {37: 0.3, 38: 0.9, 39: 0.15, 40: 0.7, 41: 0.95, 77: 0.45, 78: 0.95}.items():
        flick[k] = level

    def pose(k):
        lamp.data.energy = 28 * flick[k]
        reb.emit_strength(bulb_m, 14 * flick[k])

    # The kit's worn, bitty surfaces, as every kit room has.

    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))

    reb.export(
        CAMERAS,
        OUT,
        samples=512,
        extra={
            "bounds": {"x0": reb.g(X0), "z0": reb.g(Y0), "x1": reb.g(X1), "z1": reb.g(Y1)},
            # Underfoot (sound/ground.ts): the floorboards.
            "ground": "boards",
            "floors": [],
            "exit": {"x0": reb.g(X1) - 10, "z0": reb.g(DOOR[0]), "x1": reb.g(X1 + 0.6), "z1": reb.g(DOOR[1])},
            "crank": G(*CRANK),
        },
        anim={"frames": FRAMES, "ticks": 2, "set": pose, "key": lambda k: flick[k]},
    )


build()
