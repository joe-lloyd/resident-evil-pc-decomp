"""The Spencer mansion's back garden, at night.

What it tells: the formal garden behind the house has gone wild in a
summer without its gardener: the box beds round the fountain are shaggy
and full of dead roses and weeds, the gravel is green, ivy climbs the
back of the house. The fountain still runs. The house's back wall is dark
grey stone, three storeys of tall windows, one lit high up. Its back door
has been boarded over from outside: someone wanted something kept in.
Beside it, the cellar's sloping bulkhead doors, under a lamp on the wall
that moths circle. A maid came up out of the cellar and ran: one of her
shoes is on the path by the bulkhead and her blood runs from there across
the gravel to the west hedge, where she lies face down, half dragged into
it, her cap in the gravel. The gardener's barrow lies tipped over by the
potting shed, its soil spilled, the spade where it was dropped.

Metres: the floor is x 2-17, y 2-13.8 at z 0. The house's back wall runs
along the south at y 14.0. The path from the kennels comes in through the
yews at the north edge, x 9-11. The fountain stands in the middle at
(10, 8), radius 1.5, with four box beds round it. The potting shed is in
the north-east, x 15.2-18.2, y 3.5-6.5, its door in the west wall at
y 4.6-5.4. The cellar's bulkhead is against the house at x 12.0-13.6,
y 12.6-14.0; the boarded back door at x 6.2-7.4. A tall hedge closes the
west side.

Moving: the fountain's water dripping and rippling, moths round the wall
lamp, the lamp's flame, the weeds.
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
from mathutils import Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 2.0, 17.0, 2.0, 13.8
HOUSE_Y = 14.0
NORTH = (9.0, 11.0)
FOUNTAIN = (10.0, 8.0, 1.5)
SHED = (15.2, 18.2, 3.5, 6.5)
SHED_DOOR = (4.6, 5.4)
BULKHEAD = (12.0, 13.6, 12.6, 14.0)
BACK_DOOR = (6.2, 7.4)
BEDS = ((5.0, 3.6, 8.2, 6.6), (11.8, 3.6, 13.4, 6.6), (5.0, 9.4, 8.2, 11.0), (11.8, 9.4, 15.0, 11.0))


def height(x, y):
    return 0.02 * noise.noise(Vector((x * 0.5, y * 0.5, 5)))


def ashlar(name, light, dark, mortar=(0.04, 0.04, 0.038), size=(0.6, 0.32)):
    """Dressed stone in courses on a wall along x or y, each block its own shade."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.85
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
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Color1"].default_value = (*light, 1)
    brick.inputs["Color2"].default_value = (*dark, 1)
    brick.inputs["Mortar"].default_value = (*mortar, 1)
    links.new(comb.outputs["Vector"], brick.inputs["Vector"])
    n = reb.noise_tex(nodes, links, 1.2, 8, 0.65)
    g = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, (0.4, 0.42, 0.36)), (0.65, (1, 1, 1))])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.85
    links.new(brick.outputs["Color"], mix.inputs["A"])
    links.new(g.outputs["Color"], mix.inputs["B"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    reb.bumped(nodes, links, bsdf, brick.outputs["Fac"], -0.6, 0.02)
    return m


def shaggy(rng, verts, faces, box, count, reach=0.25):
    """Leaf cards sprouting out of a clipped hedge's faces: a summer unclipped.
    box = (x0, y0, x1, y1, height)."""
    x0, y0, x1, y1, h = box
    for _ in range(count):
        side = rng.random()
        if side < 0.3:
            p = Vector((rng.uniform(x0, x1), rng.uniform(y0, y1), h))
            out = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 1)).normalized()
        else:
            edge = rng.randrange(4)
            z = rng.uniform(0.1, h)
            if edge == 0:
                p, out = Vector((rng.uniform(x0, x1), y0, z)), Vector((0, -1, 0.3))
            elif edge == 1:
                p, out = Vector((rng.uniform(x0, x1), y1, z)), Vector((0, 1, 0.3))
            elif edge == 2:
                p, out = Vector((x0, rng.uniform(y0, y1), z)), Vector((-1, 0, 0.3))
            else:
                p, out = Vector((x1, rng.uniform(y0, y1), z)), Vector((1, 0, 0.3))
            out = (out + Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.2, 0.5)))).normalized()
        reb.card(verts, faces, p, out, Vector((0, 0, 1)), rng.uniform(0.05, 0.09), rng.uniform(0.6, 1.0) * reach, 0.2)


