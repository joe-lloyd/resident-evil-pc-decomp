"""The mansion's wine store, off the cellar, at night.

What it tells: this is where it started for the footman in the cellar. He
was sent down for a bottle: the cellar book lies open on its lectern at
tonight's page, a pencil tick against a Margaux. Something was waiting in
here. A bottle smashed on the flags, and his blood and the wine pooled
together under the north rack, where a broken bottle still drips into it.
His hands slid down the rack's bottles as he got up, and he went out
through the arch on his knees: the smear runs to the doorway. The racks
are full and dusty, crates of the estate's wine are stencilled SPENCER,
and a candle somebody stuck in a bottle neck still burns on a crate.

Metres: the floor is x 1.0-4.6, y 1.0-4.0, under a low brick vault, 1.9 at
the walls and 2.6 at the crown. The arch back to the cellar is in the west
wall at y 2.0-3.2. Bottle racks line the north, east and south walls.

Moving: the drip into the pool, the candle flame.
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

X0, X1, Y0, Y1 = 1.0, 4.6, 1.0, 4.0
SPRING, CROWN = 1.9, 2.6
ARCH = (2.0, 3.2)


def courses(name, light, dark, mortar, size, floor=False, rough=0.85):
    """Bricks or flags in courses: on walls along x or y, or a floor."""
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
    c, half, s = (Y0 + Y1) / 2, (Y1 - Y0) / 2, CROWN - SPRING
    r = (half * half + s * s) / (2 * s)
    return CROWN - r + math.sqrt(max(0.0, r * r - (y - c) ** 2))


def bottle_rack(rng, name, x0, x1, y0, y1, along, frame_v, frame_f, bottles, caps, top=1.85, cell=0.11, gaps=0.12, skip=()):
    """A bin rack against a wall: a grid of slats, a bottle lying in most
    cells with its neck and foil toward the room. `along` is 'x' or 'y';
    the room side is the far side from the wall (x1 or y1 when the wall is
    at x0 or y0, and the reverse when `face` is negative)."""
    nx = int(((x1 - x0) if along == "x" else (y1 - y0)) / cell)
    nz = int((top - 0.05) / cell)
    depth = (y1 - y0) if along == "x" else (x1 - x0)
    for i in range(nx + 1):
        a = (x0 if along == "x" else y0) + i * cell
        c = (a, (y0 + y1) / 2, top / 2) if along == "x" else ((x0 + x1) / 2, a, top / 2)
        reb.box(frame_v, frame_f, c, (0.015, depth, top) if along == "x" else (depth, 0.015, top))
    for k in range(nz + 1):
        z = 0.05 + k * cell
        c = ((x0 + x1) / 2, (y0 + y1) / 2, z)
        reb.box(frame_v, frame_f, c, (x1 - x0, depth, 0.015) if along == "x" else (depth, y1 - y0, 0.015))
    for i in range(nx):
        for k in range(nz):
            if (i, k) in skip or rng.random() < gaps:
                continue
            a = (x0 if along == "x" else y0) + (i + 0.5) * cell
            z = 0.05 + (k + 0.5) * cell
            bottles.append((a, z))
            caps.append((a, z))
    return nx, nz


def prism(verts, faces, centre, axis, r, length, sides=8):
    """An n-sided prism along `axis` (a unit Vector) from centre: a bottle."""
    axis = Vector(axis)
    u = axis.orthogonal().normalized()
    v = axis.cross(u)
    k = len(verts)
    for end in (0, 1):
        for s in range(sides):
            a = 2 * math.pi * s / sides
            p = Vector(centre) + axis * (length * end) + (u * math.cos(a) + v * math.sin(a)) * r
            verts.append(tuple(p))
    for s in range(sides):
        faces.append((k + s, k + (s + 1) % sides, k + sides + (s + 1) % sides, k + sides + s))
    faces.append(tuple(k + sides + s for s in range(sides)))


def build():
    rng = random.Random(127)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("concrete")  # flagstones
    room.camera((4.15, 1.45, 1.88), (1.5, 3.3, 0.3), 200, "high in the north-east corner: the pool under the rack, the smear out through the arch")
    room.camera((1.15, 3.5, 1.88), (4.2, 1.5, 0.5), 200, "high by the arch: the racks, the drip, the candle in its bottle, the cellar book")

    brick = courses("Wine brick", (0.19, 0.085, 0.055), (0.12, 0.055, 0.04), (0.08, 0.075, 0.068), (0.23, 0.075))
    flags = courses("Flagstones", (0.12, 0.115, 0.1), (0.08, 0.075, 0.068), (0.035, 0.03, 0.026), (0.6, 0.45), floor=True, rough=0.7)
    rack_wood = reb.mat_wood("Rack wood", (0.12, 0.08, 0.05))
    bottle_m = reb.mat_surface("Dusty bottles", [(0.0, (0.01, 0.025, 0.012)), (0.6, (0.02, 0.05, 0.025)), (1.0, (0.12, 0.12, 0.1))], scale=20, rough=0.25, bump=0.05)
    foil = reb.mat_cards("Foil caps", (0.25, 0.02, 0.03), (0.45, 0.32, 0.08))
    wine = reb.mat_plain("Spilled wine", (0.06, 0.004, 0.02), 0.06)
    stencil = mat("black")

    # ---- The shell: brick walls, the flags, the low vault, the arch to the cellar.
    kit.walls(X0, Y0, X1, Y1, SPRING, brick, openings=[("w", ARCH[0], ARCH[1], 0.0, SPRING)], thick=0.4, floor=flags)
    n_x, n_y = 12, 16
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
    reb.mesh_object("Vault", vv, vf, brick)
    for x in (X0, X1):
        lv = [(x, Y0, SPRING)] + [(x, Y0 + (Y1 - Y0) * j / n_y, vault_z(Y0 + (Y1 - Y0) * j / n_y) + 0.01) for j in range(n_y + 1)]
        reb.mesh_object("Lunette", lv, [(0, k + 1, k + 2) for k in range(n_y)], brick, smooth=False)
    ac, ar, sa = (ARCH[0] + ARCH[1]) / 2, (ARCH[1] - ARCH[0]) / 2, 1.3
    for side in (-1, 1):
        sv = [(X0 - 0.005, ac + side * ar, SPRING)]
        for k in range(9):
            t = math.pi / 2 * k / 8
            sv.append((X0 - 0.005, ac + side * ar * math.cos(t), sa + ar * math.sin(t)))
        reb.mesh_object("Arch spandrel", sv, [tuple(range(len(sv)))], brick, smooth=False)
    for k in range(13):
        t = math.pi * k / 12
        reb.prim("cube", "Arch brick", brick, (X0 + 0.02, ac + ar * math.cos(t) * 1.06, sa + ar * math.sin(t) * 1.06), (0.06, 0.08, 0.2), rot=(t - math.pi / 2, 0, 0))
    # The cellar beyond the arch: flags, a barrel, candlelight.
    reb.prim("cube", "Cellar beyond floor", flags, (X0 - 2.0, ac, -0.02), (3.6, 3.0, 0.04))
    reb.prim("cube", "Cellar beyond wall", brick, (X0 - 3.4, ac, 1.2), (0.2, 4.0, 2.4))
    reb.prim("cyl", "Barrel beyond", reb.mat_wood("Barrel oak", (0.18, 0.11, 0.06)), (X0 - 2.6, ac + 0.9, 0.5), (0.76, 0.76, 1.0), rot=(math.pi / 2, 0, 0), segments=16)
    reb.point("Candlelight beyond", (X0 - 1.6, ac - 0.4, 1.2), 10, (1.0, 0.58, 0.28), 0.1)

    # ---- The racks: north, east and south walls, full of dusty bottles.
    fv, ff, north, east, south = [], [], [], [], []
    bottle_rack(rng, "North rack", 1.6, 4.25, Y0, Y0 + 0.36, "x", fv, ff, north, [], skip={(10, 9), (11, 9), (10, 10)})
    bottle_rack(rng, "East rack", X1 - 0.36, X1, 1.4, 3.65, "y", fv, ff, east, [])
    bottle_rack(rng, "South rack", 1.6, 4.25, Y1 - 0.36, Y1, "x", fv, ff, south, [])
    reb.mesh_object("Rack frames", fv, ff, rack_wood)
    for name, (x0, y0, x1, y1) in (("North rack", (1.6, Y0, 4.25, Y0 + 0.36)), ("East rack", (X1 - 0.36, 1.4, X1, Y1)), ("South rack", (1.6, Y1 - 0.36, 4.25, Y1))):
        reb.wall(reb.prim("cube", f"{name} footprint", None, ((x0 + x1) / 2, (y0 + y1) / 2, 0.5), (x1 - x0, y1 - y0, 1.0))).hide_render = True
    bv, bf, cv, cf = [], [], [], []
    for (a, z) in north:
        prism(bv, bf, (a, Y0 + 0.02, z), (0, 1, 0), 0.037, 0.3)
        prism(cv, cf, (a, Y0 + 0.32, z), (0, 1, 0), 0.015, 0.05, 6)
    for (a, z) in south:
        prism(bv, bf, (a, Y1 - 0.02, z), (0, -1, 0), 0.037, 0.3)
        prism(cv, cf, (a, Y1 - 0.32, z), (0, -1, 0), 0.015, 0.05, 6)
    for (a, z) in east:
        prism(bv, bf, (X1 - 0.02, a, z), (-1, 0, 0), 0.037, 0.3)
        prism(cv, cf, (X1 - 0.32, a, z), (-1, 0, 0), 0.015, 0.05, 6)
    reb.mesh_object("Bottles", bv, bf, bottle_m, smooth=False)
    reb.mesh_object("Foil caps", cv, cf, foil, smooth=False)
    # The broken bottle in the north rack, dripping; his hands down the bottles.
    drip_at = (1.6 + 10.5 * 0.11, Y0 + 0.34, 0.05 + 9.5 * 0.11)
    reb.prim("cyl", "Broken bottle in the rack", bottle_m, (drip_at[0], Y0 + 0.2, drip_at[2]), (0.074, 0.25, 0.074), rot=(math.pi / 2, 0, 0), segments=8)
    kit.shards("Glass on the shelf", (drip_at[0], Y0 + 0.3, drip_at[2] - 0.05), spread=0.1, count=6, seed=2, m=mat("bottle"))
    for i in range(4):
        x = 2.3 + i * 0.25
        kit.rod(f"Bloody slide {i}", mat("blood"), (x, Y0 + 0.37, 1.3 - i * 0.1), (x + 0.05, Y0 + 0.37, 0.5 - i * 0.05), 0.012, 4)
        kit.splat(f"Bloody hand {i}", mat("blood"), (x, Y0 + 0.372, 1.3 - i * 0.1), 0.05, rot=(math.pi / 2, 0, 0), seed=10 + i, lumps=0.6)
    # The pool: wine and blood together, the smashed bottle, the trail out on his knees.
    px, py = drip_at[0], Y0 + 0.75
    kit.splat("Wine pool", wine, (px - 0.2, py, 0.0), 0.55, seed=3, stretch=(1.4, 0.9))
    kit.splat("Blood in the wine", mat("blood"), (px - 0.6, py + 0.15, 0.002), 0.4, seed=4, stretch=(1.2, 1.0))
    kit.shards("Smashed bottle", (px - 0.3, py + 0.2, 0.0), spread=0.7, count=30, seed=5, m=mat("bottle"))
    kit.rod("Bottle neck", mat("bottle"), (px + 0.3, py + 0.5, 0.03), (px + 0.45, py + 0.55, 0.035), 0.02, 8)
    kit.drag_trail("Out on his knees", mat("old blood"), [(px - 0.7, py + 0.4), (2.2, 2.3), (1.5, 2.6), (X0, 2.65)], width=0.35, seed=6)
    for i in range(6):
        kit.splat(f"Spatter {i}", mat("blood"), (px - 0.4 + rng.uniform(-0.9, 0.9), py + rng.uniform(-0.2, 0.9), 0.0), 0.04, seed=20 + i)

    # ---- The cellar book on its lectern, crates of the estate's wine, the candle in a bottle.
    lx, ly = 3.85, 3.1
    kit.rod("Lectern post", mat("dark wood"), (lx, ly, 0), (lx, ly, 1.0), 0.04)
    reb.wall(reb.prim("cube", "Lectern footprint", None, (lx, ly, 0.5), (0.3, 0.3, 1.0))).hide_render = True
    reb.prim("cube", "Lectern foot", mat("dark wood"), (lx, ly, 0.03), (0.4, 0.4, 0.06))
    reb.prim("cube", "Lectern top", mat("dark wood"), (lx, ly, 1.05), (0.4, 0.5, 0.04), rot=(0, -0.35, 0))
    reb.prim("cube", "Cellar book", mat("old paper"), (lx - 0.01, ly, 1.08), (0.32, 0.44, 0.02), rot=(0, -0.35, 0))
    reb.prim("cube", "Book spine", reb.mat_plain("Ledger leather", (0.12, 0.03, 0.02), 0.6), (lx - 0.01, ly, 1.075), (0.34, 0.03, 0.025), rot=(0, -0.35, 0))
    for k in range(6):
        reb.prim("cube", "Ledger line", mat("black"), (lx - 0.06 + k * 0.022, ly - 0.1, 1.093 - k * 0.008), (0.004, 0.16, 0.001), rot=(0, -0.35, 0))
    for i, (x, y, z, r) in enumerate(((2.3, Y1 - 0.65, 0.0, 0.05), (2.95, Y1 - 0.62, 0.0, -0.1), (2.6, Y1 - 0.64, 0.34, 0.15))):
        reb.wall(kit.box(f"Wine crate {i}", mat("pine"), (x, y, z), (0.6, 0.4, 0.34), rot=r))
        kit.text(f"Crate stencil {i}", "SPENCER", stencil, (x - 0.21 * math.sin(r), y - 0.205 * math.cos(r), z + 0.17), size=0.07, rot=(math.pi / 2, 0, r))
    stick, candle_light, flame = kit.candle("Candle in a bottle", (3.12, Y1 - 0.62, 0.62), energy=14, height=0.1)
    # Empty crates stacked in the north-west corner, waiting to go back.
    for i in range(3):
        kit.box(f"Empty crate {i}", mat("pine"), (1.3, 1.2, i * 0.3), (0.55, 0.38, 0.3), rot=0.08 * i)
    reb.wall(reb.prim("cube", "Empty crates footprint", None, (1.3, 1.2, 0.5), (0.6, 0.45, 1.0))).hide_render = True
    reb.prim("cyl", "Candle bottle", mat("bottle"), (3.12, Y1 - 0.62, 0.48), (0.08, 0.08, 0.28), segments=10)
    kit.rod("Wax run", reb.mat_plain("Wax", (0.62, 0.58, 0.48), 0.5), (3.15, Y1 - 0.62, 0.62), (3.17, Y1 - 0.6, 0.42), 0.01, 4)
    reb.prim("cube", "Corkscrew", mat("steel"), (2.4, Y1 - 0.62, 0.69), (0.1, 0.02, 0.02), rot=(0, 0, 0.6))
    kit.web("Web", (X1 - 0.05, Y0 + 0.05, SPRING), 0.35, (-1, 1))
    kit.web("Web", (X1 - 0.05, Y1 - 0.05, SPRING), 0.3, (-1, -1))
    kit.web("Web over the racks", (1.62, Y1 - 0.05, SPRING), 0.3, (1, -1))

    # ---- Light: the candle, the cellar's glow through the arch.
    kit.time_light("night")
    reb.point("Glow under the vault", (2.8, 2.5, 2.2), 8, (1.0, 0.6, 0.3), 0.8)

    anim = kit.Anim(16)
    anim.flicker(candle_light, flame, depth=0.3, dropouts=1)
    anim.drip((drip_at[0], Y0 + 0.36, drip_at[2] - 0.04), fall=drip_at[2] - 0.05, size=0.014, m=wine)
    anim.flies((px - 0.5, py + 0.1, 0.05), count=5, radius=0.25)

    # ---- What the game needs.
    room.door("cellar", (X0, ARCH[0], X0 + 0.6, ARCH[1]), arrive=(1.9, ac), face=(1, 0))
    # The handprints first: the pool's zone takes in theirs, and the first zone in the table wins.
    room.check((2.1, Y0 + 0.36, 3.0, Y0 + 0.9), "Bloody handprints down the bottles. He tried to get up.")
    room.check((px - 1.1, Y0 + 0.36, px + 0.5, py + 0.7), "Wine and blood, pooled together. A bottle smashed.\nThis is where it got him.")
    room.check((lx - 0.5, ly - 0.4, lx + 0.4, ly + 0.4), "The cellar book. Tonight's page: one Margaux, ticked.\nHe came down for a bottle.")
    room.check((2.0, Y1 - 1.0, 3.3, Y1 - 0.36), "Crates of wine. SPENCER, stencilled on the side.\nSomeone stuck a candle in a bottle here.")
    room.check((X1 - 0.8, 1.4, X1 - 0.36, 2.2), "Dusty bottles. Years of them.")
    room.entry = "The wine store. It smells of wine. And something else."
    room.export(anim, samples=128)


build()
