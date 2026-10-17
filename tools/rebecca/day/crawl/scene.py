"""The crawl passage under the mansion's floorboards, at night.

What it tells: behind the cellar's rack a service passage runs under the
house, dug out of the clay between the brick sleeper walls, the joists and
the boards of the ground floor right over her head. Nobody comes here but
the plumber and the rats: lead pipes and an old iron main run along the
walls, cobwebs hang thick between the joists, rat droppings and gnawed
paper are everywhere, a tin of rat poison lies spilled. Somebody hid down
here once and left a blanket and a candle stub. Light falls in thin bars
through the gaps between the boards from the rooms above, and now and
then something crosses the floor up there and the bars go out and come
back. At the far end of the north leg a short wooden ladder goes up to a
square hatch in the boards, light round its edges: the room above it is a
quiet one.

Metres: the floor is x 1.0-8.0, y 1.0-6.0, but the passage is an L: the
south leg y 4.4-6.0 from the cellar hole at the west end (x 1.0) east to
x 8.0, then the north leg x 6.4-8.0 up to y 1.0. The rest is clay and
brick. The boards are 1.9 above the clay floor, on joists along the legs.
The hatch is in the boards over x 6.8-7.6, y 1.2-2.0.

Moving: the bars of light through the boards as someone walks across
above, dust drifting in them, a cobweb stirring in the draught.
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
from mathutils import Vector  # noqa: E402

X0, X1, Y0, Y1 = 1.0, 8.0, 1.0, 6.0
SOUTH = (4.4, 6.0)          # y of the south leg
NORTH = (6.4, 8.0)          # x of the north leg
BOARDS = 1.9                # underside of the floorboards
HATCH = (6.8, 7.6, 1.2, 2.0)
CELLAR_HOLE = (5.0, 5.8)    # y of the hole back to the cellar, in the west end


def courses(name, light, dark, mortar, size, rough=0.85):
    """Bricks in courses on walls along x or y."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = rough
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    add = nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    links.new(sep.outputs["X"], add.inputs[0])
    links.new(sep.outputs["Y"], add.inputs[1])
    comb = nodes.new("ShaderNodeCombineXYZ")
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


def web_sheet(rng, verts, faces, a, b, sag, strands=14):
    """Cobweb strung between two points high up, sagging: threads in one mesh."""
    a, b = Vector(a), Vector(b)
    for i in range(strands):
        t0, t1 = rng.random(), rng.random()
        p = a.lerp(b, t0) + Vector((0, 0, -sag * rng.random()))
        q = a.lerp(b, t1) + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), -sag * rng.uniform(0.5, 1.4)))
        n = (q - p).cross(Vector((0.2, 0.3, 0.9))).normalized() * 0.002
        k = len(verts)
        verts.extend([tuple(p - n), tuple(p + n), tuple(q + n), tuple(q - n)])
        faces.append((k, k + 1, k + 2, k + 3))