def hedge(rng, name, m, box, verts, faces, density=60):
    """A clipped hedge gone shaggy: a rounded block and its stray growth. Blocks her."""
    x0, y0, x1, y1, h = box
    ob = reb.prim("cube", name, m, ((x0 + x1) / 2, (y0 + y1) / 2, h / 2), (x1 - x0, y1 - y0, h), bevel=min(0.2, h / 4))
    shaggy(rng, verts, faces, box, int(density * ((x1 - x0) + (y1 - y0)) * h))
    return reb.wall(ob)


def moths(anim, centre, count=10, radius=0.35):
    """Pale moths batting round a lamp, each on its own looping orbit."""
    m = reb.mat_emit("Moth wings", (0.75, 0.7, 0.55), 0.6)
    bugs = []
    for i in range(count):
        b = reb.prim("cube", "Moth", m, centre, (0.035, 0.018, 0.004))
        bugs.append((b, radius * anim.rng.uniform(0.4, 1.0), anim.rng.uniform(-0.25, 0.3), anim.rng.choice((1, 2, -1, -2)), anim.rng.uniform(0, 2 * math.pi)))

    def f(k):
        for b, r, h, speed, ph0 in bugs:
            a = ph0 + anim.phase(k, speed)
            b.location = (centre[0] + r * math.cos(a), centre[1] + r * math.sin(a) * 0.6, centre[2] + h + 0.08 * math.sin(3 * a))
            b.rotation_euler = (0.5 * math.sin(4 * a), 0, a)
    anim.custom(f)


