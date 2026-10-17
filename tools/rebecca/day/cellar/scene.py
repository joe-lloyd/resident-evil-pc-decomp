"""The Spencer mansion's cellar, at night.

What it tells: a long brick vault under the house, stone flags, barrels
on their cradles, coal heaped under its chute. Someone has been down here
lighting candles: they stand on a barrel head and in the wall niches, and
they're still burning. In the middle of the floor lies one of the
footmen, on his back, opened up; one of the household has been feeding on
him. His silver tray and the broken glasses he was carrying are scattered
round him, his blood is spread across the flags in wide smears, and the
feeder's footprints go from him, red, toward the wine store's arch and
fade. The garden stairs come down from the bulkhead in the north wall, the
moon falling down them. Against the west wall stands a heavy oak rack of
preserves, across a low crawl passage that runs off under the house: the
scuffs on the flags show the rack has been moved before. Pushed, it slides
north and the passage shows.

Metres: the floor is x 1.0-9.0, y 1.0-6.0, the walls 2.0 high to a
segmental brick vault, 3.0 at its crown. The garden stairs rise north out
of the north wall at x 6.6-8.0. The wine store's arch is in the east wall
at y 2.0-3.2. The crawl passage is in the west wall at y 5.0-5.8, a metre
high, behind the rack (x 1.0-1.6, y 3.5-5.8; pushed, y 2.6-4.9).

Moving: the candle flames, flies over the body, dust drifting down the
moonlight on the stairs.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
import bpy  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

X0, X1, Y0, Y1 = 1.0, 9.0, 1.0, 6.0
SPRING, CROWN = 2.0, 3.0
STAIRS = (6.6, 8.0)
WINE = (2.0, 3.2)
CRAWL = (5.0, 5.8)
RACK = (1.0, 1.6, 3.5, 5.8)   # across the crawl hole until she pushes it (day/events.ts "push-rack")
PUSHED = -0.9                 # how far north it slides


def courses(name, light, dark, mortar, size, floor=False, rough=0.85):
    """Bricks or flags in courses: on walls along x or y (x + y along, z up), or a floor (x, y)."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = rough
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    comb = nodes.new("ShaderNodeCombineXYZ")
    if floor:
        links.new(sep.outputs["X"], comb.inputs["X"])
        links.new(sep.outputs["Y"], comb.inputs["Y"])
    else:
        add = nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        links.new(sep.outputs["X"], add.inputs[0])
        links.new(sep.outputs["Y"], add.inputs[1])
        links.new(add.outputs[0], comb.inputs["X"])
        links.new(sep.outputs["Z"], comb.inputs["Y"])
    brick = nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = size[0]
    brick.inputs["Row Height"].default_value = size[1]
    brick.inputs["Mortar Size"].default_value = min(size) * 0.12
    brick.inputs["Color1"].default_value = (*light, 1)
    brick.inputs["Color2"].default_value = (*dark, 1)
    brick.inputs["Mortar"].default_value = (*mortar, 1)
    links.new(comb.outputs["Vector"], brick.inputs["Vector"])
    n = reb.noise_tex(nodes, links, 1.5, 8, 0.65)
    g = reb.ramp(nodes, links, n.outputs["Fac"], [(0.3, (0.35, 0.33, 0.3)), (0.7, (1, 1, 1))])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.85
    links.new(brick.outputs["Color"], mix.inputs["A"])
    links.new(g.outputs["Color"], mix.inputs["B"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    reb.bumped(nodes, links, bsdf, brick.outputs["Fac"], -0.5, 0.02)
    return m


def vault_z(y):
    """The vault's soffit height over floor point y: a segmental arch from SPRING at the walls to CROWN."""
    c = (Y0 + Y1) / 2
    half = (Y1 - Y0) / 2
    s = CROWN - SPRING
    r = (half * half + s * s) / (2 * s)
    return CROWN - r + math.sqrt(max(0.0, r * r - (y - c) ** 2))


def barrel(name, m, hoop_m, at, rot=0.0, length=1.0, radius=0.38):
    """A barrel lying on its side along `rot`, on a cradle."""
    x, y, z = at
    parts = [reb.prim("cyl", f"{name} staves", m, (0, 0, 0), (radius * 2, radius * 2, length), segments=18)]
    for t in (-0.42, -0.2, 0.2, 0.42):
        parts.append(reb.prim("cyl", "hoop", hoop_m, (0, 0, t * length), (radius * 2 * (1.04 - abs(t) * 0.12), radius * 2 * (1.04 - abs(t) * 0.12), 0.04), segments=18))
    ob = kit.join(name, parts)
    ob.location = (x, y, z + radius + 0.12)
    ob.rotation_euler = (0, math.pi / 2, rot)
    for dx in (-0.3, 0.3):
        c = reb.prim("cube", f"{name} cradle", mat("dark wood"), (x + dx * math.cos(rot), y + dx * math.sin(rot), z + 0.08), (0.08, radius * 2.0, 0.16), rot=(0, 0, rot))
    return ob


def build():
    rng = random.Random(113)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("concrete")  # flagstones
    room.camera((8.75, 5.75, 2.05), (3.0, 2.2, 0.3), 200, "under the vault, south-east: the footman on the flags, the rack, the garden stairs")
    room.camera((1.25, 1.25, 2.05), (7.2, 5.2, 0.3), 200, "under the vault, north-west: the body, the barrels, the red prints to the wine arch")
    room.camera((8.75, 1.25, 2.05), (2.2, 5.0, 0.4), 200, "under the vault, north-east: the rack and the crawl passage past its end, the coal")
    room.camera((1.25, 5.75, 2.05), (7.6, 1.8, 0.6), 200, "under the vault, south-west: the stairs down from the garden, the wine arch")

    brick = courses("Cellar brick", (0.2, 0.09, 0.06), (0.13, 0.06, 0.045), (0.09, 0.085, 0.075), (0.23, 0.075))
    vault_brick = courses("Vault brick", (0.17, 0.08, 0.055), (0.1, 0.05, 0.04), (0.08, 0.075, 0.068), (0.23, 0.075))
    flags = courses("Flagstones", (0.2, 0.19, 0.17), (0.13, 0.125, 0.115), (0.05, 0.045, 0.04), (0.7, 0.5), floor=True, rough=0.7)
    stone = reb.mat_surface("Step stone", [(0.0, (0.12, 0.12, 0.11)), (1.0, (0.22, 0.21, 0.19))], scale=5, bump=0.6)
    oak = reb.mat_wood("Barrel oak", (0.18, 0.11, 0.06))
    coal = reb.mat_surface("Coal", [(0.0, (0.008, 0.008, 0.008)), (1.0, (0.04, 0.04, 0.045))], scale=20, rough=0.3, bump=1.0)
    livery = reb.mat_surface("Footman's livery", [(0.0, (0.02, 0.02, 0.025)), (0.7, (0.04, 0.04, 0.05)), (1.0, (0.15, 0.01, 0.01))], scale=6, bump=0.2)
    silver = reb.mat_metal("Silver", (0.55, 0.55, 0.55), 0.25)
    gore = reb.mat_surface("Gore", [(0.0, (0.08, 0.005, 0.004)), (0.6, (0.25, 0.03, 0.025)), (1.0, (0.4, 0.15, 0.12))], scale=14, rough=0.3, bump=0.6)

    # ---- The shell: brick walls to the springing, the stairwell, the arch and the crawl hole cut.
    kit.walls(X0, Y0, X1, Y1, SPRING, brick, openings=[
        ("n", STAIRS[0], STAIRS[1], 0.0, SPRING),
        ("e", WINE[0], WINE[1], 0.0, SPRING),
        ("w", CRAWL[0], CRAWL[1], 0.0, 1.0),
    ], thick=0.4, floor=flags)
    # The vault, a mesh over the whole room; brick ribs across it; lunettes at the ends.
    n_x, n_y = 24, 20
    vv, vf = [], []
    for i in range(n_x + 1):
        x = X0 - 0.4 + (X1 - X0 + 0.8) * i / n_x
        for j in range(n_y + 1):
            y = Y0 + (Y1 - Y0) * j / n_y
            vv.append((x, y, vault_z(y)))
    for i in range(n_x):
        for j in range(n_y):
            a = i * (n_y + 1) + j
            vf.append((a, a + n_y + 1, a + n_y + 2, a + 1))
    reb.mesh_object("Vault", vv, vf, vault_brick)
    for x in (3.0, 5.0, 7.0):
        rv, rf = [], []
        for j in range(n_y):
            y0_, y1_ = Y0 + (Y1 - Y0) * j / n_y, Y0 + (Y1 - Y0) * (j + 1) / n_y
            ym = (y0_ + y1_) / 2
            reb.box(rv, rf, (x, ym, vault_z(ym) - 0.06), (0.3, y1_ - y0_ + 0.02, 0.14), 0.0)
        reb.mesh_object("Vault rib", rv, rf, brick)
        reb.prim("cube", "Rib pier", brick, (x, Y0 + 0.08, SPRING / 2), (0.32, 0.16, SPRING))
        reb.prim("cube", "Rib pier", brick, (x, Y1 - 0.08, SPRING / 2), (0.32, 0.16, SPRING))
    for x, flip in ((X0, 1), (X1, -1)):
        lv = [(x, Y0, SPRING)]
        for j in range(n_y + 1):
            y = Y0 + (Y1 - Y0) * j / n_y
            lv.append((x, y, vault_z(y) + 0.01))
        lf = [(0, k + 1, k + 2) for k in range(n_y)]
        reb.mesh_object("Lunette", lv, lf, brick, smooth=False)
    # Wine arch: a round head over the opening, its spandrels filled, a ring of bricks.
    ac, ar, spring_a = (WINE[0] + WINE[1]) / 2, (WINE[1] - WINE[0]) / 2, 1.4
    for side in (-1, 1):
        sv = [(X1 + 0.005, ac + side * ar, SPRING)]
        for k in range(9):
            t = math.pi / 2 * k / 8
            sv.append((X1 + 0.005, ac + side * ar * math.cos(t), spring_a + ar * math.sin(t)))
        reb.mesh_object("Arch spandrel", sv, [tuple(range(len(sv)))], brick, smooth=False)
    for k in range(13):
        t = math.pi * k / 12
        reb.prim("cube", "Arch brick", brick, (X1 - 0.02, ac + ar * math.cos(t) * 1.06, spring_a + ar * math.sin(t) * 1.06), (0.06, 0.08, 0.2), rot=(t - math.pi / 2, 0, 0))
    # Beyond the arch: the wine store's racks in the dark, one candle's glow.
    reb.prim("cube", "Wine beyond floor", flags, (X1 + 2.0, ac, -0.02), (3.6, 3.0, 0.04))
    reb.prim("cube", "Wine beyond wall", brick, (X1 + 3.5, ac, 1.2), (0.2, 3.0, 2.4))
    for k in range(4):
        reb.prim("cube", "Rack beyond", mat("dark wood"), (X1 + 3.25, ac - 1.0 + k * 0.6, 1.0), (0.3, 0.05, 2.0))
    reb.point("Glow beyond the arch", (X1 + 1.8, ac + 0.6, 1.3), 6, (1.0, 0.55, 0.25), 0.1)
    # The crawl passage: a low black hole in the brick, a draught of nothing.
    reb.prim("cube", "Crawl beyond", reb.mat_plain("Crawl dark", (0.005, 0.004, 0.004), 1.0), (X0 - 1.2, sum(CRAWL) / 2, 0.5), (1.8, CRAWL[1] - CRAWL[0] + 0.4, 1.2))
    reb.prim("cube", "Crawl lintel", mat("dark wood"), (X0 - 0.05, sum(CRAWL) / 2, 1.05), (0.5, CRAWL[1] - CRAWL[0] + 0.3, 0.12))
    kit.web("Web in the crawl", (X0 - 0.15, CRAWL[1], 1.0), 0.35, (1, -1))

    # ---- The garden stairs, rising north, the bulkhead open at the top, the moon down them.
    sx0, sx1 = STAIRS
    for k in range(10):
        y = Y0 - 0.3 * (k + 0.5)
        z = 0.26 * (k + 1)
        reb.prim("cube", "Step", stone, ((sx0 + sx1) / 2, y, z / 2), (sx1 - sx0, 0.3, z))
    for x in (sx0 - 0.2, sx1 + 0.2):
        reb.prim("cube", "Stair wall", brick, (x, Y0 - 1.8, 1.8), (0.4, 3.6, 3.6))
    reb.prim("cube", "Bulkhead door, open", reb.mat_plain("Bulkhead iron", (0.04, 0.045, 0.04), 0.6), (sx0 - 0.1, Y0 - 2.9, 3.4), (0.05, 1.2, 1.0), rot=(0, 0.3, 0))
    reb.prim("cube", "Stair head", stone, ((sx0 + sx1) / 2, Y0 - 3.4, 2.5), (sx1 - sx0 + 0.8, 0.6, 0.2))
    kit.splat("Bloody hand on the stair wall", mat("blood"), (sx1 - 0.005, Y0 - 1.0, 1.4), 0.07, rot=(0, math.pi / 2, 0), seed=3)
    for k in range(5):
        kit.splat(f"Drop on the step {k}", mat("blood"), ((sx0 + sx1) / 2 + rng.uniform(-0.3, 0.3), Y0 - 0.3 * (k + 0.5), 0.26 * (k + 1)), 0.04, seed=40 + k)
    moon = reb.spot("Moon down the stairs", ((sx0 + sx1) / 2, Y0 - 4.5, 5.5), ((sx0 + sx1) / 2, Y0 + 1.6, 0.0), 600, (0.55, 0.65, 0.95), 22, 0.4, 0.3)

    # ---- The footman, on his back on the flags, opened; his tray and glasses round him.
    bx, by = 4.2, 3.6
    kit.body("Footman", (bx, by, 0.0), heading=0.35, pose="back", top=livery, legs=livery, seed=11, missing=("l_hand",))
    chest = Vector((bx, by, 0)) + Matrix.Rotation(0.35, 3, "Z") @ Vector((1.1, 0, 0))
    reb.prim("sphere", "Opened chest", gore, (chest.x, chest.y, 0.2), (0.35, 0.28, 0.08), segments=12)
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi)
        kit.rod(f"Pulled out {i}", gore, (chest.x, chest.y, 0.2), (chest.x + math.cos(a) * rng.uniform(0.2, 0.5), chest.y + math.sin(a) * rng.uniform(0.2, 0.5), 0.03), 0.03, 6)
    kit.splat("Pool round him", mat("blood"), (chest.x - 0.1, chest.y, 0.0), 0.75, seed=12, stretch=(1.3, 1.0))
    kit.drag_trail("Smears", mat("old blood"), [(chest.x - 0.6, chest.y + 0.7), (chest.x - 1.3, chest.y + 1.0), (chest.x - 2.0, chest.y + 0.6)], width=0.45, seed=13)
    kit.drag_trail("Smears 2", mat("old blood"), [(chest.x + 0.5, chest.y - 0.6), (chest.x + 1.2, chest.y - 1.2)], width=0.4, seed=14)
    for i in range(5):
        kit.splat(f"Handprint {i}", mat("blood"), (chest.x + rng.uniform(-1.0, 1.0), chest.y + rng.uniform(-0.9, 0.9), 0.0), 0.06, seed=50 + i, lumps=0.6)
    # The feeder's footprints, red, toward the wine arch, fading.
    pts = [Vector((chest.x + 0.6, chest.y - 0.3)), Vector((X1 - 0.6, ac))]
    for i in range(12):
        t = i / 11
        p = pts[0].lerp(pts[1], t) + Vector((0, 0.1 if i % 2 else -0.1))
        ob = kit.splat(f"Red footprint {i}", mat("blood") if i < 6 else mat("old blood"), (p.x, p.y, 0.0), 0.06 * (1 - 0.4 * t), rot=(0, 0, math.atan2(pts[1].y - pts[0].y, pts[1].x - pts[0].x)), seed=60 + i, stretch=(1.8, 0.7), lumps=0.2)
    reb.prim("cyl", "Silver tray", silver, (bx - 0.6, by + 1.2, 0.01), (0.5, 0.5, 0.015), segments=24)
    kit.shards("Broken glasses", (bx - 0.3, by + 0.9, 0.0), spread=0.7, count=24, seed=5)
    reb.prim("cone", "Glass, whole", mat("glass"), (bx - 1.0, by + 0.6, 0.06), (0.07, 0.07, 0.12), rot=(math.pi / 2, 0, 0.4), top=0.3, segments=10)
    reb.prim("cube", "White glove", reb.mat_plain("Glove", (0.55, 0.55, 0.52), 0.8), (bx + 1.3, by + 0.7, 0.01), (0.18, 0.09, 0.02), rot=(0, 0, 1.1))

    # ---- The rack against the west wall, its south end short of the crawl hole; scuffs on the flags.
    rx0, rx1, ry0, ry1 = RACK
    rack_parts = []
    for y in (ry0, (ry0 + ry1) / 2, ry1):
        rack_parts.append(reb.prim("cube", "Rack upright", mat("dark wood"), ((rx0 + rx1) / 2, y, 1.0), (rx1 - rx0, 0.1, 2.0)))
    for z in (0.1, 0.65, 1.2, 1.75):
        rack_parts.append(reb.prim("cube", "Rack shelf", mat("dark wood"), ((rx0 + rx1) / 2, (ry0 + ry1) / 2, z), (rx1 - rx0, ry1 - ry0, 0.05)))
    rack = kit.join("Rack", rack_parts)
    on_rack = [rack]
    reb.wall(reb.prim("cube", "Rack footprint", None, ((rx0 + rx1) / 2, (ry0 + ry1) / 2, 0.5), (rx1 - rx0, ry1 - ry0, 1.0))).hide_render = True
    for z in (0.15, 0.7, 1.25, 1.8):
        y = ry0 + 0.12
        while y < ry1 - 0.1:
            k = rng.random()
            if k < 0.55:
                on_rack.append(reb.prim("cyl", "Preserve jar", reb.mat_glass("Jar", rng.choice(((0.6, 0.25, 0.1), (0.4, 0.45, 0.15), (0.55, 0.1, 0.1)))), ((rx0 + rx1) / 2 + rng.uniform(-0.1, 0.1), y, z + 0.1), (0.12, 0.12, 0.17), segments=10))
            elif k < 0.75:
                on_rack.append(reb.prim("cube", "Crock", reb.mat_plain("Stoneware", (0.35, 0.3, 0.22), 0.5), ((rx0 + rx1) / 2, y, z + 0.12), (0.2, 0.2, 0.22), bevel=0.04))
            y += rng.uniform(0.14, 0.22)
    for i in range(6):
        kit.rod(f"Scuff {i}", reb.mat_plain("Scuff", (0.25, 0.24, 0.22), 0.9), (rx1 + 0.02, ry1 - 0.3 + i * 0.05, 0.002), (rx1 + 0.6 + i * 0.05, ry1 + 0.35 + i * 0.03, 0.002), 0.006, 4)

    def push(done):
        # The footprint stays where the rack stood: the crawl door's zone
        # reaches out past it, so she can still get to the hole.
        for ob in on_rack:
            ob.location.y += PUSHED if done else -PUSHED
    room.state("push-rack", push)

    # ---- Barrels on their cradles along the south wall; coal heaped under its chute, north-east.
    # Clear of the crawl hole's corner, so she can get to it past the rack.
    for i, x in enumerate((3.2, 4.2, 5.6, 6.6)):
        barrel(f"Barrel {i}", oak, mat("iron"), (x, Y1 - 0.55, 0.0), rot=math.pi / 2)
    reb.wall(reb.prim("cube", "Barrels footprint", None, (4.9, Y1 - 0.5, 0.5), (4.2, 1.0, 1.0))).hide_render = True
    barrel("Barrel stacked", oak, mat("iron"), (3.7, Y1 - 0.55, 0.88), rot=math.pi / 2)
    kit.drum("Ale cask, standing", oak, (7.9, Y1 - 0.5, 0.0))
    reb.wall(reb.prim("cube", "Cask footprint", None, (7.9, Y1 - 0.5, 0.5), (0.6, 0.6, 1.0))).hide_render = True
    reb.prim("cube", "Spigot", mat("rust"), (5.6, Y1 - 0.55 - 0.52, 0.5), (0.04, 0.08, 0.04))
    kit.splat("Drip under the spigot", reb.mat_plain("Wine stain", (0.08, 0.01, 0.02), 0.2), (5.6, Y1 - 1.15, 0.0), 0.15, seed=7)
    cv, cf = [], []
    for _ in range(60):
        x = 8.4 + rng.gauss(0, 0.3)
        y = 1.5 + rng.gauss(0, 0.3)
        reb.boulder(rng, (x, y, max(0.0, 0.5 - ((x - 8.6) ** 2 + (y - 1.3) ** 2) * 0.9)), rng.uniform(0.06, 0.12), cv, cf, squash=0.8)
    reb.mesh_object("Coal heap", cv, cf, coal)
    reb.wall(reb.prim("cube", "Coal footprint", None, (8.5, 1.5, 0.3), (1.0, 1.0, 0.6))).hide_render = True
    reb.prim("cube", "Coal chute", mat("iron"), (8.75, 1.15, 1.75), (0.5, 0.3, 0.5), rot=(-0.4, 0, 0))
    reb.prim("cone", "Scuttle", mat("iron"), (7.7, 1.5, 0.15), (0.35, 0.35, 0.3), top=0.6, rot=(0.2, 0, 0), segments=12)
    kit.rod("Shovel", mat("pine"), (7.3, 2.1, 0.02), (8.0, 1.6, 0.4), 0.018, 6)
    reb.prim("cube", "Shovel blade", mat("rust"), (8.1, 1.55, 0.45), (0.22, 0.25, 0.02), rot=(0.6, 0, 0.6))
    # A dust sheet over old furniture; sacks of potatoes.
    reb.wall(kit.box("Old chest", mat("dark wood"), (2.2, 1.6, 0.0), (1.0, 0.55, 0.55)))
    reb.cloth("Dust sheet", mat("sheet"), (2.25, 1.6, 0.85), (1.3, 0.9), cuts=16, lumps=0.12, seed=3)
    reb.prim("cube", "Chair under the sheet", mat("dark wood"), (2.0, 1.6, 0.7), (0.4, 0.4, 0.3))
    for i in range(3):
        reb.prim("cube", f"Potato sack {i}", mat("canvas"), (5.0 + i * 0.55, Y0 + 0.35, 0.25), (0.5, 0.4, 0.5), rot=(0, 0, rng.uniform(-0.2, 0.2)), bevel=0.1)
    reb.wall(reb.prim("cube", "Sacks footprint", None, (5.55, Y0 + 0.35, 0.3), (1.6, 0.5, 0.6))).hide_render = True

    # ---- Candles: on a barrel head, in the niches, on the rack.
    candles = []
    for i, at in enumerate(((3.7, Y1 - 0.55 - 0.02, 1.76), (X0 + 0.08, 1.9, 1.3), (X1 - 0.08, 4.6, 1.3), (rx1 - 0.15, ry0 + 0.15, 1.25), (6.0, 2.0, 0.0), (4.8, 5.2, 0.0))):
        stick, light, flame = kit.candle(f"Candle {i}", at, energy=6 if at[2] > 0 else 4, height=0.14 if i % 2 else 0.1)
        candles.append((light, flame))
        if i == 3:
            # It slides with the rack: the stick, its flame, its wax and its light.
            on_rack.extend(o for o in bpy.data.objects if o.name.startswith("Candle 3"))
    for x, y in ((X0 + 0.04, 1.9), (X1 - 0.04, 4.6)):
        reb.prim("cube", "Niche", reb.mat_plain("Niche dark", (0.02, 0.015, 0.012), 0.9), (x, y, 1.42), (0.06, 0.35, 0.4))
    kit.web("Web", (X0 + 0.05, Y0 + 0.05, SPRING), 0.4, (1, 1))
    kit.web("Web", (X1 - 0.05, Y1 - 0.05, SPRING), 0.4, (-1, -1))

    # ---- Light: the moon down the stairs, the candles, a little bounce under the vault.
    kit.time_light("night")
    reb.point("Candle bounce", (4.5, 3.5, 2.5), 12, (1.0, 0.6, 0.3), 1.0)

    anim = kit.Anim(16)
    for light, flame in candles:
        anim.flicker(light, flame, depth=0.3, dropouts=0)
    anim.flies((chest.x, chest.y, 0.25), count=10, radius=0.4)
    dust_m = reb.mat_emit("Dust", (0.6, 0.65, 0.8), 1.2)
    motes = []
    for i in range(14):
        p = reb.prim("sphere", "Dust mote", dust_m, (0, 0, 0), (0.012, 0.012, 0.012), segments=4)
        motes.append((p, rng.uniform(sx0 + 0.1, sx1 - 0.1), rng.uniform(Y0 - 1.5, Y0 + 1.2), rng.uniform(0.3, 2.6), i / 14))

    def drift(k):
        for p, x, y, z, off in motes:
            t = (k / anim.frames + off) % 1.0
            p.location = (x + 0.05 * math.sin(2 * math.pi * t), y, z - 0.4 * t + 0.4 * off)
    anim.custom(drift)

    # ---- What the game needs.
    room.door("back-garden", (sx0, Y0, sx1, Y0 + 0.6), arrive=((sx0 + sx1) / 2, 1.9), face=(0, 1))
    room.door("wine", (X1 - 0.6, WINE[0], X1, WINE[1]), arrive=(8.1, ac), face=(-1, 0))
    room.door("crawl", (X0, CRAWL[0], X0 + 1.3, CRAWL[1]), arrive=(2.1, sum(CRAWL) / 2), face=(1, 0))
    room.check((chest.x - 1.0, chest.y - 0.8, chest.x + 0.8, chest.y + 0.8), "One of the footmen. Something's been... eating him.\nIt's not long gone.")
    room.check((bx - 1.2, by + 0.6, bx, by + 1.6), "A silver tray. Broken glasses. He was bringing something down.")
    room.check((6.6, 2.2, 8.4, 3.3), "Footprints in his blood. Going that way.")
    room.spot("push-rack", (rx1, ry0, rx1 + 0.6, CRAWL[0]))  # day/events.ts says what she sees and does here
    room.check((7.6, Y0, X1, 2.2), "Coal, under the chute.")
    room.check((2.8, Y1 - 1.1, 7.0, Y1), "Barrels. Someone's lit a candle on one of them.")
    room.entry = "Candles. Someone's down here."
    room.export(anim, samples=128)


build()