def build():
    rng = random.Random(131)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("earth")  # clay
    room.camera((1.15, 4.78, 1.5), (7.5, 5.6, 0.2), 195, "from the cellar hole: the south leg, bars of light across the clay, the pipes")
    room.camera((7.85, 4.78, 1.5), (1.5, 5.4, 0.3), 195, "from the corner: back west along the south leg to the cellar's glow")
    room.camera((6.75, 4.3, 1.45), (7.3, 1.4, 1.55), 200, "from the foot of the north leg: up it to the ladder and the hatch")

    brick = courses("Sleeper brick", (0.16, 0.075, 0.05), (0.1, 0.05, 0.035), (0.07, 0.065, 0.06), (0.23, 0.075))
    clay = reb.mat_surface("Clay floor", [(0.0, (0.06, 0.045, 0.03)), (0.6, (0.11, 0.08, 0.05)), (1.0, (0.14, 0.1, 0.06))], scale=4, bump=0.7)
    board_m = kit.boards("Underside of the boards", (0.13, 0.09, 0.055), width=0.14, grime=0.8)
    joist_m = reb.mat_wood("Joists", (0.05, 0.035, 0.022))
    lead = reb.mat_metal("Lead pipe", (0.18, 0.18, 0.2), 0.6)
    room_light = (1.0, 0.72, 0.42)

    # ---- The clay, the brick sleeper walls round the L, the earth bank inside it.
    reb.prim("cube", "Clay", clay, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.05), (X1 - X0 + 1.0, Y1 - Y0 + 1.0, 0.1))
    walls = [
        (X0 - 0.2, SOUTH[1] + 0.2, X1 + 0.2, SOUTH[1]),          # south wall, along the whole south leg
        (X1 + 0.2, Y0 - 0.2, X1, SOUTH[1] + 0.2),                # east wall, the outside of both legs
        (X0 - 0.2, SOUTH[0], NORTH[0], SOUTH[0] - 0.2),          # north wall of the south leg
        (NORTH[0] - 0.2, Y0 - 0.2, NORTH[0], SOUTH[0]),          # west wall of the north leg
        (NORTH[0] - 0.2, Y0 - 0.2, X1 + 0.2, Y0),                # north end
    ]
    for x0, y0, x1, y1 in walls:
        a, b = sorted((x0, x1)), sorted((y0, y1))
        w = reb.prim("cube", "Sleeper wall", brick, ((a[0] + a[1]) / 2, (b[0] + b[1]) / 2, BOARDS / 2), (a[1] - a[0], b[1] - b[0], BOARDS))
        reb.wall(w)
    # The clay inside the L, solid.
    reb.wall(reb.prim("cube", "Clay inside the L", None, ((X0 + NORTH[0]) / 2 - 0.1, (Y0 + SOUTH[0]) / 2 - 0.1, 0.5), (NORTH[0] - X0 + 0.2, SOUTH[0] - Y0 + 0.2, 1.0))).hide_render = True
    # The west end: brick with the hole back to the cellar, candlelight beyond it.
    for y0, y1 in ((SOUTH[0], CELLAR_HOLE[0]), (CELLAR_HOLE[1], SOUTH[1])):
        reb.wall(reb.prim("cube", "West end", brick, (X0 - 0.1, (y0 + y1) / 2, BOARDS / 2), (0.2, y1 - y0, BOARDS)))
    reb.prim("cube", "Over the hole", brick, (X0 - 0.1, sum(CELLAR_HOLE) / 2, (1.0 + BOARDS) / 2), (0.2, CELLAR_HOLE[1] - CELLAR_HOLE[0], BOARDS - 1.0))
    reb.prim("cube", "Cellar beyond", courses("Cellar brick", (0.2, 0.09, 0.06), (0.13, 0.06, 0.045), (0.09, 0.085, 0.075), (0.23, 0.075)), (X0 - 2.0, sum(CELLAR_HOLE) / 2, 1.0), (0.2, 2.0, 2.0))
    reb.prim("cube", "Cellar beyond floor", clay, (X0 - 1.0, sum(CELLAR_HOLE) / 2, -0.02), (2.0, 2.0, 0.04))
    reb.prim("cube", "Rack's end, beyond", mat("dark wood"), (X0 - 0.6, CELLAR_HOLE[0] - 0.3, 1.0), (0.6, 0.1, 2.0))
    reb.point("Cellar candlelight", (X0 - 1.2, sum(CELLAR_HOLE) / 2, 0.8), 30, (1.0, 0.55, 0.25), 0.1)
    # Arched vents in the sleeper walls, black.
    for x in (2.5, 4.5):
        reb.prim("cube", "Vent", mat("black"), (x, SOUTH[0] + 0.005, 0.9), (0.4, 0.01, 0.35))
        reb.prim("cube", "Vent", mat("black"), (x + 0.6, SOUTH[1] - 0.005, 0.9), (0.4, 0.01, 0.35))

    # ---- Overhead: joists along each leg and the boards across them, with gaps; the hatch.
    jv, jf = [], []
    for y in (4.55, 5.0, 5.45, 5.9):
        reb.box(jv, jf, ((X0 + X1) / 2, y, BOARDS - 0.1), (X1 - X0 + 0.4, 0.07, 0.2))
    for x in (6.55, 7.05, 7.55):
        reb.box(jv, jf, (x, (Y0 + SOUTH[0]) / 2, BOARDS - 0.1), (0.07, SOUTH[0] - Y0 + 0.4, 0.2))
    reb.mesh_object("Joists", jv, jf, joist_m)
    bv, bf = [], []
    x = X0 - 0.2
    gaps = []
    while x < X1 + 0.2:
        w = rng.choice((0.13, 0.15, 0.17))
        reb.box(bv, bf, (x + w / 2, (SOUTH[0] + SOUTH[1]) / 2, BOARDS + 0.012), (w - 0.022, SOUTH[1] - SOUTH[0] + 0.4, 0.024))
        gaps.append(("x", x + w))
        x += w
    y = Y0 - 0.2
    while y < SOUTH[0]:
        w = rng.choice((0.13, 0.15, 0.17))
        if not (HATCH[2] - 0.02 < y + w / 2 < HATCH[3] + 0.02):
            reb.box(bv, bf, ((NORTH[0] + NORTH[1]) / 2, y + w / 2, BOARDS + 0.012), (NORTH[1] - NORTH[0] + 0.4, w - 0.022, 0.024))
        else:
            for x0, x1 in ((NORTH[0] - 0.2, HATCH[0]), (HATCH[1], NORTH[1] + 0.2)):
                reb.box(bv, bf, ((x0 + x1) / 2, y + w / 2, BOARDS + 0.012), (x1 - x0, w - 0.012, 0.024))
        y += w
    reb.mesh_object("Floorboards above", bv, bf, board_m)
    # Over the boards: the rooms' floor, lit; carpet on it so the light comes up warm.
    reb.prim("cube", "Room above", reb.mat_plain("Carpet above", (0.25, 0.08, 0.06), 0.9), ((X0 + X1) / 2, (Y0 + Y1) / 2, BOARDS + 2.6), (X1 - X0 + 2.0, Y1 - Y0 + 2.0, 0.1))
    # The hatch: a square of boards, light leaking round it; a ladder up to it.
    hx0, hx1, hy0, hy1 = HATCH
    reb.prim("cube", "Hatch", kit.boards("Hatch boards", (0.15, 0.1, 0.06), width=0.12, grime=0.6), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, BOARDS + 0.03), (hx1 - hx0 - 0.04, hy1 - hy0 - 0.04, 0.04))
    for x in (hx0 + 0.15, hx1 - 0.15):
        reb.prim("cube", "Hatch batten", mat("dark wood"), (x, (hy0 + hy1) / 2, BOARDS - 0.0), (0.06, hy1 - hy0 - 0.1, 0.04))
    reb.prim("cube", "Hatch ring", mat("iron"), ((hx0 + hx1) / 2, hy1 - 0.15, BOARDS - 0.03), (0.08, 0.02, 0.06))
    leak_m = reb.mat_emit("Light round the hatch", (1.0, 0.75, 0.45), 6)
    for (cx, cy, sx, sy) in (((hx0 + hx1) / 2, hy0 + 0.01, hx1 - hx0, 0.012), ((hx0 + hx1) / 2, hy1 - 0.01, hx1 - hx0, 0.012), (hx0 + 0.01, (hy0 + hy1) / 2, 0.012, hy1 - hy0), (hx1 - 0.01, (hy0 + hy1) / 2, 0.012, hy1 - hy0)):
        reb.prim("cube", "Hatch leak", leak_m, (cx, cy, BOARDS + 0.06), (sx, sy, 0.005))
        reb.prim("cube", "Hatch edge, lit", leak_m, (cx, cy, BOARDS - 0.004), (max(sx, 0.025), max(sy, 0.025), 0.004))
    for x in (hx0 + 0.1, hx1 - 0.1):
        kit.rod("Ladder stile", mat("pine"), (x, hy1 + 0.55, 0.0), (x, hy1 - 0.05, BOARDS - 0.02), 0.03, 6)
    for k in range(5):
        t = (k + 1) / 6
        kit.rod("Ladder rung", mat("pine"), (hx0 + 0.1, hy1 + 0.55 - 0.6 * t, BOARDS * t), (hx1 - 0.1, hy1 + 0.55 - 0.6 * t, BOARDS * t), 0.022, 6)
    reb.wall(reb.prim("cube", "Ladder footprint", None, ((hx0 + hx1) / 2, hy1 + 0.25, 0.5), (hx1 - hx0, 0.6, 1.0))).hide_render = True
    kit.splat("Scuffed clay under the ladder", reb.mat_plain("Trodden clay", (0.15, 0.11, 0.07), 0.6), ((hx0 + hx1) / 2, hy1 + 0.7, 0.0), 0.35, seed=4)

    # ---- Pipes along the walls; the old iron main; a dripping joint.
    kit.rod("Lead pipe", lead, (X0, SOUTH[1] - 0.12, 1.45), (X1 - 0.12, SOUTH[1] - 0.12, 1.45), 0.035, 10)
    kit.rod("Lead pipe, up", lead, (X1 - 0.12, SOUTH[1] - 0.12, 1.45), (X1 - 0.12, Y0 + 0.12, 1.45), 0.035, 10)
    kit.rod("Lead pipe, riser", lead, (X1 - 0.12, Y0 + 0.12, 1.45), (X1 - 0.12, Y0 + 0.12, BOARDS + 0.1), 0.035, 10)
    kit.rod("Iron main", mat("rust"), (X0, SOUTH[0] + 0.18, 0.35), (NORTH[0] + 0.18, SOUTH[0] + 0.18, 0.35), 0.08, 12)
    kit.rod("Iron main, north", mat("rust"), (NORTH[0] + 0.18, SOUTH[0] + 0.18, 0.35), (NORTH[0] + 0.18, Y0 + 0.2, 0.35), 0.08, 12)
    for x in (2.2, 3.6, 5.0):
        reb.prim("cube", "Pipe clip", mat("iron"), (x, SOUTH[1] - 0.06, 1.45), (0.04, 0.14, 0.1))
        reb.prim("cyl", "Main collar", mat("rust"), (x + 0.4, SOUTH[0] + 0.18, 0.35), (0.2, 0.2, 0.08), rot=(0, math.pi / 2, 0), segments=12)
    kit.splat("Damp under the joint", reb.mat_plain("Wet clay", (0.03, 0.025, 0.02), 0.2), (4.2, SOUTH[1] - 0.35, 0.0), 0.3, seed=7)
    kit.rod("Wire", mat("black"), (X0, SOUTH[0] + 0.05, BOARDS - 0.25), (X1, SOUTH[0] + 0.05, BOARDS - 0.25), 0.006, 4)

    # ---- Cobwebs between the joists and in the corners; rat droppings, gnawed paper, the poison tin.
    wv, wf = [], []
    for _ in range(22):
        x = rng.uniform(X0 + 1.6, X1 - 1.4)
        a = (x, rng.choice((4.55, 5.0, 5.45)), BOARDS - 0.2)
        b = (x + rng.uniform(-0.3, 0.3), a[1] + 0.45, BOARDS - 0.2)
        web_sheet(rng, wv, wf, a, b, rng.uniform(0.1, 0.4))
    webs = reb.mesh_object("Cobwebs", wv, wf, mat("web"), smooth=False)
    for c, f in (((X1 - 0.02, SOUTH[1] - 0.02, BOARDS - 0.2), (-1, -1)), ((NORTH[0] + 0.02, Y0 + 0.02, BOARDS - 0.2), (1, 1)), ((X0 + 0.02, SOUTH[0] + 0.02, BOARDS - 0.2), (1, 1))):
        kit.web("Corner web", c, 0.45, f)
    dv, df = [], []
    for _ in range(500):
        if rng.random() < 0.6:
            x, y = rng.uniform(X0, X1), rng.choice((rng.uniform(SOUTH[0], SOUTH[0] + 0.3), rng.uniform(SOUTH[1] - 0.3, SOUTH[1])))
        else:
            x, y = rng.uniform(NORTH[0], NORTH[1]), rng.uniform(Y0, SOUTH[0])
        reb.box(dv, df, (x, y, 0.006), (0.012, 0.005, 0.005), rng.uniform(0, 3))
    reb.mesh_object("Rat droppings", dv, df, reb.mat_plain("Droppings", (0.02, 0.015, 0.012), 0.6), smooth=False)
    pv, pf = [], []
    for i in range(18):
        kit._stain(pv, pf, rng, (rng.uniform(2.0, 5.0), rng.uniform(SOUTH[0] + 0.1, SOUTH[0] + 0.5), 0.004), rng.uniform(0.02, 0.06), rng.uniform(0, 3), 0.6, (1.3, 0.8), i, points=7, drops=False)
    reb.mesh_object("Gnawed paper", pv, pf, mat("old paper"), smooth=False)
    reb.prim("cyl", "Poison tin", mat("yellow paint"), (5.6, SOUTH[0] + 0.3, 0.06), (0.14, 0.14, 0.12), rot=(math.pi / 2, 0, 0.4), segments=12)
    kit.text("Poison", "POISON", mat("red paint"), (5.6, SOUTH[0] + 0.375, 0.08), size=0.03, rot=(math.pi / 2, 0, 0.4 + math.pi))
    kit.splat("Spilled poison", reb.mat_plain("Poison grain", (0.4, 0.3, 0.1), 0.8), (5.85, SOUTH[0] + 0.45, 0.0), 0.15, seed=8, stretch=(1.6, 0.7))
    # Someone hid down here: a blanket, a candle stub, a biscuit tin.
    reb.cloth("Blanket", mat("flannel"), (7.25, 3.0, 0.03), (0.8, 1.3), rot=(0, 0, 0.1), cuts=14, lumps=0.05, seed=3)
    stub, stub_light, stub_flame = kit.candle("Candle stub", (6.75, 3.9, 0.0), energy=0.0, height=0.04)
    stub_light.data.energy = 0.0
    reb.emit_strength(stub_flame, 0.0)
    reb.prim("cyl", "Biscuit tin", reb.mat_plain("Tin blue", (0.05, 0.08, 0.2), 0.4), (7.7, 3.6, 0.05), (0.22, 0.22, 0.1), segments=16)
    reb.prim("cyl", "Biscuit tin lid", reb.mat_plain("Tin blue", (0.05, 0.08, 0.2), 0.4), (7.55, 3.9, 0.012), (0.23, 0.23, 0.02), rot=(0.1, 0, 0), segments=16)

    # ---- Light: bars through the board gaps from the warm rooms above; a walker crossing up there.
    kit.time_light("night")
    above = []
    for i, (x, y) in enumerate(((2.2, 5.2), (4.4, 5.2), (6.6, 5.2), (7.2, 3.4), (7.2, 2.0))):
        above.append(reb.spot(f"Room light above {i}", (x, y, BOARDS + 2.4), (x, y, 0.0), 1400, room_light, 70, 0.6, 0.15))
    reb.point("Hatch room light", ((hx0 + hx1) / 2, (hy0 + hy1) / 2, BOARDS + 1.2), 40, room_light, 0.2)
    walker = reb.prim("cube", "Someone walking above", reb.mat_plain("Shadow", (0.0, 0.0, 0.0), 1.0), (0, 0, BOARDS + 0.4), (0.35, 0.6, 0.6))
    reb.point("Under-glow", (4.5, 5.2, 1.2), 6, room_light, 0.5)
    reb.point("Under-glow north", (7.2, 3.0, 1.2), 4, room_light, 0.5)
    dust_m = reb.mat_emit("Dust", (1.0, 0.85, 0.6), 0.4)
    motes = []
    for i in range(24):
        p = reb.prim("sphere", "Dust mote", dust_m, (0, 0, 0), (0.006, 0.006, 0.006), segments=4)
        motes.append((p, rng.uniform(X0 + 0.3, X1 - 0.3), rng.uniform(SOUTH[0] + 0.2, SOUTH[1] - 0.2), rng.uniform(0.3, 1.7), i / 24))

    anim = kit.Anim(16)

    def walk(k):
        t = k / anim.frames
        # Across the south leg from north to south and back out of sight: two steps a loop.
        x = 3.3 + 2.4 * t
        walker.location = (x, SOUTH[0] - 0.8 + 2.4 * math.sin(math.pi * t), BOARDS + 0.4)
        walker.hide_render = not (0.1 < t < 0.9)
        for p, mx, my, mz, off in motes:
            u = (t + off) % 1.0
            p.location = (mx + 0.08 * math.sin(2 * math.pi * u), my, mz - 0.3 * u + 0.3 * off)
    anim.custom(walk)
    anim.sway(webs, amount=0.02, along=(0.6, 1.0), every=4, tip=2)

    # ---- What the game needs.
    room.door("cellar", (X0, SOUTH[0], X0 + 0.6, SOUTH[1]), arrive=(2.2, 5.2), face=(1, 0))
    room.door("save", (hx0, hy0, hx1, hy1 + 0.9), arrive=((hx0 + hx1) / 2, 3.2), face=(0, 1), walk=False)
    room.check((6.6, 2.4, 8.0, 3.8), "A blanket, a candle stub, an empty biscuit tin.\nSomeone hid down here.")
    room.check((5.2, SOUTH[0], 6.2, SOUTH[0] + 0.7), "Rat poison. The rats ate it all anyway.")
    room.check((3.0, SOUTH[0], 5.0, SOUTH[1]), "Footsteps, overhead. Slow ones.\nKeep going.")
    room.check((X1 - 0.6, SOUTH[0], X1, SOUTH[1]), "Pipes. Cobwebs. Rat droppings. Lovely.")
    room.entry = "Under the house.\nI can hear someone walking around up there."
    room.export(anim, samples=128)


build()
