"""The logging camp's mess hall, noon: the cookhouse.

What it tells: the men who were still well sat down to a last meal
together. The stew was served and the bread cut, and then it went wrong at
the table: the benches went over, plates broke, a fork is driven into the
tabletop, blood has soaked into the boards where somebody was dragged
across them. Nobody finished eating. The flies have the plates now. The
cook held the serving counter. He died against it in his apron, his meat
cleaver dropped by his hand, the keys to the office still on his belt. On
the range behind the hatch the stew is still on a low fire, and the pot
still steams. The kitchen is a working camp kitchen: the sink tub full of
dishes, plates stacked on the shelves, tins and sacks of stores, pans on
their hooks, the coffee pot on the range. The menu board says what day it
was. The door to the yard is shut.

Metres: the floor is x 1.0-6.4, y 1.0-10.0, 2.8 high (in the yard the mess
is x -3.4-2.0, y 5.0-14.0: this room is it moved 4.4 east, 4.0 north). The
door is in the east wall at y 5.0-5.9, out to the yard; windows in the
east wall at y 2.0-3.4 (the kitchen's) and 7.2-8.6, from 1.0 to 1.9 high.
A partition at y 3.6 closes off the kitchen to the north, with the serving
hatch and counter at x 1.8-4.2 and a doorway at x 5.3-6.2. The range is on
the kitchen's north wall at x 3.5-4.5. The two long tables run north-south
at x 2.3 and 4.6, y 6.0-9.6.

Moving: steam off the stew pot, the range's fire behind its door, flies
over the plates and over the cook, the bulb over the hatch sagging now and
then.
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
from mathutils import Matrix, Vector  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 6.4, 1.0, 10.0, 2.8
DOOR = (5.0, 5.9)
WINDOWS = [(2.0, 3.4), (7.2, 8.6)]
WZ = (1.0, 1.9)
PART = 3.6            # the partition's line
HATCH = (1.8, 4.2)    # the serving hatch along the partition
KDOOR = (5.3, 6.2)    # the doorway into the kitchen
TABLES = (2.3, 4.6)
TY = (6.0, 9.6)
RANGE = (3.5, 4.5)
POT = (3.75, 1.45)


def cyl(verts, faces, centre, r, h, seg=12, tilt=None):
    """A closed cylinder (a plate, a cup, a bowl) added to one mesh's lists."""
    c = Vector(centre)
    k = len(verts)
    rot = tilt.to_matrix() if tilt else Matrix.Identity(3)
    for z in (0.0, h):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append(tuple(c + rot @ Vector((math.cos(a) * r, math.sin(a) * r, z))))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((k + i, k + j, k + seg + j, k + seg + i))
    faces.append(tuple(k + seg + i for i in range(seg)))
    faces.append(tuple(k + i for i in reversed(range(seg))))