def build():
    rng = random.Random(83)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((10.0, 1.6, 3.8), (10.0, 12.0, 1.6), 200, "from the yews at the north: the fountain, the house's back, the lit window")
    room.camera((2.4, 2.4, 3.6), (12.5, 11.0, 0.6), 200, "from the north-west: the beds, the fountain, the bulkhead under its lamp")
    room.camera((16.6, 13.4, 3.4), (8.0, 5.0, 0.4), 200, "from under the house, east: the shed, the tipped barrow, the beds")
    room.camera((2.6, 13.4, 3.2), (11.5, 5.0, 0.3), 200, "from under the house, west: the maid in the hedge, the fountain, the yews")
    room.camera((10.2, 10.2, 2.7), (13.0, 13.8, 0.5), 195, "close at the bulkhead: the cellar doors, the lamp and its moths, her shoe")
    room.camera((4.2, 13.2, 2.5), (4.0, 9.6, 0.1), 195, "close by the west bed: the maid dragged into the hedge, her cap, the trail from the bulkhead")

    house = ashlar("House stone", (0.2, 0.2, 0.19), (0.12, 0.12, 0.115))
    plinth_m = ashlar("Plinth stone", (0.16, 0.16, 0.15), (0.1, 0.1, 0.095), size=(0.8, 0.4))
    stone = reb.mat_surface("Fountain stone", [(0.0, (0.15, 0.15, 0.14)), (0.6, (0.26, 0.26, 0.24)), (1.0, (0.12, 0.15, 0.1))], scale=4, bump=0.6)
    box_m = reb.mat_surface("Box hedge", [(0.0, (0.01, 0.025, 0.01)), (1.0, (0.035, 0.07, 0.03))], scale=6, bump=1.0)
    yew = reb.mat_surface("Yew", [(0.0, (0.006, 0.018, 0.009)), (1.0, (0.025, 0.05, 0.02))], scale=5, bump=1.0)
    dark_glass = reb.mat_plain("Dark glass", (0.01, 0.012, 0.016), 0.15)
    frame_m = mat("white paint")
    door_m = kit.boards("Back door", (0.08, 0.06, 0.05), width=0.16, grime=0.6)
    bulk_m = reb.mat_surface("Bulkhead iron", [(0.0, (0.03, 0.035, 0.03)), (0.7, (0.06, 0.07, 0.055)), (1.0, (0.2, 0.09, 0.04))], scale=6, rough=0.6, bump=0.3)
    lit = reb.mat_emit("Lit window", (1.0, 0.6, 0.28), 4)
    dress = reb.mat_plain("Maid's black", (0.015, 0.014, 0.016), 0.7)
    apron = reb.mat_surface("Bloody apron", [(0.0, (0.55, 0.53, 0.5)), (0.6, (0.5, 0.48, 0.45)), (0.75, (0.2, 0.02, 0.01)), (1.0, (0.1, 0.005, 0.004))], scale=5, bump=0.1)
    soil = reb.mat_surface("Spilled soil", [(0.0, (0.03, 0.02, 0.012)), (1.0, (0.08, 0.055, 0.035))], scale=12, bump=0.8)

    # ---- Ground: gravel paths gone green, the beds' earth.
    reb.terrain("Garden", kit.dirtied(mat("gravel"), 0.7, scale=0.5), (-12, 32), (-4, HOUSE_Y + 0.5), height, step=0.5)
    for bx0, by0, bx1, by1 in BEDS:
        reb.prim("cube", "Bed earth", mat("mud"), ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.02), (bx1 - bx0 - 0.2, by1 - by0 - 0.2, 0.06))
    kit.cracks("Moss lines", reb.mat_plain("Moss", (0.03, 0.05, 0.02), 0.9), (X0, Y0, X1, Y1), count=30, seed=2, z=0.025, length=2.5)

    # ---- The house's back wall: three storeys, tall windows, ivy, the boarded door, the bulkhead.
    reb.wall(reb.prim("cube", "House", house, (9.0, HOUSE_Y + 6.0, 6.5), (44.0, 12.0, 13.0)))
    reb.prim("cube", "Plinth", plinth_m, (9.0, HOUSE_Y + 0.15, 0.4), (44.0, 0.3, 0.8))
    for z in (3.4, 7.2):
        reb.prim("cube", "String course", stone, (9.0, HOUSE_Y - 0.08, z), (44.0, 0.18, 0.18))
    reb.prim("cube", "Cornice", stone, (9.0, HOUSE_Y - 0.15, 12.6), (44.0, 0.4, 0.5))
    for side in (-1, 1):
        reb.prim("cube", "Roof", reb.mat_plain("Slate", (0.015, 0.017, 0.022), 0.6), (9.0, HOUSE_Y + 6.0 + side * 3.2, 15.0), (44.0, 7.6, 0.3), rot=(-side * 0.75, 0, 0))
    for x in (-3.0, 5.0, 14.0, 22.0):
        reb.prim("cube", "Chimney stack", house, (x, HOUSE_Y + 6.0, 17.5), (1.4, 1.4, 4.0))
    lit_at = None
    for i, x in enumerate((0.0, 3.2, 9.6, 15.4, 18.6, 21.8)):
        for z0, z1 in ((1.2, 3.0), (4.2, 6.6), (8.0, 10.0)):
            if 11.5 < x < 14.0 and z0 < 3:
                continue
            m = lit if (i, z0) in ((3, 8.0), (1, 1.2)) else dark_glass
            if m is lit and z0 > 5:
                lit_at = (x, (z0 + z1) / 2)
            reb.prim("cube", "Window", m, (x, HOUSE_Y - 0.02, (z0 + z1) / 2), (1.1, 0.04, z1 - z0))
            reb.prim("cube", "Window frame", frame_m, (x, HOUSE_Y - 0.05, (z0 + z1) / 2), (0.05, 0.03, z1 - z0))
            reb.prim("cube", "Window frame", frame_m, (x, HOUSE_Y - 0.05, z0 + (z1 - z0) * 0.62), (1.1, 0.03, 0.04))
            reb.prim("cube", "Sill", stone, (x, HOUSE_Y - 0.12, z0 - 0.06), (1.4, 0.24, 0.1))
            reb.prim("cube", "Lintel", stone, (x, HOUSE_Y - 0.06, z1 + 0.12), (1.4, 0.12, 0.22))
    reb.point("Lit window glow", (lit_at[0], HOUSE_Y - 0.8, lit_at[1]), 60, (1.0, 0.6, 0.28), 0.4)
    reb.spot("Downstairs window spill", (3.2, HOUSE_Y - 0.3, 2.4), (3.6, 10.2, 0.0), 260, (1.0, 0.6, 0.3), 60, 0.7, 0.4)
    # Drainpipes and the ivy up the wall.
    for x in (1.6, 11.2, 17.0):
        kit.rod("Drainpipe", mat("iron"), (x, HOUSE_Y - 0.1, 0.0), (x, HOUSE_Y - 0.1, 12.4), 0.05, 8)
    iv, ifc = [], []
    for cx, w, top in ((1.0, 2.6, 9.0), (8.4, 1.8, 5.0), (16.0, 3.0, 11.0)):
        for _ in range(int(w * top * 45)):
            x = cx + rng.uniform(-w / 2, w / 2)
            z = top * rng.random() ** 0.8
            a = rng.uniform(0, 2 * math.pi)
            reb.card(iv, ifc, Vector((x, HOUSE_Y - 0.03, z)), Vector((math.cos(a), 0, math.sin(a) - 0.3)).normalized(), Vector((0, -1, 0)), 0.1, 0.13, -0.5)
    ivy_ob = reb.mesh_object("Ivy", iv, ifc, mat("ivy"), smooth=False)
    # The back door, boarded over from outside, a step up to it.
    bd = BACK_DOOR
    reb.prim("cube", "Back door", door_m, ((bd[0] + bd[1]) / 2, HOUSE_Y - 0.02, 1.25), (bd[1] - bd[0], 0.06, 2.5))
    reb.prim("cube", "Door surround", stone, ((bd[0] + bd[1]) / 2, HOUSE_Y - 0.08, 2.75), (bd[1] - bd[0] + 0.5, 0.16, 0.4))
    for x in (bd[0] - 0.15, bd[1] + 0.15):
        reb.prim("cube", "Door pilaster", stone, (x, HOUSE_Y - 0.08, 1.3), (0.25, 0.16, 2.6))
    reb.wall(reb.prim("cube", "Back step", stone, ((bd[0] + bd[1]) / 2, HOUSE_Y - 0.35, 0.09), (bd[1] - bd[0] + 0.8, 0.7, 0.18)))
    kit.barricade("Boards over the door", mat("planks"), (bd[0] - 0.1, HOUSE_Y - 0.1), (bd[1] + 0.1, HOUSE_Y - 0.1), z0=0.4, z1=2.2, count=5, seed=3)
    kit.text("Daubed", "KEEP OUT", mat("white paint"), ((bd[0] + bd[1]) / 2, HOUSE_Y - 0.14, 1.05), size=0.16)
    # The bulkhead: two sloping iron doors in a stone curb, shut, chained.
    cx0, cx1, cy0, cy1 = BULKHEAD
    rise = math.atan2(0.75, cy1 - cy0)
    reb.wall(reb.prim("cube", "Bulkhead curb", stone, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.2), (cx1 - cx0 + 0.3, cy1 - cy0, 0.4)))
    for i, (a, b) in enumerate(((cx0, (cx0 + cx1) / 2 - 0.01), ((cx0 + cx1) / 2 + 0.01, cx1))):
        reb.prim("cube", f"Bulkhead door {i}", bulk_m, ((a + b) / 2, (cy0 + cy1) / 2, 0.6), (b - a, (cy1 - cy0) / math.cos(rise), 0.05), rot=(rise, 0, 0))
        for t in (0.25, 0.75):
            reb.prim("cube", "Strap", mat("rust"), ((a + b) / 2, cy0 + (cy1 - cy0) * t, 0.6 + (t - 0.5) * 0.75 + 0.03), (b - a - 0.05, 0.06, 0.02), rot=(rise, 0, 0))
    for side in (-1, 1):
        reb.prim("cube", "Bulkhead cheek", stone, ((cx0 + cx1) / 2 + side * ((cx1 - cx0) / 2 + 0.1), (cy0 + cy1) / 2, 0.55), (0.2, cy1 - cy0, 0.4), rot=(rise, 0, 0))
    reb.prim("cube", "Hasp", mat("iron"), ((cx0 + cx1) / 2, cy0 + 0.35, 0.82), (0.12, 0.05, 0.03), rot=(rise, 0, 0))
    reb.prim("cube", "Cellar padlock", reb.mat_metal("Brass", (0.45, 0.33, 0.12), 0.45), ((cx0 + cx1) / 2, cy0 + 0.32, 0.76), (0.07, 0.04, 0.09), bevel=0.01)
    kit.scratches("Clawed bulkhead", mat("steel"), ((cx0 + cx1) / 2 - 0.3, cy0 + 0.2, 0.75), (0, -1), count=5, length=0.3, seed=7)
    kit.splat("Bloody hand on the door", mat("blood"), (cx0 + 0.4, cy0 + 0.4, 0.8), 0.07, rot=(rise, 0, 0), seed=5)
    # The lamp on the wall over it, moths round it.
    kit.rod("Lamp bracket", mat("iron"), (11.4, HOUSE_Y, 2.8), (11.4, HOUSE_Y - 0.45, 2.8), 0.02)
    lamp, lamp_light, flame = kit.lantern("Wall lamp", (11.4, HOUSE_Y - 0.45, 2.4), energy=55, hanging=True)
    reb.spot("Wall lamp throw", (11.4, HOUSE_Y - 0.6, 2.7), (11.8, 11.0, 0.0), 160, (1.0, 0.62, 0.3), 100, 0.8, 0.2)

    # ---- The maid: up out of the cellar, her shoe left on the path, dragged into the west hedge.
    reb.prim("cube", "Her shoe", reb.mat_plain("Patent leather", (0.01, 0.01, 0.01), 0.2), (11.6, 12.2, 0.04), (0.22, 0.08, 0.08), rot=(0, 0.2, 2.6), bevel=0.02)
    kit.drag_trail("Her blood to the hedge", mat("old blood"), [(12.4, 12.4), (10.4, 12.6), (7.8, 12.3), (5.4, 11.2), (4.0, 10.4), (3.4, 10.1)], width=0.3, seed=11, height=height)
    kit.drag_trail("Fresh at the hedge", mat("blood"), [(5.0, 10.9), (3.6, 10.2)], width=0.35, seed=12, height=height)
    maid = kit.body("Maid", (5.0, 10.15, 0.02), heading=math.pi + 0.1, pose="front", top=dress, legs=dress, seed=9)
    reb.cloth("Apron, torn", apron, (4.1, 9.65, 0.05), (0.4, 0.5), rot=(0, 0, 0.6), cuts=8, lumps=0.03, seed=4)
    reb.cloth("Apron on the hedge", apron, (3.05, 9.3, 1.1), (0.25, 0.35), rot=(0.3, math.pi / 2, 0), cuts=6, lumps=0.03, seed=5)
    reb.prim("cyl", "Maid's cap", reb.mat_plain("Starched white", (0.6, 0.6, 0.57), 0.6), (5.4, 9.6, 0.03), (0.18, 0.18, 0.04), rot=(0.2, 0, 0), segments=14)
    kit.splat("Pool at the hedge", mat("blood"), (3.9, 10.15, height(3.9, 10.15)), 0.4, seed=13, stretch=(1.3, 0.8))

    # ---- Hedges: the tall west hedge, yews at the north, four box beds round the fountain.
    hv, hf = [], []
    hedge(rng, "West hedge", yew, (1.3, 2.0, 3.1, HOUSE_Y - 0.2, 2.4), hv, hf, density=35)
    hedge(rng, "North yews west", yew, (-6.0, 0.2, NORTH[0], 1.8, 2.4), hv, hf, density=20)
    hedge(rng, "North yews east", yew, (NORTH[1], 0.2, 20.0, 1.8, 2.4), hv, hf, density=20)
    hedge(rng, "East hedge", yew, (17.2, 7.2, 19.0, HOUSE_Y - 0.2, 2.4), hv, hf, density=30)
    beds_veg_v, beds_veg_f = [], []
    for i, (bx0, by0, bx1, by1) in enumerate(BEDS):
        for (a0, b0, a1, b1) in ((bx0, by0, bx1, by0 + 0.35), (bx0, by1 - 0.35, bx1, by1), (bx0, by0, bx0 + 0.35, by1), (bx1 - 0.35, by0, bx1, by1)):
            reb.prim("cube", "Box edging", box_m, ((a0 + a1) / 2, (b0 + b1) / 2, 0.3), (a1 - a0, b1 - b0, 0.6), bevel=0.1)
            shaggy(rng, hv, hf, (a0, b0, a1, b1, 0.6), int(30 * ((a1 - a0) + (b1 - b0))), reach=0.2)
        reb.wall(reb.prim("cube", "Bed footprint", None, ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.3), (bx1 - bx0, by1 - by0, 0.6))).hide_render = True
        # Dead roses and weeds standing up out of the bed.
        for _ in range(int((bx1 - bx0) * (by1 - by0) * 6)):
            c = Vector((rng.uniform(bx0 + 0.5, bx1 - 0.5), rng.uniform(by0 + 0.5, by1 - 0.5), 0.05))
            for _ in range(rng.randint(3, 6)):
                tip = c + Vector((rng.gauss(0, 0.15), rng.gauss(0, 0.15), rng.uniform(0.5, 1.2)))
                w = Vector((0.01, 0.01, 0))
                k = len(beds_veg_v)
                beds_veg_v.extend([tuple(c - w), tuple(c + w), tuple(tip)])
                beds_veg_f.append((k, k + 1, k + 2))
    reb.mesh_object("Hedge growth", hv, hf, mat("leaves"), smooth=False)
    weeds = reb.mesh_object("Dead roses", beds_veg_v, beds_veg_f, reb.mat_cards("Dead stems", (0.05, 0.04, 0.02), (0.15, 0.12, 0.06)), smooth=False)
    rv, rf = [], []
    for _ in range(40):
        bx0, by0, bx1, by1 = rng.choice(BEDS)
        reb.boulder(rng, (rng.uniform(bx0 + 0.6, bx1 - 0.6), rng.uniform(by0 + 0.6, by1 - 0.6), 0.6 + rng.uniform(0, 0.3)), rng.uniform(0.12, 0.2), rv, rf, squash=1.0)
    reb.mesh_object("Rose heads, dead", rv, rf, reb.mat_plain("Dead roses", (0.12, 0.02, 0.025), 0.8))

    # ---- The fountain: a basin, a pedestal, a bowl, still running.
    fx, fy, fr = FOUNTAIN
    reb.wall(reb.prim("cyl", "Basin", stone, (fx, fy, 0.25), (fr * 2, fr * 2, 0.5), segments=40), "circle")
    reb.prim("cyl", "Basin lip", stone, (fx, fy, 0.52), (fr * 2 + 0.12, fr * 2 + 0.12, 0.06), segments=40)
    water = mat("water")
    reb.prim("cyl", "Basin water", water, (fx, fy, 0.555), (fr * 2 - 0.3, fr * 2 - 0.3, 0.01), segments=40)
    reb.prim("cyl", "Pedestal", stone, (fx, fy, 0.9), (0.32, 0.32, 0.9), segments=16)
    reb.prim("cone", "Upper bowl", stone, (fx, fy, 1.45), (1.3, 1.3, 0.22), rot=(math.pi, 0, 0), top=0.35, segments=28)
    reb.prim("cyl", "Bowl water", water, (fx, fy, 1.55), (1.2, 1.2, 0.01), segments=28)
    reb.prim("cyl", "Finial stem", stone, (fx, fy, 1.8), (0.12, 0.12, 0.5), segments=10)
    reb.prim("sphere", "Finial", stone, (fx, fy, 2.1), (0.22, 0.22, 0.26), segments=12)
    reb.prim("cyl", "Spout stream", reb.mat_glass("Falling water", (0.7, 0.75, 0.8)), (fx, fy, 1.85), (0.03, 0.03, 0.55), segments=8)
    kit.splat("Scum in the basin", reb.mat_plain("Pond scum", (0.04, 0.06, 0.02), 0.7), (fx + 0.5, fy - 0.3, 0.562), 0.5, seed=21, stretch=(1.2, 0.8))
    kit.splat("Moss on the basin", reb.mat_plain("Moss", (0.03, 0.05, 0.02), 0.9), (fx - fr - 0.002, fy, 0.25), 0.3, rot=(0, math.pi / 2, 0), seed=22, stretch=(1.6, 0.6))

    # ---- The potting shed, north-east: boards, a tin roof, its door shut.
    sx0, sx1, sy0, sy1 = SHED
    shed_boards = kit.boards("Shed boards", (0.12, 0.1, 0.07), width=0.15, grime=0.7)
    for ob in kit.walls(sx0 + 0.06, sy0 + 0.06, sx1 - 0.06, sy1 - 0.06, 2.3, shed_boards, openings=[("w", SHED_DOOR[0], SHED_DOOR[1], 0.0, 1.95), ("w", 5.8, 6.2, 1.1, 1.6)], thick=0.12, name="Shed wall"):
        reb.wall(ob)
    reb.prim("cube", "Shed roof", mat("tin"), ((sx0 + sx1) / 2, (sy0 + sy1) / 2, 2.5), (sx1 - sx0 + 0.5, sy1 - sy0 + 0.5, 0.06), rot=(0, 0.12, 0))
    reb.prim("cube", "Shed inside", reb.mat_plain("Shed dark", (0.01, 0.01, 0.008), 0.9), ((sx0 + sx1) / 2, (sy0 + sy1) / 2, 1.1), (sx1 - sx0 - 0.4, sy1 - sy0 - 0.4, 2.2))
    reb.prim("cube", "Shed door", kit.boards("Shed door", (0.15, 0.1, 0.06), width=0.12, grime=0.7), (sx0 + 0.02, sum(SHED_DOOR) / 2, 0.97), (0.05, SHED_DOOR[1] - SHED_DOOR[0], 1.94))
    reb.prim("sphere", "Shed door knob", mat("iron"), (sx0 - 0.03, SHED_DOOR[0] + 0.12, 1.0), (0.05, 0.05, 0.05), segments=8)
    reb.prim("cube", "Shed window", reb.mat_glass("Cobwebbed glass", (0.45, 0.45, 0.4)), (sx0, 6.0, 1.35), (0.01, 0.4, 0.5))
    for k in range(4):
        reb.prim("cone", f"Stacked pot {k}", reb.mat_plain("Terracotta", (0.3, 0.12, 0.06), 0.8), (sx0 - 0.3, 3.9, 0.1 + k * 0.08), (0.24, 0.24, 0.2), rot=(math.pi, 0, 0), top=0.7, segments=10)
    reb.wall(kit.box("Water butt", reb.mat_wood("Butt staves", (0.15, 0.1, 0.06)), (sx0 - 0.35, 6.2, 0.0), (0.55, 0.55, 0.9)))
    # The barrow, tipped, its soil spilled, the spade dropped.
    bx, by = 12.8, 7.6
    tray = kit.join("Barrow", [
        reb.prim("cube", "tray floor", mat("green paint"), (0, 0, 0.0), (0.7, 0.55, 0.03)),
        reb.prim("cube", "tray side", mat("green paint"), (0, 0.29, 0.13), (0.8, 0.03, 0.28), rot=(-0.3, 0, 0)),
        reb.prim("cube", "tray side", mat("green paint"), (0, -0.29, 0.13), (0.8, 0.03, 0.28), rot=(0.3, 0, 0)),
        reb.prim("cube", "tray front", mat("green paint"), (0.42, 0, 0.13), (0.03, 0.6, 0.28), rot=(0, 0.5, 0)),
        kit.rod("handle", mat("pine"), (-0.3, 0.22, 0.02), (-1.1, 0.26, 0.0), 0.02, 6),
        kit.rod("handle", mat("pine"), (-0.3, -0.22, 0.02), (-1.1, -0.26, 0.0), 0.02, 6),
        kit.rod("leg", mat("iron"), (-0.3, 0.2, 0.0), (-0.3, 0.2, -0.3), 0.012, 4),
        kit.rod("leg", mat("iron"), (-0.3, -0.2, 0.0), (-0.3, -0.2, -0.3), 0.012, 4),
        reb.prim("cyl", "wheel", mat("rubber"), (0.55, 0, -0.12), (0.34, 0.34, 0.07), rot=(math.pi / 2, 0, 0), segments=16),
    ])
    tray.location = (bx, by, 0.3)
    tray.rotation_euler = (1.45, 0, 2.3)
    reb.wall(reb.prim("cube", "Barrow footprint", None, (bx, by, 0.3), (1.0, 1.0, 0.6))).hide_render = True
    sv, sf = [], []
    for i in range(14):
        kit._stain(sv, sf, rng, (bx + 0.5 + rng.gauss(0, 0.3), by + 0.5 + rng.gauss(0, 0.25), 0.012), rng.uniform(0.1, 0.25), rng.uniform(0, 3), 0.4, (1.3, 0.8), i, points=12, drops=False)
    reb.mesh_object("Spilled soil", sv, sf, soil, smooth=False)
    for i in range(5):
        p = (bx + 0.6 + rng.uniform(-0.4, 0.5), by + 0.6 + rng.uniform(-0.4, 0.4))
        kit.rod("Uprooted seedling", reb.mat_plain("Wilted green", (0.06, 0.08, 0.03), 0.8), (p[0], p[1], 0.02), (p[0] + rng.uniform(-0.15, 0.15), p[1] + rng.uniform(-0.15, 0.15), 0.05), 0.008, 4)
    reb.prim("cube", "Spade blade", mat("rust"), (13.9, 8.9, 0.02), (0.18, 0.25, 0.012), rot=(0, 0, 0.8))
    kit.rod("Spade handle", mat("pine"), (13.8, 8.75, 0.03), (13.1, 8.0, 0.03), 0.018, 6)
    # A stone bench, an urn knocked off its plinth and broken.
    reb.wall(reb.prim("cube", "Bench seat", stone, (6.6, 2.7, 0.45), (1.6, 0.45, 0.08)))
    for x in (6.0, 7.2):
        reb.prim("cube", "Bench leg", stone, (x, 2.7, 0.21), (0.15, 0.4, 0.42))
    reb.wall(reb.prim("cube", "Urn plinth", stone, (13.6, 2.7, 0.45), (0.5, 0.5, 0.9)))
    reb.prim("cone", "Urn, fallen", stone, (13.1, 3.2, 0.25), (0.6, 0.6, 0.5), rot=(math.pi / 2 - 0.2, 0, 0.8), top=0.6, segments=16)
    kit.shards("Urn shards", (12.9, 3.4, 0.0), spread=0.6, count=12, seed=8, m=stone)

    # ---- Beyond: the woods over the yews and hedges.
    kit.forest(rng, lambda x, y: 0.0, lambda x, y: (-4 < x < 21 and y > -1.5) or y > HOUSE_Y, (-24, -26, 40, 26), count=60, spacing=2.6, tall=(12, 20), ferns=0, needles=0)
    grass = kit.meadow(rng, 900, lambda r: (r.uniform(X0, X1), r.uniform(Y0, Y1)), height, mat("blades"))

    # ---- Light: the moon, the wall lamp by the bulkhead, the lit window high up.
    kit.time_light("night", sun_heading=60, sun_energy=0.4)
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(35), 0, math.radians(200)))
    fill = bpy.context.active_object
    fill.name, fill.data.energy, fill.data.color = "Night sky fill", 0.08, (0.35, 0.42, 0.7)

    anim = kit.Anim(16)
    anim.ripple(water)
    for i in range(8):
        a = 2 * math.pi * i / 8
        anim.drip((fx + math.cos(a) * 0.62, fy + math.sin(a) * 0.62, 1.5), fall=0.93, size=0.018, m=water)
    moths(anim, (11.4, HOUSE_Y - 0.45, 2.6), count=10, radius=0.4)
    anim.flicker(lamp_light, flame, depth=0.2, dropouts=0)
    anim.sway(weeds, amount=0.05)
    anim.sway(grass, amount=0.04)

    # ---- What the game needs.
    room.door("kennels", (NORTH[0], Y0, NORTH[1], Y0 + 0.6), arrive=(10.0, 3.4), face=(0, 1))
    room.door("garden-shed", (sx0 - 0.6, SHED_DOOR[0], sx0, SHED_DOOR[1]), arrive=(14.0, 5.0), face=(-1, 0), walk=False)
    room.door("cellar", (cx0, cy0 - 0.6, cx1, cy0), arrive=(12.8, 11.5), face=(0, -1), walk=False)
    room.check((cx0, cy0 - 0.7, cx1, cy0), "Cellar doors. Padlocked.\nThere's blood on the handle.")
    room.check((bd[0], HOUSE_Y - 1.0, bd[1], Y1), "The back door's been boarded over. From out here.\nKEEP OUT.")
    room.check((3.1, 9.4, 5.6, 10.9), "One of the maids. Something dragged her into the hedge.\nShe came from the cellar doors. She was running.")
    room.check((11.2, 11.8, 12.0, 12.6), "A shoe. Hers, I think.")
    room.check((fx - fr - 0.6, fy - fr - 0.6, fx + fr + 0.6, fy + fr + 0.6), "The fountain's still running. There's no one left to turn it off.")
    room.check((12.0, 7.0, 14.2, 9.3), "The gardener's barrow, tipped over. Seedlings, spilled.\nHe never finished.")
    room.check((10.8, 12.6, 12.0, Y1), "The lamp's lit. The moths found it.")
    room.entry = "The back of the mansion.\nThe house is dark."
    room.export(anim, samples=128)


build()
