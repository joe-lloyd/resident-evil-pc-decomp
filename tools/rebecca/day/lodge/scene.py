"""Inside the estate gardener's lodge, at dusk.

What it tells: the gardener caught it first and slowest. His diary on the
table tells the itching, day by day, down to its last line: "itchy. itchy.
scott came. ugly face so i killed him. tasty". Scott's blood is pooled by
the door where it happened, and a gnawed bone lies on a plate by the lamp
he never put out. He scratched himself raw: his bed is a mess of bloody
sheets and flakes of skin, the plaster above it is clawed through in
furrows, and across the wall he has written ITCHY in blood. He washed and
washed: the basin on the stand is pink. Then he went out and someone
padlocked the door behind him. His life is still on the walls: the tools
on their pegs, seed trays under the window, his boots by the door. The
estate's back gate key hangs on its hook by the door, tagged.

Metres: the floor is x 1.0-5.4, y 1.0-4.6, 2.5 high to the beams. The door
is in the east wall at y 1.7-2.6, out to the creek. The window is in the
north wall at x 2.2-3.2. The fireplace is in the south-west corner, the bed
along the south wall, the washstand in the north-east corner.

Moving: the lamp's flame, the flies over the plate, the embers in the grate.
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

X0, X1, Y0, Y1, H = 1.0, 5.4, 1.0, 4.6, 2.5
DOOR = (1.7, 2.6)           # y, east wall
WINDOW = (2.2, 3.2, 1.0, 1.8)   # x0, x1, z0, z1, north wall


def ashlar(name, light, dark, mortar=(0.05, 0.05, 0.045), size=(0.5, 0.26)):
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
    brick.inputs["Mortar Size"].default_value = 0.018
    brick.inputs["Color1"].default_value = (*light, 1)
    brick.inputs["Color2"].default_value = (*dark, 1)
    brick.inputs["Mortar"].default_value = (*mortar, 1)
    links.new(comb.outputs["Vector"], brick.inputs["Vector"])
    links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    reb.bumped(nodes, links, bsdf, brick.outputs["Fac"], -0.5, 0.02)
    return m


def settle(ob, offset, rot=None):
    """kit.join keeps its first part's frame, and kit.body, chair, crate,
    shelves, bunk and crow then place the result as if it had none: bodies
    stand on end, chairs sink. Move the mesh back into the prop's own frame
    (children are placed in that frame already)."""
    m = Matrix.Translation(offset)
    if rot is not None:
        m = m @ rot.to_matrix().to_4x4()
    ob.data.transform(m)
    return ob


def body(name, at, heading=0.0, pose="back", **kw):
    """kit.body lying as it should. No `bloody` or `sheet`: their pool lands wrong."""
    ob = kit.body(name, at, heading=heading, pose=pose, **kw)
    j, missing = kit._POSES[pose], kw.get("missing", ())
    a, b = next((Vector(j[p]), Vector(j[q])) for p, q, _, _ in kit._BONES if p not in missing and q not in missing)
    return settle(ob, (a + b) / 2, (b - a).to_track_quat("Z", "Y"))


def chair(name, m, at, rot=0.0, tipped=False):
    return settle(kit.chair(name, m, at, rot=rot, tipped=tipped), (0, 0, 0.45))


def crow(name, at, heading=0.0, perched=True):
    b, wings = kit.crow(name, at, heading=heading, perched=perched)
    settle(b, (0, 0, 0.12))
    return b, wings


def build():
    rng = random.Random(53)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((5.25, 1.15, 2.3), (2.0, 3.9, 0.5), 200, "high over the washstand: the table and its lamp, the bed, the fireplace, the tools")
    room.camera((1.85, 4.45, 2.3), (4.9, 1.6, 0.6), 200, "high by the fireplace: the table, the pink basin, the door, the key on its hook")
    room.camera((1.15, 1.15, 2.3), (4.7, 4.1, 0.5), 200, "high by the window: the bed, ITCHY on the wall, the pool by the door")
    room.camera((5.25, 4.45, 2.3), (2.0, 1.5, 0.7), 200, "high over the bed: the window, the seed trays, the diary, the tools")

    plaster = kit.dirtied(mat("plaster"), 0.8, scale=1.5)
    floor_m = kit.boards("Lodge floor", (0.17, 0.12, 0.07), width=0.15, grime=0.8)
    beam_m = mat("dark wood")
    stone = ashlar("Hearth stone", (0.22, 0.21, 0.19), (0.13, 0.125, 0.115), size=(0.4, 0.22))
    pink = reb.mat_plain("Pink water", (0.32, 0.08, 0.08), 0.05)
    china = reb.mat_plain("China", (0.6, 0.6, 0.56), 0.25)
    soil = reb.mat_surface("Potting soil", [(0.0, (0.03, 0.02, 0.012)), (1.0, (0.08, 0.055, 0.035))], scale=30, bump=0.8)
    bloody_sheet = reb.mat_surface("Bloody sheet", [(0.0, (0.5, 0.47, 0.4)), (0.45, (0.45, 0.42, 0.36)), (0.58, (0.25, 0.03, 0.02)), (0.8, (0.14, 0.01, 0.008)), (1.0, (0.08, 0.005, 0.004))], scale=3.5, bump=0.15)
    skin_flakes = reb.mat_plain("Skin flakes", (0.45, 0.36, 0.3), 0.8)
    towel_m = reb.mat_surface("Bloody towel", [(0.0, (0.45, 0.42, 0.36)), (0.6, (0.3, 0.06, 0.05)), (1.0, (0.12, 0.01, 0.01))], scale=6, bump=0.2)
    leather = reb.mat_plain("Diary leather", (0.12, 0.05, 0.03), 0.6)
    tray_m = mat("pine")

    # ---- The shell: whitewash gone grey over stone, a board floor, beams under a boarded ceiling.
    kit.walls(X0, Y0, X1, Y1, H, plaster, openings=[
        ("e", DOOR[0], DOOR[1], 0.0, 2.0),
        ("n", WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3]),
    ], thick=0.4, floor=floor_m, ceiling=kit.boards("Lodge ceiling", (0.12, 0.09, 0.06), width=0.14))
    for y in (1.8, 2.8, 3.8):
        reb.prim("cube", "Beam", beam_m, ((X0 + X1) / 2, y, H - 0.08), (X1 - X0 + 0.2, 0.14, 0.16))
    kit.splat("Damp", reb.mat_plain("Damp", (0.12, 0.11, 0.08), 0.9), (X0 + 0.005, 1.6, 0.4), 0.4, rot=(0, math.pi / 2, 0), seed=31, stretch=(1.8, 0.7))
    kit.web("Web", (X1 - 0.02, Y1 - 0.02, H - 0.2), 0.35, (-1, -1))
    kit.web("Web", (X0 + 0.02, Y0 + 0.02, H - 0.2), 0.3, (1, 1))
    # The door, shut, its planks and frame; the hasp's bolts through it.
    reb.prim("cube", "Door", kit.boards("Door planks", (0.16, 0.1, 0.05), width=0.14, grime=0.7), (X1 + 0.05, sum(DOOR) / 2, 1.0), (0.06, DOOR[1] - DOOR[0], 2.0))
    for y in (DOOR[0] - 0.04, DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", beam_m, (X1 - 0.02, y, 1.03), (0.09, 0.08, 2.06))
    reb.prim("cube", "Door head", beam_m, (X1 - 0.02, sum(DOOR) / 2, 2.06), (0.09, DOOR[1] - DOOR[0] + 0.16, 0.08))
    for z in (0.4, 1.6):
        reb.prim("cube", "Ledge", beam_m, (X1 + 0.015, sum(DOOR) / 2, z), (0.03, DOOR[1] - DOOR[0] - 0.05, 0.1))
    reb.prim("cube", "Latch", mat("iron"), (X1 - 0.0, DOOR[0] + 0.12, 1.05), (0.04, 0.16, 0.04))
    kit.scratches("Clawed door", mat("pine"), (X1 + 0.015, sum(DOOR) / 2, 1.55), (-1, 0), count=8, length=0.9, seed=5)
    # The window: four panes, grime, the red last light beyond and the trees.
    for i, (x0, x1) in enumerate(((WINDOW[0], 2.69), (2.71, WINDOW[1]))):
        reb.prim("cube", f"Pane {i}", reb.mat_glass("Grimy glass", (0.55, 0.5, 0.45)), ((x0 + x1) / 2, Y0 - 0.2, (WINDOW[2] + WINDOW[3]) / 2), (x1 - x0, 0.01, WINDOW[3] - WINDOW[2]))
    reb.prim("cube", "Mullion", mat("white paint"), (2.7, Y0 - 0.2, 1.4), (0.04, 0.05, 0.8))
    reb.prim("cube", "Transom", mat("white paint"), (2.7, Y0 - 0.2, 1.4), (1.0, 0.05, 0.04))
    reb.prim("cube", "Sill", mat("dark wood"), (2.7, Y0 + 0.02, WINDOW[2] - 0.02), (1.2, 0.12, 0.04))
    kit.splat("Hand smear", mat("old blood"), (2.95, Y0 - 0.19, 1.25), 0.1, rot=(math.pi / 2, 0, 0), seed=4, stretch=(0.6, 1.6))
    reb.prim("cube", "Outside ground", mat("grass"), (2.7, Y0 - 6.0, -0.1), (14.0, 10.0, 0.1))
    for i in range(7):
        x = rng.uniform(-3.5, 8.5)
        kit.rod("Outside trunk", mat("bark"), (x, Y0 - rng.uniform(3.0, 9.0), -0.1), (x, Y0 - 6.0, 9.0), rng.uniform(0.15, 0.3), 7)
    reb.prim("cube", "Outside creek", mat("water"), (2.7, Y0 - 3.0, -0.25), (14.0, 2.0, 0.02))

    # ---- The fireplace, south-west: a stone surround, the grate, a kettle on its crane.
    fx, fy = X0 + 0.35, 3.95
    reb.wall(reb.prim("cube", "Chimney breast", stone, (fx, fy, H / 2), (0.7, 1.2, H)))
    reb.prim("cube", "Firebox", mat("black"), (fx + 0.36, fy, 0.4), (0.04, 0.7, 0.6))
    reb.prim("cube", "Mantel", beam_m, (fx + 0.42, fy, 1.15), (0.2, 1.35, 0.08))
    reb.prim("cube", "Hearth", stone, (fx + 0.6, fy, 0.03), (0.5, 1.3, 0.06))
    ember_m = reb.mat_emit("Embers", (1.0, 0.25, 0.05), 3)
    for i in range(8):
        reb.prim("sphere", f"Ember {i}", ember_m, (fx + 0.44, fy + rng.uniform(-0.2, 0.2), 0.14 + rng.uniform(0, 0.05)), (0.06, 0.06, 0.04), segments=6)
    reb.prim("cube", "Grate", mat("iron"), (fx + 0.45, fy, 0.12), (0.2, 0.55, 0.06))
    kit.splat("Ash", reb.mat_plain("Ash", (0.2, 0.19, 0.18), 1.0), (fx + 0.7, fy, 0.065), 0.25, seed=8)
    kit.rod("Kettle crane", mat("iron"), (fx + 0.4, fy - 0.3, 0.75), (fx + 0.5, fy, 0.75), 0.012)
    reb.prim("sphere", "Kettle", mat("iron"), (fx + 0.5, fy, 0.6), (0.22, 0.22, 0.18), segments=12)
    kit.rod("Poker", mat("iron"), (fx + 0.62, fy + 0.6, 0.0), (fx + 0.42, fy + 0.58, 0.7), 0.01)
    on_mantel = [("cyl", mat("rust"), 0.1, 0.14), ("cyl", mat("bottle"), 0.07, 0.25), ("cube", mat("old paper"), 0.12, 0.16)]
    for i, (k, m, w, h) in enumerate(on_mantel):
        reb.prim(k, f"Mantel thing {i}", m, (fx + 0.42, fy - 0.4 + i * 0.35, 1.19 + h / 2), (w, w, h), segments=10)
    heat = reb.point("Ember glow", (fx + 0.6, fy, 0.25), 6, (1.0, 0.3, 0.06), 0.1)

    # ---- The bed along the south wall: an iron frame, bloody sheets, skin.
    bx0, bx1 = 3.2, 5.25
    by0, by1 = Y1 - 0.95, Y1 - 0.05
    bed_parts = []
    for x in (bx0, bx1):
        for y in (by0, by1):
            bed_parts.append(kit.rod("Bed post", mat("iron"), (x, y, 0), (x, y, 0.95 if x == bx1 else 0.7), 0.025))
    for y in (by0, by1):
        bed_parts.append(kit.rod("Bed rail", mat("iron"), (bx0, y, 0.38), (bx1, y, 0.38), 0.02))
    for x, top in ((bx0, 0.7), (bx1, 0.95)):
        bed_parts.append(kit.rod("Bed end", mat("iron"), (x, by0, top), (x, by1, top), 0.02))
        for k in range(4):
            y = by0 + (k + 1) * (by1 - by0) / 5
            bed_parts.append(kit.rod("Bed spindle", mat("iron"), (x, y, 0.38), (x, y, top), 0.01))
    bed = kit.join("Bed frame", bed_parts)
    reb.wall(reb.prim("cube", "Bed footprint", None, ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.3), (bx1 - bx0, by1 - by0, 0.6))).hide_render = True
    reb.prim("cube", "Mattress", mat("mattress"), ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.47), (bx1 - bx0 - 0.08, by1 - by0 - 0.06, 0.16), bevel=0.04)
    reb.cloth("Sheet, kicked down", bloody_sheet, ((bx0 + bx1) / 2 - 0.15, (by0 + by1) / 2 - 0.05, 0.62), (1.6, 1.0), rot=(0, 0, 0.05), cuts=20, lumps=0.05, seed=3)
    reb.cloth("Blanket on the floor", mat("flannel"), (bx0 - 0.25, by0 + 0.2, 0.02), (0.8, 1.0), rot=(0, 0, 0.4), cuts=16, lumps=0.06, seed=4)
    reb.prim("cube", "Pillow", bloody_sheet, (bx1 - 0.3, (by0 + by1) / 2, 0.62), (0.4, 0.6, 0.12), rot=(0, 0, 0.1), bevel=0.04)
    kit.splat("Blood soaked in", mat("old blood"), ((bx0 + bx1) / 2 + 0.3, (by0 + by1) / 2, 0.69), 0.3, seed=12, stretch=(1.4, 0.8))
    fv, ff = [], []
    for _ in range(140):
        x, y = rng.uniform(bx0, bx1), rng.uniform(by0, by1)
        kit._stain(fv, ff, rng, (x, y, 0.695), rng.uniform(0.006, 0.015), 0.0, 0.5, (1, 1), 1, points=5, drops=False)
    for _ in range(80):
        x, y = rng.uniform(bx0 - 0.6, bx1), rng.uniform(by0 - 0.6, by0)
        kit._stain(fv, ff, rng, (x, y, 0.004), rng.uniform(0.006, 0.015), 0.0, 0.5, (1, 1), 1, points=5, drops=False)
    reb.mesh_object("Skin flakes", fv, ff, skin_flakes, smooth=False)
    # The wall over the bed, clawed to the stone, ITCHY written across it in blood.
    for i, (x, z) in enumerate(((3.5, 1.7), (3.95, 1.55), (4.4, 1.8), (4.85, 1.5), (5.2, 1.65))):
        kit.scratches(f"Clawed plaster {i}", mat("old blood"), (x, Y1 - 0.004, z), (0, -1), count=rng.randint(4, 6), length=rng.uniform(0.5, 0.9), seed=10 + i)
    kit.text("ITCHY", "ITCHY ITCHY", mat("blood"), (4.2, Y1 - 0.006, 1.2), size=0.22)
    kit.scratches("Clawed corner", mat("old blood"), (X1 - 0.004, 3.8, 1.6), (-1, 0), count=6, length=0.8, seed=21)
    for i in range(4):
        kit.splat(f"Smear {i}", mat("old blood"), (3.4 + i * 0.5, Y1 - 0.005, 0.95 + rng.uniform(-0.1, 0.3)), 0.07, rot=(math.pi / 2, 0, 0), seed=40 + i, stretch=(0.5, 1.6))

    # ---- The table by the window: the diary open, the lamp burning, a plate with a gnawed bone.
    tx, ty = 2.6, 2.4
    reb.wall(kit.table("Table", mat("pine"), (tx, ty, 0.0), size=(1.2, 0.75, 0.76), rot=0.05))
    reb.prim("cube", "Diary", leather, (tx - 0.2, ty + 0.05, 0.775), (0.3, 0.22, 0.02), rot=(0, 0, 0.2))
    reb.prim("cube", "Diary pages", mat("old paper"), (tx - 0.2, ty + 0.05, 0.788), (0.28, 0.2, 0.008), rot=(0, 0, 0.2))
    for k in range(6):
        reb.prim("cube", "Scrawl", mat("black"), (tx - 0.26 + (k % 2) * 0.13, ty - 0.02 + (k // 2) * 0.05, 0.7925), (0.1, 0.006, 0.001), rot=(0, 0, 0.2 + rng.uniform(-0.15, 0.15)))
    reb.prim("cyl", "Pencil", mat("yellow paint"), (tx - 0.02, ty + 0.15, 0.78), (0.008, 0.008, 0.16), rot=(math.pi / 2, 0, 1.0), segments=6)
    lamp, lamp_light, flame = kit.lantern("Lamp", (tx + 0.3, ty - 0.15, 0.76), energy=34)
    reb.prim("cyl", "Plate", china, (tx + 0.25, ty + 0.18, 0.775), (0.26, 0.26, 0.015), segments=18)
    kit.rod("Gnawed bone", mat("bone"), (tx + 0.15, ty + 0.15, 0.8), (tx + 0.36, ty + 0.24, 0.8), 0.02, 6)
    reb.prim("sphere", "Knuckle", mat("bone"), (tx + 0.37, ty + 0.25, 0.8), (0.05, 0.045, 0.04), segments=8)
    kit.splat("Juice on the plate", mat("old blood"), (tx + 0.25, ty + 0.18, 0.784), 0.08, seed=6)
    reb.prim("cyl", "Mug", china, (tx - 0.4, ty - 0.22, 0.8), (0.08, 0.08, 0.09), segments=12)
    chair("Chair, tipped", mat("pine"), (tx - 0.2, ty + 0.7, 0.0), rot=math.pi / 2 + 0.3, tipped=True)
    chair("Chair", mat("pine"), (tx + 0.85, ty - 0.1, 0.0), rot=math.pi + 0.2)

    # ---- Under the window: the potting bench, seed trays gone to rot; the tools on the west wall.
    reb.wall(kit.table("Potting bench", mat("planks"), (1.85, Y0 + 0.3, 0.0), size=(1.5, 0.5, 0.82)))
    for i in range(3):
        x = 1.35 + i * 0.42
        kit.box(f"Seed tray {i}", tray_m, (x, Y0 + 0.3, 0.82), (0.38, 0.3, 0.06))
        reb.prim("cube", f"Tray soil {i}", soil, (x, Y0 + 0.3, 0.875), (0.34, 0.26, 0.01))
        sv, sf = [], []
        for _ in range(18):
            p = Vector((x + rng.uniform(-0.15, 0.15), Y0 + 0.3 + rng.uniform(-0.11, 0.11), 0.88))
            a = rng.uniform(0, 2 * math.pi)
            reb.card(sv, sf, p, Vector((math.cos(a), math.sin(a), 0.3)).normalized(), Vector((0, 0, 1)), 0.02, 0.06, 1.0)
        reb.mesh_object(f"Dead seedlings {i}", sv, sf, mat("dead grass"))
    for i in range(3):
        kit.box(f"Stacked tray {i}", tray_m, (1.5, Y0 + 0.3, 0.06 + i * 0.07), (0.38, 0.3, 0.06), rot=i * 0.08)
    for i in range(4):
        reb.prim("cone", f"Pot {i}", reb.mat_plain("Terracotta", (0.3, 0.12, 0.06), 0.8), (2.3 + i * 0.13, Y0 + 0.25, 0.9), (0.11, 0.11, 0.11), rot=(math.pi, 0, 0), top=0.7, segments=10)
    reb.prim("cube", "Seed packets", mat("old paper"), (2.5, Y0 + 0.4, 0.83), (0.12, 0.08, 0.01), rot=(0, 0, 0.5))
    reb.prim("cube", "Peg rail", beam_m, (X0 + 0.02, 2.2, 1.7), (0.04, 1.6, 0.08))
    tools = [("Spade", 1.6, 0.18, 0.25), ("Fork", 2.0, 0.16, 0.22), ("Rake", 2.4, 0.4, 0.06), ("Hoe", 2.8, 0.15, 0.1)]
    for name, y, w, hgt in tools:
        kit.rod(f"{name} handle", mat("pine"), (X0 + 0.06, y, 1.72), (X0 + 0.07, y + 0.03, 0.4), 0.017, 6)
        reb.prim("cube", f"{name} head", mat("rust"), (X0 + 0.07, y + 0.03, 0.35), (0.02, w, hgt))
    reb.prim("cube", "Shears", mat("steel"), (X0 + 0.06, 3.15, 1.4), (0.02, 0.06, 0.4), rot=(0.3, 0, 0))
    kit.rod("Hose", mat("green paint"), (X0 + 0.1, 3.0, 1.2), (X0 + 0.1, 3.2, 0.2), 0.06, 10)

    # ---- The washstand in the north-east corner: the basin of pink water, the jug, the towel.
    wx, wy = 4.75, Y0 + 0.28
    reb.wall(kit.table("Washstand", mat("pine"), (wx, wy, 0.0), size=(0.6, 0.45, 0.8)))
    reb.prim("cone", "Basin", china, (wx, wy, 0.86), (0.45, 0.45, 0.12), top=0.6, rot=(math.pi, 0, 0), segments=20)
    reb.prim("cyl", "Pink water", pink, (wx, wy, 0.9), (0.38, 0.38, 0.005), segments=20)
    reb.prim("cyl", "Jug", china, (wx + 0.2, wy + 0.1, 0.92), (0.13, 0.13, 0.24), segments=12)
    reb.prim("cube", "Mirror", reb.mat_metal("Mirror", (0.5, 0.5, 0.5), 0.15), (wx, Y0 + 0.01, 1.45), (0.4, 0.02, 0.5))
    kit.splat("Mirror smear", mat("old blood"), (wx - 0.05, Y0 + 0.025, 1.4), 0.12, rot=(math.pi / 2, 0, 0), seed=13, stretch=(1.4, 0.6))
    reb.cloth("Towel", towel_m, (wx - 0.32, wy + 0.1, 0.55), (0.35, 0.5), rot=(0, math.pi / 2, 0), cuts=8, lumps=0.02, seed=7)
    kit.splat("Pink drips", pink, (wx - 0.1, wy + 0.35, 0.0), 0.15, seed=14)

    # ---- By the door: his boots, coats, the key board; the pool where Scott died.
    reb.prim("cube", "Boot", mat("rubber"), (X1 - 0.25, 2.9, 0.18), (0.14, 0.3, 0.36), bevel=0.03)
    reb.prim("cube", "Boot, fallen", mat("rubber"), (X1 - 0.35, 3.25, 0.07), (0.14, 0.36, 0.14), rot=(0, 0, 0.7), bevel=0.03)
    kit.splat("Mud", mat("mud"), (X1 - 0.3, 3.05, 0.0), 0.18, seed=15)
    reb.prim("cube", "Key board", beam_m, (X1 - 0.02, 3.15, 1.5), (0.03, 0.4, 0.3))
    key_m = mat("iron")
    reb.prim("cyl", "Key bow", key_m, (X1 - 0.06, 3.1, 1.42), (0.08, 0.08, 0.015), rot=(0, math.pi / 2, 0), segments=12)
    reb.prim("cube", "Key shank", key_m, (X1 - 0.06, 3.1, 1.3), (0.015, 0.015, 0.2))
    reb.prim("cube", "Key bit", key_m, (X1 - 0.06, 3.125, 1.22), (0.015, 0.04, 0.04))
    reb.prim("cube", "Key tag", mat("old paper"), (X1 - 0.055, 3.22, 1.38), (0.01, 0.07, 0.1), rot=(0.2, 0, 0))
    for y in (3.0, 3.1, 3.2, 3.3):
        reb.prim("cyl", "Hook", mat("iron"), (X1 - 0.05, y, 1.55), (0.012, 0.012, 0.06), rot=(0, math.pi / 2, 0), segments=6)
    reb.cloth("Coat", mat("canvas"), (X1 - 0.08, 3.9, 1.3), (0.5, 0.9), rot=(math.pi / 2, 0, math.pi / 2), cuts=8, lumps=0.03, seed=2)
    reb.prim("sphere", "Hat", mat("khaki"), (X1 - 0.12, 3.9, 1.78), (0.3, 0.3, 0.12), segments=12)
    kit.splat("Where Scott died", mat("blood"), (4.4, 2.2, 0.0), 0.42, seed=16, stretch=(1.3, 1.0))
    kit.drag_trail("Dragged out", mat("old blood"), [(4.4, 2.2), (4.9, 2.15), (X1 - 0.05, 2.15)], width=0.35, seed=17)
    for i in range(5):
        kit.splat(f"Spatter {i}", mat("blood"), (X1 - 0.004, 1.9 + rng.uniform(-0.3, 0.6), 0.3 + rng.uniform(0, 0.6)), 0.03, rot=(0, math.pi / 2, 0), seed=50 + i)
    kit.papers("Diary pages torn out", (3.6, 2.9, 0.0), spread=0.6, count=4, seed=9, m=mat("old paper"))

    # ---- Light: dusk at the window, the lamp, the embers.
    kit.time_light("dusk", sun_heading=280, sun_energy=2.0)
    reb.spot("Dusk through the window", (2.7, Y0 - 3.0, 2.6), (4.0, 3.9, 0.4), 420, (1.0, 0.42, 0.28), 35, 0.6, 0.3)
    reb.spot("Sky at the window", (2.7, Y0 - 1.5, 1.6), (2.7, 3.0, 0.4), 40, (0.5, 0.55, 0.9), 70, 0.9, 0.6)

    anim = kit.Anim(16)
    anim.flicker(lamp_light, flame, depth=0.25, dropouts=1)
    anim.flicker(heat, ember_m, depth=0.3, dropouts=0)
    anim.flies((tx + 0.25, ty + 0.18, 0.8), count=8, radius=0.25)
    anim.flies((4.4, 2.2, 0.05), count=6, radius=0.3)

    # ---- What the game needs.
    room.door("creek", (X1 - 0.5, DOOR[0], X1, DOOR[1]), arrive=(4.6, 2.15), face=(-1, 0))
    room.check((tx - 0.6, ty - 0.4, tx + 0.1, ty + 0.4), "His diary. Day after day: the itching.\nThe last entry: itchy. itchy. scott came. ugly face so i killed him. tasty")
    room.check((tx + 0.1, ty - 0.4, tx + 0.7, ty + 0.4), "The lamp's still lit. On the plate, a bone. Gnawed.")
    room.check((bx0, by0 - 0.5, bx1, by0), "The sheets are soaked. Flakes of skin, everywhere.\nHe scratched himself raw.")
    room.check((4.4, Y0, X1, Y0 + 0.7), "The water in the basin is pink.")
    room.check((X1 - 0.6, 2.9, X1, 3.4), "A key on the hook. The tag says BACK GATE.")
    room.check((X0, 1.4, X0 + 0.6, 3.0), "His tools. Kept clean, oiled. Before.")
    room.check((1.1, Y0, 2.6, Y0 + 0.7), "Seed trays. Everything in them has died.")
    room.check((3.9, 1.8, 4.9, 2.6), "This is where it happened. Someone called Scott.")
    room.entry = "Someone left the lamp burning."
    room.export(anim, samples=128)


build()