def smoke_mat(name, density=0.5, rgb=(0.7, 0.7, 0.7)):
    """Steam: a volume, thin and torn by noise, whose amount the Anim turns."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*rgb, 1)
    n = reb.noise_tex(nodes, links, 4.0, 4, 0.6)
    tc = nodes.new("ShaderNodeTexCoord")
    grad = nodes.new("ShaderNodeVectorMath")
    grad.operation = "LENGTH"
    links.new(tc.outputs["Object"], grad.inputs[0])
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 0.5
    edge.inputs["From Max"].default_value = 0.1
    links.new(grad.outputs["Value"], edge.inputs["Value"])
    wisp = nodes.new("ShaderNodeMapRange")
    wisp.inputs["From Min"].default_value = 0.4
    wisp.inputs["From Max"].default_value = 0.7
    links.new(n.outputs["Fac"], wisp.inputs["Value"])
    both = nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    links.new(edge.outputs["Result"], both.inputs[0])
    links.new(wisp.outputs["Result"], both.inputs[1])
    amount = nodes.new("ShaderNodeMath")
    amount.operation = "MULTIPLY"
    amount.inputs[1].default_value = density
    links.new(both.outputs[0], amount.inputs[0])
    links.new(amount.outputs[0], vol.inputs["Density"])
    links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    return m, amount.inputs[1]


def steam(name, base, puffs=5, rise=0.9, drift=(0.15, 0.25), size=(0.15, 0.5), density=8.0):
    parts = []
    for i in range(puffs):
        m, amount = smoke_mat(f"{name} {i}", density)
        ob = reb.prim("sphere", f"{name} puff {i}", m, base, (1, 1, 1.2), segments=10)
        parts.append((ob, amount, i / puffs))

    def f(k):
        for ob, amount, off in parts:
            t = (k / 16 + off) % 1.0
            ob.location = (base[0] + drift[0] * t, base[1] + drift[1] * t, base[2] + rise * t)
            s = size[0] + (size[1] - size[0]) * t
            ob.scale = (s, s, s)
            amount.default_value = density * math.sin(math.pi * t) ** 0.7
    f(0)
    return f


def kitchen_things(rng, enamel, table_m, frame_m, rx):
    """What a camp kitchen has: a galvanised tub on a washstand full of
    dirty dishes, stacks of plates and mugs, tins and coffee on the shelf
    over it, utensils on a rail by the range, a frying pan and a coffee pot
    on the hot plate, a bin of potatoes, a tea towel, a crate of tins."""
    galv = reb.mat_metal("Galvanised", (0.32, 0.33, 0.32), 0.45)
    # The washstand between the range and the sacks: the tub on it, full of
    # dirty dishes, plates draining on the board beside it, the tea towel.
    ws = kit.table("Washstand", table_m, (4.85, 1.3, 0.0), size=(0.6, 0.55, 0.82))
    reb.mask(reb.wall(ws))
    reb.prim("cyl", "Wash tub", galv, (4.8, 1.3, 0.95), (0.5, 0.42, 0.26), segments=20)
    reb.prim("cyl", "Grey water", reb.mat_plain("Dishwater", (0.12, 0.11, 0.09), 0.2), (4.8, 1.3, 1.05), (0.46, 0.38, 0.01), segments=20)
    for i in range(4):
        reb.prim("cyl", f"Plate in the tub {i}", enamel, (4.72 + i * 0.06, 1.3, 1.08), (0.24, 0.24, 0.02), rot=(0, 1.2, 0), segments=14)
    for i in range(3):
        reb.prim("cyl", f"Mug in the tub {i}", reb.mat_plain("Mug blue", (0.1, 0.15, 0.3), 0.35), (4.7 + i * 0.1, 1.42, 1.07), (0.09, 0.09, 0.1), rot=(0.6, 0, i), segments=10)
    for i in range(5):
        reb.prim("cyl", f"Plate draining {i}", enamel, (5.04 + i * 0.012, 1.48, 0.95), (0.24, 0.24, 0.015), rot=(0, 1.35, 0.1), segments=14)
    reb.cloth("Tea towel", mat("flannel"), (5.15, 1.56, 0.62), (0.03, 0.4), rot=(0, math.pi / 2, math.pi / 2), cuts=6, lumps=0.02, seed=8)
    # A shelf over the table: plates stacked, mugs, tins, the coffee can.
    reb.prim("cube", "Plate shelf", frame_m, (X0 + 0.15, 2.3, 1.55), (0.3, 1.3, 0.03))
    for j, y in enumerate((1.85, 2.15)):
        for k in range(10):
            reb.prim("cyl", f"Stacked plate {j}{k}", enamel, (X0 + 0.15, y, 1.58 + k * 0.022), (0.24, 0.24, 0.018), segments=14)
    mug = reb.mat_plain("Mug blue", (0.1, 0.15, 0.3), 0.35)
    for k in range(5):
        reb.prim("cyl", f"Shelf mug {k}", mug, (X0 + 0.15, 2.4 + k * 0.1, 1.61), (0.09, 0.09, 0.1), segments=10)
    for k, rgb in enumerate(((0.4, 0.1, 0.05), (0.15, 0.25, 0.4), (0.45, 0.35, 0.08), (0.4, 0.1, 0.05))):
        reb.prim("cyl", f"Tin of stores {k}", reb.mat_plain(f"Tin label {k}", rgb, 0.6), (X0 + 0.15, 2.65 + k * 0.08 - 0.1 * (k > 1), 1.62 + 0.13 * (k > 1)), (0.08, 0.08, 0.12), segments=10)
    reb.prim("cyl", "Coffee can", reb.mat_plain("Coffee can red", (0.35, 0.05, 0.03), 0.5), (X0 + 0.15, 2.9, 1.64), (0.15, 0.15, 0.18), segments=12)
    # The kitchen shelves' stock, shelf by shelf: the big pots, the plates
    # stacked, the mugs, tins of stores, jars and the coffee.
    sy = Y0 + 0.18
    for k, (x, r, h) in enumerate(((1.4, 0.2, 0.3), (1.85, 0.17, 0.24), (2.2, 0.12, 0.2))):
        reb.prim("cyl", f"Stock pot {k}", mat("steel"), (x, sy, 0.1125 + h / 2), (2 * r, 2 * r, h), segments=16)
    for k, x in enumerate((1.3, 1.55, 1.8, 2.05)):
        for j in range(8 - k):
            reb.prim("cyl", f"Shelf plate {k}{j}", enamel, (x, sy, 0.565 + j * 0.022), (0.22, 0.22, 0.018), segments=14)
    for k in range(9):
        reb.prim("cyl", f"Shelf mug {k}", reb.mat_plain("Mug blue", (0.1, 0.15, 0.3), 0.35), (1.25 + k * 0.12, sy + 0.05 * (k % 2), 1.04), (0.09, 0.09, 0.1), segments=10)
    labels = [reb.mat_plain(f"Tin label {k}", rgb, 0.6) for k, rgb in enumerate(((0.4, 0.1, 0.05), (0.15, 0.25, 0.4), (0.45, 0.35, 0.08)))]
    for k in range(10):
        reb.prim("cyl", f"Tin {k}", labels[k % 3], (1.25 + k * 0.11, sy + 0.04 * (k % 2), 1.5), (0.09, 0.09, 0.13), segments=10)
    for k in range(4):
        reb.prim("cyl", f"Jar {k}", mat("glass"), (1.3 + k * 0.16, sy, 1.95), (0.1, 0.1, 0.18), segments=10)
    reb.prim("cyl", "Coffee can, big", reb.mat_plain("Coffee can red", (0.35, 0.05, 0.03), 0.5), (2.05, sy, 1.96), (0.18, 0.18, 0.2), segments=12)
    reb.prim("cube", "Flour box", mat("old paper"), (2.25, sy, 1.95), (0.14, 0.16, 0.18))
    # Utensils on a rail by the range: ladle, spoon, fish slice, a sieve.
    kit.rod("Utensil rail", mat("steel"), (rx + 0.55, Y0 + 0.03, 1.55), (rx + 0.9, Y0 + 0.03, 1.55), 0.01, 6)
    for k in range(4):
        x = rx + 0.59 + k * 0.1
        kit.rod(f"Utensil {k}", mat("steel"), (x, Y0 + 0.05, 1.55), (x, Y0 + 0.05, 1.2 + 0.05 * (k % 2)), 0.008, 6)
        reb.prim("sphere" if k % 2 == 0 else "cube", f"Utensil head {k}", mat("steel"), (x, Y0 + 0.05, 1.17 + 0.05 * (k % 2)), (0.07, 0.03, 0.05), segments=8)
    # On the hot plate: a frying pan of fat and the coffee pot.
    reb.prim("cyl", "Frying pan", mat("iron"), (rx + 0.2, Y0 + 0.62, 0.91), (0.32, 0.32, 0.04), segments=16)
    kit.rod("Pan handle", mat("iron"), (rx + 0.2, Y0 + 0.78, 0.92), (rx + 0.25, Y0 + 1.0, 0.94), 0.015, 6)
    reb.prim("cyl", "Fat in the pan", reb.mat_plain("Cold fat", (0.45, 0.4, 0.3), 0.4), (rx + 0.2, Y0 + 0.62, 0.925), (0.28, 0.28, 0.01), segments=16)
    reb.prim("cone", "Coffee pot", reb.mat_metal("Enamel blue", (0.08, 0.12, 0.25), 0.35), (rx + 0.05, Y0 + 0.12, 1.01), (0.18, 0.18, 0.24), top=0.6)
    # Stores: a bin of potatoes, a crate of tins, a sack of coffee.
    reb.prim("cube", "Potato bin", table_m, (4.95, 3.1, 0.25), (0.5, 0.4, 0.5), bevel=0.01)
    pv, pf = [], []
    for _ in range(14):
        reb.boulder(rng, (4.95 + rng.uniform(-0.18, 0.18), 3.1 + rng.uniform(-0.14, 0.14), 0.5), 0.05, pv, pf, squash=0.8, subdivisions=2)
    reb.mesh_object("Potatoes", pv, pf, reb.mat_plain("Potato", (0.35, 0.27, 0.15), 0.8), smooth=True)
    kit.crate("Crate of tins", table_m, (4.45, 3.15, 0.0), size=(0.5, 0.4, 0.35))
    for k in range(6):
        reb.prim("cyl", f"Tin in the crate {k}", mat("steel"), (4.3 + (k % 3) * 0.13, 3.08 + (k // 3) * 0.14, 0.38), (0.08, 0.08, 0.1), segments=10)
    reb.wall(reb.prim("cube", "Stores footprint", None, (4.7, 3.12, 0.3), (1.05, 0.45, 0.6))).hide_render = True
    # The cook's list of shifts.
    reb.prim("cube", "Shift list", mat("old paper"), (X0 + 0.01, 1.5, 1.45), (0.006, 0.25, 0.32))


def build():
    rng = random.Random(31)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("boards")
    room.camera((6.25, 9.85, 2.45), (2.9, 4.6, 0.6), 200, "high in the south-east corner: the tables, the benches over, the cook against the counter")
    room.camera((1.15, 9.85, 2.45), (4.8, 4.6, 0.6), 200, "high in the south-west corner: the length of the hall to the hatch, the door on the right")
    room.camera((6.25, 3.8, 2.45), (2.6, 8.4, 0.5), 200, "high by the kitchen doorway: the last meal on the tables, the fork in the board")
    room.camera((1.15, 3.45, 2.45), (5.0, 1.3, 0.6), 200, "high in the kitchen's south-west corner: the range, the steaming pot, the block")

    # ---- Materials.
    walls_m = kit.boards("Whitewashed boards", (0.42, 0.4, 0.35), width=0.18, grime=0.85)
    floor_m = kit.dirtied(mat("planks"), 0.8, scale=1.2)
    ceil_m = kit.boards("Mess ceiling", (0.45, 0.43, 0.38), width=0.16, grime=0.4)
    frame_m = mat("dark wood")
    table_m = reb.mat_wood("Table boards", (0.3, 0.22, 0.13))
    enamel = reb.mat_plain("Enamel plate", (0.55, 0.56, 0.52), 0.35)
    stew = reb.mat_plain("Stew", (0.13, 0.06, 0.02), 0.3)
    bread = reb.mat_plain("Bread", (0.45, 0.3, 0.14), 0.9)
    apron = reb.mat_surface("Apron", [(0.0, (0.5, 0.48, 0.42)), (0.7, (0.45, 0.42, 0.36)), (0.85, (0.25, 0.02, 0.01)), (1.0, (0.12, 0.005, 0.004))], scale=9, bump=0.2)
    range_m = reb.mat_metal("Range iron", (0.05, 0.05, 0.05), 0.5)
    # Blood gone into the boards: dark, brown-red, matte, never a red puddle.
    soaked = reb.mat_surface("Soaked blood", [(0.0, (0.02, 0.006, 0.004)), (0.5, (0.045, 0.012, 0.007)), (0.8, (0.07, 0.025, 0.014)), (1.0, (0.05, 0.03, 0.02))], scale=25, detail=8, rough=0.92, bump=0.1)

    # ---- The shell: whitewashed boards, the partition with its hatch and doorway.
    kit.walls(X0, Y0, X1, Y1, H, walls_m, openings=[("e", DOOR[0], DOOR[1], 0.0, 2.1)] + [("e", a, b, WZ[0], WZ[1]) for a, b in WINDOWS], ceiling=ceil_m)
    kit.plank_floor(X0 - 0.1, Y0 - 0.1, X1 + 0.1, Y1 + 0.1, floor_m, along="y", seed=5)
    for y in (2.2, 4.6, 7.0, 9.2):
        reb.prim("cube", "Ceiling beam", frame_m, ((X0 + X1) / 2, y, H - 0.08), (X1 - X0, 0.12, 0.16))
    part = []
    for (a, b, z0, z1) in ((X0, HATCH[0], 0, H), (HATCH[0], HATCH[1], 0, 0.95), (HATCH[0], HATCH[1], 1.85, H), (HATCH[1], KDOOR[0], 0, H), (KDOOR[0], KDOOR[1], 2.1, H), (KDOOR[1], X1, 0, H)):
        part.append(reb.prim("cube", "Partition", walls_m, ((a + b) / 2, PART, (z0 + z1) / 2), (b - a, 0.1, z1 - z0)))
    for (a, b) in ((X0, HATCH[0]), (HATCH[1], KDOOR[0]), (KDOOR[1], X1)):
        reb.wall(reb.prim("cube", "Partition footprint", None, ((a + b) / 2, PART, 0.5), (b - a, 0.12, 1.0))).hide_render = True
    counter = reb.prim("cube", "Serving counter", table_m, (sum(HATCH) / 2, PART, 0.96), (HATCH[1] - HATCH[0] + 0.1, 0.5, 0.05))
    reb.mask(reb.wall(reb.prim("cube", "Counter footprint", None, (sum(HATCH) / 2, PART, 0.5), (HATCH[1] - HATCH[0], 0.5, 1.0)))).hide_render = True
    reb.prim("cube", "Hatch shutter, up", table_m, (sum(HATCH) / 2, PART - 0.02, 2.0), (HATCH[1] - HATCH[0], 0.04, 0.3), rot=(0.3, 0, 0))
    for x in (KDOOR[0] - 0.04, KDOOR[1] + 0.04):
        reb.prim("cube", "Kitchen door frame", frame_m, (x, PART, 1.05), (0.08, 0.14, 2.1))
    # Windows and the door out to the yard.
    glass_m = reb.mat_glass("Steamy glass", (0.5, 0.48, 0.42))
    for i, (a, b) in enumerate(WINDOWS):
        reb.prim("cube", f"Window glass {i}", glass_m, (X1 + 0.06, (a + b) / 2, sum(WZ) / 2), (0.01, b - a, WZ[1] - WZ[0]))
        reb.prim("cube", "Window bar", frame_m, (X1 + 0.03, (a + b) / 2, sum(WZ) / 2), (0.04, 0.04, WZ[1] - WZ[0]))
        reb.prim("cube", "Window sill", frame_m, (X1 - 0.04, (a + b) / 2, WZ[0] - 0.02), (0.1, b - a + 0.1, 0.04))
    for y in (DOOR[0] - 0.04, DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", frame_m, (X1 + 0.04, y, 1.08), (0.16, 0.08, 2.16))
    reb.prim("cube", "Door head", frame_m, (X1 + 0.04, sum(DOOR) / 2, 2.14), (0.16, DOOR[1] - DOOR[0] + 0.16, 0.08))
    # The door, shut: whitewashed ledged boards, a latch.
    door_m = kit.boards("Door boards", (0.4, 0.38, 0.33), width=0.15, grime=0.85)
    reb.prim("cube", "Door, shut", door_m, (X1 + 0.03, sum(DOOR) / 2, 1.04), (0.05, DOOR[1] - DOOR[0], 2.08))
    for z in (0.3, 1.0, 1.75):
        reb.prim("cube", "Door ledge", frame_m, (X1 - 0.0, sum(DOOR) / 2, z), (0.03, DOOR[1] - DOOR[0] - 0.06, 0.12))
    reb.prim("cube", "Door latch", mat("iron"), (X1 - 0.02, DOOR[0] + 0.12, 1.05), (0.03, 0.16, 0.04))

    # ---- Outside: the yard, moved 4.4 east and 4 north from its own plan.
    reb.prim("cube", "Outside, mud", kit.dirtied(mat("mud"), 0.6), (16.0, 5.0, -0.1), (20, 30, 0.2))
    reb.prim("cube", "Outside, step", mat("planks"), (X1 + 0.3, sum(DOOR) / 2, 0.06), (0.5, 1.3, 0.14))
    kit.rod("Outside, bell post", mat("dark wood"), (7.6, 3.3, 0), (7.6, 3.3, 2.9), 0.07)
    kit.rod("Outside, bell arm", mat("dark wood"), (7.6, 3.3, 2.75), (7.6, 3.95, 2.75), 0.04)
    reb.prim("cone", "Outside, bell", reb.mat_metal("Bell bronze", (0.45, 0.3, 0.12), 0.4), (7.6, 3.85, 2.5), (0.42, 0.42, 0.38), top=0.45)
    tarp = reb.mat_surface("Tarp", [(0.0, (0.1, 0.11, 0.07)), (1.0, (0.2, 0.2, 0.13))], scale=6, bump=0.3)
    for i, x in enumerate((7.35, 8.35)):
        reb.cloth(f"Outside, canvas {i}", tarp, (x, 7.65, 0.22), (0.95, 1.45), cuts=10, lumps=0.07, seed=60 + i)
        reb.prim("cube", f"Outside, boots {i}", mat("rubber"), (x, 6.75, 0.08), (0.25, 0.14, 0.16))
    reb.prim("cube", "Outside, skidder", reb.mat_plain("Skidder yellow", (0.45, 0.3, 0.03), 0.6), (12.4, 9.0, 1.2), (4.4, 2.4, 2.0))
    reb.prim("cyl", "Outside, fire ring", reb.mat_plain("Ash", (0.1, 0.1, 0.1), 0.9), (13.4, 4.3, 0.04), (2.2, 2.2, 0.1), segments=16)
    reb.prim("cube", "Outside, bunkhouse", kit.boards("Bunkhouse boards", (0.17, 0.11, 0.07), width=0.22), (15.9, -4.9, 1.2), (11.2, 5.2, 2.4))
    reb.prim("cube", "Outside, office", kit.boards("Office boards", (0.08, 0.14, 0.09), width=0.16), (7.2, -1.9, 1.25), (3.8, 3.2, 2.5))
    reb.prim("cube", "Outside, logs", mat("bark"), (19.4, -0.5, 0.9), (4.8, 2.2, 1.8))
    reb.prim("cube", "Outside, sawmill", kit.boards("Mill boards", (0.2, 0.19, 0.17), width=0.3), (28.0, 3.4, 3.0), (10.0, 9.6, 6.0))
    reb.prim("cube", "Outside, far trees", reb.mat_plain("Far trees", (0.05, 0.07, 0.05), 0.9), (40, 5, 8), (1, 80, 16))

    # ---- The kitchen: the range with the stew still on it, the block and cleaver, shelves, sacks.
    rx = sum(RANGE) / 2
    rng_ob = kit.box("Range", range_m, (rx, Y0 + 0.38, 0.0), (RANGE[1] - RANGE[0], 0.75, 0.85), bevel=0.02)
    reb.mask(reb.wall(rng_ob))
    reb.prim("cube", "Range top", mat("iron"), (rx, Y0 + 0.38, 0.87), (RANGE[1] - RANGE[0] + 0.04, 0.78, 0.04))
    reb.prim("cube", "Range rail", mat("steel"), (rx, Y0 + 0.79, 0.75), (RANGE[1] - RANGE[0], 0.03, 0.03))
    fire_m = reb.mat_emit("Range fire", (1.0, 0.35, 0.06), 6)
    reb.prim("cube", "Firebox door, ajar", mat("iron"), (rx + 0.32, Y0 + 0.85, 0.35), (0.25, 0.02, 0.22), rot=(0, 0, 0.7))
    reb.prim("cube", "Firebox", fire_m, (rx + 0.25, Y0 + 0.765, 0.35), (0.22, 0.01, 0.18))
    fire = reb.point("Range fire light", (rx + 0.25, Y0 + 1.0, 0.4), 18, (1.0, 0.4, 0.1), 0.15)
    kit.rod("Flue", mat("rust"), (rx, Y0 + 0.3, 0.9), (rx, Y0 + 0.3, H), 0.09)
    pot_v, pot_f = [], []
    cyl(pot_v, pot_f, (POT[0], POT[1], 0.89), 0.2, 0.3, seg=16)
    reb.mesh_object("Stew pot", pot_v, pot_f, mat("iron"), smooth=False)
    reb.prim("cyl", "Stew in the pot", stew, (POT[0], POT[1], 1.16), (0.37, 0.37, 0.02), segments=16)
    kit.rod("Ladle", mat("steel"), (POT[0] + 0.05, POT[1], 1.1), (POT[0] + 0.3, POT[1] + 0.1, 1.45), 0.012, 6)
    reb.prim("cyl", "Kettle", mat("steel"), (rx + 0.3, Y0 + 0.3, 0.98), (0.2, 0.2, 0.18), segments=12)
    kit.splat("Stew down the range", stew, (rx - 0.35, Y0 + 0.77, 0.6), 0.08, rot=(math.pi / 2, 0, 0), seed=2, stretch=(0.6, 2.4))
    steam_f = steam("Steam", (POT[0], POT[1], 1.3))
    # The work table and the block, the cleaver gone from it.
    wt = kit.table("Kitchen table", table_m, (1.65, 2.55, 0.0), size=(0.9, 1.4, 0.85), rot=0.0)
    reb.mask(reb.wall(wt))
    reb.prim("cyl", "Butcher block", mat("logs"), (2.75, 1.8, 0.4), (0.6, 0.6, 0.8), segments=14)
    reb.wall(reb.prim("cyl", "Block footprint", None, (2.75, 1.8, 0.4), (0.6, 0.6, 0.8)), "circle").hide_render = True
    kit.splat("Block blood", soaked, (2.75, 1.8, 0.805), 0.15, seed=3)
    reb.prim("cube", "Side of meat", reb.mat_plain("Meat", (0.35, 0.08, 0.06), 0.5), (1.6, 2.4, 0.92), (0.5, 0.3, 0.12), bevel=0.04)
    kit.splat("Meat juice", soaked, (1.65, 2.7, 0.851), 0.2, seed=4)
    for i in range(3):
        reb.prim("cube", f"Onion {i}", reb.mat_plain("Onion", (0.5, 0.38, 0.2), 0.6), (1.5 + i * 0.12, 3.0, 0.9), (0.08, 0.08, 0.08))
    reb.mask(reb.wall(kit.shelves("Kitchen shelves", frame_m, (1.75, Y0 + 0.18, 0.0), size=(1.2, 0.3, 1.9), rows=5, clutter=0.0, seed=6)))
    for i, (x, y) in enumerate(((5.4, 1.4), (5.8, 1.35), (5.6, 1.8))):
        reb.prim("cube", f"Flour sack {i}", mat("canvas"), (x, y, 0.3), (0.45, 0.35, 0.6), rot=(0, 0, rng.uniform(-0.3, 0.3)), bevel=0.1)
    reb.wall(reb.prim("cube", "Sacks footprint", None, (5.6, 1.6, 0.3), (0.95, 0.9, 0.6))).hide_render = True
    for i in range(3):
        kit.rod(f"Pan hook {i}", mat("iron"), (2.65 + i * 0.27, 1.05, 2.3), (2.65 + i * 0.27, 1.1, 1.9), 0.008, 4)
        reb.prim("cyl", f"Hanging pan {i}", mat("iron"), (2.65 + i * 0.27, 1.12, 1.75), (0.26 - i * 0.03, 0.04, 0.26 - i * 0.03), rot=(math.pi / 2, 0, 0), segments=14)
    reb.wall(reb.prim("cube", "Water barrel", mat("logs"), (6.12, 2.3, 0.45), (0.6, 0.6, 0.9), bevel=0.15), "circle")
    kitchen_things(rng, enamel, table_m, frame_m, rx)

    # ---- The counter: the cook, dead against it in his apron, keys on his belt, the cleaver by his hand.
    ck = (3.0, PART + 0.27, 0.0)
    kit.body("The cook", ck, heading=math.pi / 2, pose="slumped", top=apron, legs=reb.mat_plain("Cook's trousers", (0.25, 0.24, 0.22), 0.9), seed=12)
    # The office key, off the ring on his belt (office-key).
    room.item("office-key", (ck[0], ck[1] + 0.7, 0.0))
    reb.prim("cube", "Apron bib", apron, (ck[0], ck[1] + 0.2, 0.55), (0.36, 0.02, 0.5), rot=(0.25, 0, 0))
    hip = Vector((ck[0] - 0.2, ck[1] + 0.25, 0.2))
    kit.rod("Key ring", mat("steel"), hip, hip + Vector((0.0, 0.0, -0.08)), 0.03, 10)
    for i in range(4):
        reb.prim("cube", f"Key {i}", reb.mat_metal("Key brass", (0.55, 0.42, 0.15), 0.3), hip + Vector((-0.03 + i * 0.02, 0.02, -0.12 - (i % 2) * 0.02)), (0.012, 0.004, 0.07), rot=(0, (i - 1.5) * 0.25, 0))
    reb.prim("cube", "Cleaver blade", mat("steel"), (ck[0] + 0.55, ck[1] + 0.45, 0.012), (0.2, 0.1, 0.01), rot=(0, 0, 0.4))
    reb.prim("cube", "Cleaver handle", reb.mat_wood("Cleaver handle", (0.18, 0.1, 0.05)), (ck[0] + 0.72, ck[1] + 0.53, 0.015), (0.14, 0.03, 0.025), rot=(0, 0, 0.4))
    kit.splat("Under the cook", soaked, (ck[0], ck[1] + 0.35, 0.0), 0.32, seed=13, stretch=(1.3, 1.0), lumps=0.6)
    kit.splat("Down the counter", soaked, (ck[0] + 0.1, PART + 0.255, 0.75), 0.15, rot=(math.pi / 2, 0, 0), seed=14, stretch=(0.6, 1.6))
    kit.splat("Hand on the counter", soaked, (ck[0] + 0.5, PART + 0.1, 0.988), 0.07, seed=15)
    for i in range(6):
        reb.prim("cyl", f"Serving bowl {i}", enamel, (2.0 + i * 0.36, PART - 0.05, 1.02), (0.18, 0.18, 0.08), segments=12)
    reb.prim("cube", "Bread on the counter", bread, (3.9, PART + 0.1, 1.04), (0.3, 0.14, 0.12), bevel=0.04)

    # ---- The hall: two long tables, the last meal, the fight.
    for tx in TABLES:
        t = kit.table(f"Long table {tx}", table_m, (tx, sum(TY) / 2, 0.0), size=(0.9, TY[1] - TY[0], 0.76))
        reb.mask(reb.wall(t))
    benches = [  # (x, y, tipped, yaw)
        (TABLES[0] - 0.75, sum(TY) / 2, False, 0.0), (TABLES[0] + 0.75, sum(TY) / 2 + 0.4, True, 0.15),
        (TABLES[1] - 0.75, sum(TY) / 2 - 0.5, True, -0.25), (TABLES[1] + 0.75, sum(TY) / 2, False, 0.04),
    ]
    for i, (bx, by, tipped, yaw) in enumerate(benches):
        legs = []
        for dy in (-1.4, 1.4):
            legs.append(reb.prim("cube", "bench leg", table_m, (0, dy, 0.22), (0.3, 0.06, 0.44)))
        legs.append(reb.prim("cube", "bench seat", table_m, (0, 0, 0.45), (0.32, 3.2, 0.05)))
        b = kit.join(f"Bench {i}", legs, origin=(0, 0, 0))
        if tipped:
            b.location = (bx + 0.25, by, 0.16)
            b.rotation_euler = (0, math.pi / 2 * (1 if bx > sum(TABLES) / 2 else -1), yaw)
        else:
            b.location = (bx, by, 0.0)
            b.rotation_euler = (0, 0, yaw)
        reb.mask(reb.wall(b))
    # Thrown to the far end of the aisle between the tables, clear of the
    # way round the cook to the hatch.
    kit.chair("Chair thrown", table_m, (3.45, 9.6, 0.0), rot=1.0, tipped=True)
    pv, pf, sv, sf, cv, cf = [], [], [], [], [], []
    for tx in TABLES:
        for side in (-1, 1):
            for k in range(6):
                y = TY[0] + 0.35 + k * 0.58 + rng.uniform(-0.05, 0.05)
                x = tx + side * 0.25 + rng.uniform(-0.04, 0.04)
                if rng.random() < 0.12:
                    continue
                cyl(pv, pf, (x, y, 0.762), 0.12, 0.02, seg=14)
                if rng.random() < 0.75:
                    cyl(sv, sf, (x, y, 0.775), 0.09, 0.008, seg=12)
                cyl(cv, cf, (x + side * 0.15, y + 0.15, 0.762), 0.045, 0.09, seg=10)
    reb.mesh_object("Plates", pv, pf, enamel, smooth=False)
    reb.mesh_object("Stew on the plates", sv, sf, stew, smooth=False)
    reb.mesh_object("Mugs", cv, cf, reb.mat_plain("Mug blue", (0.1, 0.15, 0.3), 0.35), smooth=False)
    # Broken plates on the floor, a plate on its edge, spilled stew, cutlery.
    bv, bf = [], []
    for i in range(10):
        c = Vector((3.4 + rng.gauss(0, 0.4), 6.6 + rng.gauss(0, 0.6), 0.003))
        a = rng.uniform(0, 6.3)
        k = len(bv)
        bv += [tuple(c), tuple(c + Vector((math.cos(a), math.sin(a), 0)) * 0.1), tuple(c + Vector((math.cos(a + 0.9), math.sin(a + 0.9), 0)) * 0.1)]
        bf.append((k, k + 1, k + 2))
    reb.mesh_object("Broken plates", bv, bf, enamel, smooth=False)
    for i in range(3):
        kit.splat(f"Spilled stew {i}", stew, (3.3 + rng.uniform(-0.4, 0.4), 6.4 + rng.uniform(-0.5, 1.2), 0.0), rng.uniform(0.1, 0.2), seed=20 + i)
    reb.prim("cube", "Bread loaf", bread, (TABLES[0], 7.5, 0.82), (0.32, 0.16, 0.12), bevel=0.04)
    reb.prim("cube", "Bread knife", mat("steel"), (TABLES[0] + 0.15, 7.75, 0.765), (0.25, 0.02, 0.005), rot=(0, 0, 0.6))
    # The fork driven into the board, the smear where someone went across the table.
    kit.rod("Fork in the board", mat("steel"), (TABLES[1] - 0.05, 7.2, 0.76), (TABLES[1] + 0.05, 7.15, 0.95), 0.006, 6)
    kit.drag_trail("Dragged across the table", soaked, [(TABLES[1] - 0.3, 8.3), (TABLES[1], 8.0), (TABLES[1] + 0.35, 7.7)], width=0.2, seed=25, z=0.762)
    kit.splat("Blood off the table", soaked, (TABLES[1] + 0.7, 7.8, 0.0), 0.18, seed=26, stretch=(1.2, 0.9), lumps=0.6)
    kit.drag_trail("Out of the door", soaked, [(TABLES[1] + 0.7, 7.5), (5.6, 6.6), (6.1, 5.6), (X1, 5.45)], width=0.16, seed=27)
    kit.bottles("Bottles", (TABLES[0], 8.8, 0.76), count=3, spread=0.3, seed=7, tipped=0.6)
    # The menu board on the west wall; coat hooks with coats nobody came back for.
    reb.prim("cube", "Menu board", reb.mat_surface("Chalkboard", [(0.0, (0.04, 0.06, 0.05)), (1.0, (0.1, 0.12, 0.1))], scale=6, rough=0.9, bump=0.05), (X0 + 0.02, 5.0, 1.6), (0.02, 1.0, 0.7))
    chalk = reb.mat_plain("Chalk", (0.62, 0.62, 0.58), 0.95)
    for i, line in enumerate(("THURS 23", "STEW", "BREAD", "NO SECONDS")):
        kit.text(f"Menu {i}", line, chalk, (X0 + 0.035, 5.0, 1.82 - i * 0.14), size=0.09, rot=(math.pi / 2, 0, math.pi / 2))
    reb.prim("cube", "Coat hooks", frame_m, (X0 + 0.02, 8.0, 1.75), (0.03, 1.4, 0.08))
    for i, y in enumerate((7.5, 7.95, 8.4)):
        reb.cloth(f"Coat {i}", mat("flannel") if i != 1 else mat("canvas"), (X0 + 0.08, y, 1.3), (0.5, 0.85), rot=(math.pi / 2, 0, math.pi / 2), cuts=8, lumps=0.04, seed=i)
    reb.prim("cube", "Notice", mat("paper"), (X0 + 0.015, 6.0, 1.5), (0.006, 0.22, 0.3))
    kit.text("Notice words", "WASH HANDS", mat("black"), (X0 + 0.022, 6.0, 1.58), size=0.035, rot=(math.pi / 2, 0, math.pi / 2))

    # ---- Light: grey noon through the east windows and the door, the range fire, the bulb over the hatch.
    kit.time_light("noon", sun_heading=200, sun_energy=1.5, sky=((0.5, 0.52, 0.54), (0.36, 0.39, 0.43), 0.8))
    for i, (a, b) in enumerate(WINDOWS):
        reb.spot(f"Window light {i}", (X1 - 0.15, (a + b) / 2, 1.8), (X1 - 2.6, (a + b) / 2 + 0.3, 0.0), 160, (0.72, 0.78, 0.88), 110, 0.9, 0.5)
    cord, glass, bulb, glow = kit.bulb("Hatch bulb", (3.0, 4.6, H - 0.02), energy=70, rgb=(1.0, 0.72, 0.42), flex=0.12)
    reb.point("Hall fill", (3.6, 8.0, 1.6), 40, (0.6, 0.65, 0.75), 1.0)
    reb.point("Kitchen fill", (3.0, 2.4, 2.4), 20, (1.0, 0.7, 0.45), 0.8)

    anim = kit.Anim(16)
    anim.custom(steam_f)
    anim.flicker(fire, fire_m, depth=0.35, dropouts=0)
    anim.dips(bulb, glow)
    anim.flies((TABLES[0], 7.0, 0.8), count=8, radius=0.45)
    anim.flies((TABLES[1], 8.2, 0.8), count=7, radius=0.4)
    anim.flies((ck[0] + 0.3, ck[1] + 0.3, 0.4), count=9, radius=0.35)

    # ---- What the game needs.
    room.door("camp-yard", (X1 - 0.5, DOOR[0], X1, DOOR[1]), arrive=(5.0, 5.45), face=(-1, 0))
    room.check((ck[0] - 0.7, ck[1] + 0.5, ck[0] + 0.7, ck[1] + 1.1), "The cook, in his apron. He died holding the counter.\nThere's a ring of keys on his belt. One is tagged OFFICE.")
    room.check((ck[0] + 0.4, ck[1] + 0.4, ck[0] + 1.0, ck[1] + 0.9), "A meat cleaver. He didn't go down without a fight.")
    room.check((2.8, 1.85, 4.6, 2.3), "Stew, still simmering on the range. Someone kept the fire going.\nIt doesn't smell like food any more.")
    room.check((TABLES[1] + 0.45, 6.6, TABLES[1] + 1.0, 8.4), "A fork, driven into the table. Blood across the boards.\nThey turned on each other over dinner.")
    room.check((TABLES[0] + 0.45, 6.6, TABLES[0] + 1.0, 8.6), "Plates of stew, half eaten. Flies.")
    room.check((X0, 4.5, X0 + 0.6, 5.5), "THURS 23. STEW. BREAD. NO SECONDS.\nYesterday.")
    room.check((1.9, 4.1, 2.5, 4.6), "The serving hatch. The kitchen's through there.")
    # Many scenes share the render machine's GPU: keep each frame cheap.
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    scene.cycles.volume_step_rate = 4.0
    scene.cycles.volume_max_steps = 64
    room.export(anim, samples=160)


build()
