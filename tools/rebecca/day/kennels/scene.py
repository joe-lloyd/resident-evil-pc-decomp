"""The Spencer estate's kennels, inside the back gate, at night.

What it tells: this is where the dogs on the mountain came from. Four
chain-link runs stand along the west side, each with its doghouse and its
name board, and every run's gate has been torn open from inside: one
hangs off a single hinge, one lies flat in the gravel, the wire bellied
outward. The chains that held them are snapped at the collar end. The
straw in the runs is soaked dark, gnawed bones lie among the steel bowls,
and their paw prints run out across the yard, north to the back gate and
south toward the house. Their handler is in the third run, in what's left
of his grey estate uniform, his catch-pole snapped beside him. His hut's
door stands open and bangs in the wind; his lamp is still lit on the desk
inside, a feed chart on the wall. A sign on the hut: CAUTION - DOGS.

Metres: the floor is x 2-17, y 2-14 at z 0. The estate's back wall runs
along the north at y 1.6 with the back gate at x 9.2-10.8. The runs are
x 2.0-6.5, y 3.5-13.1, four of them 2.4 m wide, each gate in the east fence.
The handler's hut is x 13.0-16.4, y 4.0-7.4, its door in the west wall at
y 5.2-6.1. The path to the back garden leaves through the south edge at
x 9-11, between clipped yews; the mansion's back stands dark beyond.

Moving: the hut's door banging, the yard lamp and the hut's lamp
flickering, a loose chain swinging on the fence.
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
from mathutils import Matrix, Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 2.0, 17.0, 2.0, 14.0
WALL_Y = 1.6
GATE = (9.2, 10.8)
RUNS_X = (2.0, 6.5)
RUN_Y = [3.5, 5.9, 8.3, 10.7, 13.1]
RUN_DOOR = 1.0          # the gate's width in each run's east fence, centred
HUT = (13.0, 16.4, 4.0, 7.4)
HUT_DOOR = (5.2, 6.1)
SOUTH = (9.0, 11.0)


def height(x, y):
    """Flat gravel, dropped under the runs' slab and the hut's floor so it can't poke through."""
    if RUNS_X[0] - 1.0 < x < RUNS_X[1] + 0.2 and RUN_Y[0] - 0.3 < y < RUN_Y[-1] + 0.3:
        return -0.1
    if HUT[0] - 0.1 < x < HUT[1] + 0.1 and HUT[2] - 0.1 < y < HUT[3] + 0.1:
        return -0.1
    return 0.03 * noise.noise(Vector((x * 0.4, y * 0.4, 5)))


def chainlink():
    """Diamond wire mesh you can see through: the wire from a brick
    pattern turned 45 degrees, the holes cut out with alpha."""
    m, nodes, links, bsdf = reb.nodes_material("Chain link")
    bsdf.inputs["Base Color"].default_value = (0.11, 0.11, 0.105, 1)
    bsdf.inputs["Metallic"].default_value = 0.4
    bsdf.inputs["Roughness"].default_value = 0.45
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
    rot = nodes.new("ShaderNodeMapping")
    rot.inputs["Rotation"].default_value = (0, 0, math.radians(45))
    links.new(comb.outputs["Vector"], rot.inputs["Vector"])
    brick = nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 0.06
    brick.inputs["Row Height"].default_value = 0.06
    brick.inputs["Mortar Size"].default_value = 0.005
    brick.offset = 0.0
    links.new(rot.outputs["Vector"], brick.inputs["Vector"])
    links.new(brick.outputs["Fac"], bsdf.inputs["Alpha"])
    return m


def fence(name, m, a, b, h=2.0):
    """A chain-link panel from floor point a to b, on posts, with a top rail."""
    a, b = Vector((*a, 0)), Vector((*b, 0))
    d = b - a
    mid = (a + b) / 2
    p = reb.prim("cube", name, m, (mid.x, mid.y, h / 2), (d.length, 0.01, h), rot=(0, 0, math.atan2(d.y, d.x)))
    kit.rod(f"{name} rail", mat("steel"), (a.x, a.y, h), (b.x, b.y, h), 0.02, 6)
    return reb.wall(p)


def build():
    rng = random.Random(71)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("gravel")
    room.floor((RUNS_X[0], 3.3, 6.8, 13.3), "concrete")  # the runs' slab
    room.floor((HUT[0], HUT[2], HUT[1], HUT[3]), "boards")  # the handler's hut
    room.floor((9.3, Y0, 10.7, Y1), "earth")  # the path from the gate to the house
    room.camera((10.4, 2.3, 3.6), (5.0, 9.6, 0.0), 200, "from inside the back gate: the runs torn open, the paw prints out across the yard")
    room.camera((16.6, 13.6, 3.4), (6.5, 5.5, 0.4), 200, "from the south-east: the yard, the hut's door banging, the runs beyond")
    room.camera((2.2, 14.6, 4.0), (11.0, 4.5, 0.0), 200, "from over the yews behind the last run: the length of the runs, the gate, the hut")
    room.camera((8.6, 9.0, 2.8), (4.4, 9.6, 0.2), 195, "close on the third run: the handler in the straw, the snapped pole")
    room.camera((12.0, 2.6, 3.6), (11.0, 13.5, 0.0), 200, "from inside the gate, east: the yard, the trough, the path south to the yews and the house")

    link_m = chainlink()
    concrete = kit.dirtied(mat("concrete"), 0.8, scale=1.0)
    stone = reb.mat_surface("Estate stone", [(0.0, (0.13, 0.13, 0.125)), (0.6, (0.22, 0.215, 0.2)), (1.0, (0.27, 0.27, 0.25))], scale=3, bump=0.6)
    hut_boards = kit.boards("Hut boards", (0.14, 0.15, 0.1), width=0.14, grime=0.7)
    straw = reb.mat_cards("Straw", (0.2, 0.14, 0.05), (0.42, 0.33, 0.14))
    bloody_straw = reb.mat_cards("Bloody straw", (0.08, 0.01, 0.005), (0.25, 0.08, 0.03))
    uniform = reb.mat_surface("Grey uniform", [(0.0, (0.06, 0.065, 0.07)), (0.75, (0.1, 0.105, 0.11)), (1.0, (0.16, 0.015, 0.01))], scale=8, bump=0.2)
    yew = reb.mat_surface("Clipped yew", [(0.0, (0.008, 0.02, 0.01)), (1.0, (0.03, 0.06, 0.025))], scale=5, bump=1.0)
    dark_stone = reb.mat_plain("Mansion stone", (0.03, 0.03, 0.035), 0.9)
    lit = reb.mat_emit("Lit window", (1.0, 0.6, 0.28), 5)
    sign_m = mat("yellow paint")

    # ---- Ground: gravel yard, the runs' concrete, mud where the dogs went out.
    reb.terrain("Yard", kit.dirtied(mat("gravel"), 0.9, scale=0.6), (-10, 30), (WALL_Y, 40), height, step=0.5)
    reb.prim("cube", "Run slab", concrete, ((RUNS_X[0] + RUNS_X[1]) / 2 - 0.3, (RUN_Y[0] + RUN_Y[-1]) / 2, -0.06), (RUNS_X[1] - RUNS_X[0] + 1.2, RUN_Y[-1] - RUN_Y[0] + 0.4, 0.12))
    reb.prim("cube", "Drain gutter", mat("black"), (RUNS_X[1] - 0.3, (RUN_Y[0] + RUN_Y[-1]) / 2, 0.012), (0.12, RUN_Y[-1] - RUN_Y[0], 0.004))
    kit.path_strip("Path to the house", mat("dirt"), [(10.0, 9.0), (10.0, 12.0), (10.0, 16.0), (10.2, 30.0)], height, width=0.7)
    kit.path_strip("Path from the gate", mat("dirt"), [(10.0, WALL_Y), (10.1, 4.0), (10.0, 9.0)], height, width=0.6)
    kit.path_strip("Path to the hut", mat("dirt"), [(10.1, 5.6), (12.9, 5.65)], height, width=0.4)

    # ---- The estate wall behind, the back gate in it, the gate open a crack.
    for x0, x1 in ((-12.0, GATE[0] - 0.4), (GATE[1] + 0.4, 32.0)):
        reb.wall(reb.prim("cube", "Estate wall", stone, ((x0 + x1) / 2, WALL_Y - 0.3, 2.25), (x1 - x0, 0.6, 4.5)))
        reb.prim("cube", "Coping", stone, ((x0 + x1) / 2, WALL_Y - 0.3, 4.58), (x1 - x0, 0.8, 0.16))
    for x in (GATE[0] - 0.4, GATE[1] + 0.4):
        reb.wall(reb.prim("cube", "Gate pier", stone, (x, WALL_Y - 0.2, 2.6), (0.8, 0.85, 5.2)))
        reb.prim("sphere", "Finial ball", stone, (x, WALL_Y - 0.2, 5.6), (0.55, 0.55, 0.55), segments=16)
    for leaf, (a, b) in enumerate(((GATE[0], 10.0), (10.0, GATE[1]))):
        for i in range(7):
            x = a + 0.06 + (b - a - 0.12) * i / 6
            kit.rod("Gate bar", reb.mat_metal("Gate iron", (0.035, 0.035, 0.035), 0.55), (x, WALL_Y - 0.2, 0.05), (x, WALL_Y - 0.2, 3.1), 0.016, 6)
    reb.wall(reb.prim("cube", "Gate footprint", None, (10.0, WALL_Y - 0.2, 0.5), (1.6, 0.2, 1.0))).hide_render = True
    kit.rod("Chain on the gate", mat("rust"), (9.85, WALL_Y - 0.12, 1.45), (10.15, WALL_Y - 0.12, 1.3), 0.015, 5)
    iv, ifc = [], []
    for _ in range(1600):
        x = rng.uniform(-6, 26)
        if GATE[0] - 0.9 < x < GATE[1] + 0.9:
            continue
        z = 4.5 - 4.0 * rng.random() ** 1.5
        a = rng.uniform(0, 2 * math.pi)
        reb.card(iv, ifc, Vector((x, WALL_Y + 0.02, z)), Vector((math.cos(a), 0, math.sin(a) - 0.4)).normalized(), Vector((0, 1, 0)), 0.1, 0.12, -0.5)
    reb.mesh_object("Ivy", iv, ifc, mat("ivy"), smooth=False)

    # ---- The runs: chain-link on posts, a doghouse and a name board each, every gate torn out.
    x0, x1 = RUNS_X
    for y in RUN_Y:
        fence("Run divider", link_m, (x0, y), (x1, y))
    fence("Run back", link_m, (x0, RUN_Y[0]), (x0, RUN_Y[-1]))
    for y in RUN_Y:
        for x in (x0, x1):
            reb.wall(kit.rod("Run post", mat("steel"), (x, y, 0), (x, y, 2.1), 0.035, 8))
    gates = []
    names = ("No.1  REX", "No.2  BRUTUS", "No.3  SHADOW", "No.4  KAISER")
    for i in range(4):
        ya, yb = RUN_Y[i], RUN_Y[i + 1]
        yc = (ya + yb) / 2
        d0, d1 = yc - RUN_DOOR / 2, yc + RUN_DOOR / 2
        fence("Run front", link_m, (x1, ya), (x1, d0))
        fence("Run front", link_m, (x1, d1), (x1, yb))
        for y in (d0, d1):
            kit.rod("Gate post", mat("steel"), (x1, y, 0), (x1, y, 2.0), 0.03, 8)
        # Name board over the gate, facing the yard.
        reb.prim("cube", "Name board", mat("dark wood"), (x1 + 0.03, yc, 2.25), (0.03, 1.1, 0.24))
        kit.text(f"Name {i}", names[i], mat("white paint"), (x1 + 0.05, yc, 2.25), size=0.1, rot=(math.pi / 2, 0, math.pi / 2))
        # The doghouse at the back.
        dh = (x0 + 0.65, yc)
        reb.wall(kit.box("Doghouse", mat("planks"), (dh[0], dh[1], 0.0), (1.0, 1.1, 0.85)))
        for side in (-1, 1):
            reb.prim("cube", "Doghouse roof", mat("tin"), (dh[0], dh[1] + side * 0.3, 1.02), (1.15, 0.7, 0.04), rot=(side * 0.55, 0, 0))
        reb.prim("cube", "Doghouse door", mat("black"), (dh[0] + 0.505, dh[1], 0.3), (0.01, 0.42, 0.5))
        kit.scratches(f"Claw marks {i}", mat("pine"), (dh[0] + 0.51, dh[1] + 0.35, 0.75), (1, 0), count=4, length=0.4, seed=i)
        # Straw, bowls, a snapped chain, bones.
        sv, sf = [], []
        bloody = i in (2, 1)
        for _ in range(260):
            p = Vector((rng.uniform(x0 + 1.2, x1 - 0.3), rng.uniform(ya + 0.2, yb - 0.2), 0.01))
            a = rng.uniform(0, 2 * math.pi)
            reb.card(sv, sf, p, Vector((math.cos(a), math.sin(a), 0.05)).normalized(), Vector((0, 0, 1)), 0.02, rng.uniform(0.12, 0.25), -0.1)
        reb.mesh_object(f"Straw {i}", sv, sf, bloody_straw if bloody else straw, smooth=False)
        bx, by = x1 - 0.6, ya + 0.45
        reb.prim("cone", f"Bowl {i}", mat("steel"), (bx, by, 0.04), (0.3, 0.3, 0.08), top=0.7, rot=(0, 0, 0) if i % 2 else (1.4, 0, 0.5), segments=16)
        reb.prim("cone", f"Water bowl {i}", mat("steel"), (bx - 0.4, by + 0.1, 0.04), (0.28, 0.28, 0.08), top=0.7, segments=16)
        stake = Vector((x0 + 1.25, yc + 0.5, 0.0))
        kit.rod(f"Stake {i}", mat("iron"), stake, stake + Vector((0, 0, 0.25)), 0.03)
        prev = stake + Vector((0, 0, 0.2))
        for k in range(rng.randint(5, 9)):
            nxt = prev + Vector((rng.uniform(0.1, 0.18), rng.uniform(-0.1, 0.1), 0)) if k else Vector((prev.x + 0.1, prev.y, 0.02))
            nxt.z = 0.02
            kit.rod("Chain link", mat("rust"), prev, nxt, 0.012, 5)
            prev = nxt
        reb.prim("cube", f"Snapped link {i}", mat("rust"), (prev.x + 0.06, prev.y, 0.02), (0.05, 0.02, 0.015), rot=(0, 0, rng.uniform(0, 3)))
        if i != 2:
            kit.bones(f"Gnawed bones {i}", (x0 + 1.9, yc - 0.3, 0.0), spread=0.5, seed=10 + i, skull=(i == 3))
        kit.splat(f"Run blood {i}", mat("old blood"), (x0 + 2.4, yc, 0.0), 0.35 + 0.2 * (i == 1), seed=20 + i, stretch=(1.5, 0.9))
        # The gate, torn out a different way in each run.
        g = reb.prim("cube", f"Run gate {i}", link_m, (0, RUN_DOOR / 2, 0.9), (0.01, RUN_DOOR, 1.8))
        frame = [kit.rod("Gate frame", mat("steel"), (0, 0, z), (0, RUN_DOOR, z), 0.018, 6) for z in (0.05, 1.8)]
        frame += [kit.rod("Gate frame", mat("steel"), (0, y, 0.05), (0, y, 1.8), 0.018, 6) for y in (0.0, RUN_DOOR)]
        leaf = kit.join(f"Run gate {i}", [g] + frame, origin=(0, 0, 0))
        if i == 0:
            leaf.location, leaf.rotation_euler = (x1 + 0.02, d1, 0), (0, 0, math.pi / 2 + 1.2)
        elif i == 1:
            leaf.location, leaf.rotation_euler = (x1 + 0.4, d0 - 0.2, 0.03), (0, math.pi / 2, 0.3)
        elif i == 2:
            leaf.location, leaf.rotation_euler = (x1 + 0.02, d0, 0.1), (0.1, -0.12, -1.75)
        else:
            leaf.location, leaf.rotation_euler = (x1 + 0.02, d1, 0), (0, 0, math.pi + 0.5)
        gates.append(leaf)
    for i in range(6):
        kit.splat(f"Blood on the wire {i}", mat("blood"), (x1 + 0.01, RUN_Y[2] + rng.uniform(0.1, 2.3), rng.uniform(0.3, 1.4)), 0.07, rot=(0, math.pi / 2, 0), seed=60 + i)
    # A loose length of chain hanging from the last post, swinging.
    hook = reb.prim("sphere", "Chain hook", mat("iron"), (x1 + 0.05, RUN_Y[-1], 1.9), (0.04, 0.04, 0.04), segments=6)
    links_ = []
    for k in range(7):
        links_.append(kit.rod("Hanging chain", mat("rust"), (x1 + 0.05, RUN_Y[-1], 1.9 - k * 0.12), (x1 + 0.05, RUN_Y[-1], 1.78 - k * 0.12), 0.013, 5))
    for l_ in links_:
        l_.parent = hook
        l_.matrix_parent_inverse = Matrix.Translation(-hook.location)
    # A hole dug out under the back fence of the last run.
    kit.splat("Dug hole", mat("black"), (x0 + 0.1, 12.2, 0.002), 0.35, seed=9, stretch=(0.7, 1.3))
    kit.splat("Spoil", mat("mud"), (x0 + 0.6, 12.0, 0.004), 0.45, seed=10)

    # ---- The handler, in the third run, in his grey uniform; his catch-pole snapped.
    hx, hy = 3.9, (RUN_Y[2] + RUN_Y[3]) / 2
    kit.body("Handler", (hx, hy - 0.4, 0.02), heading=0.5, pose="back", top=uniform, legs=uniform, seed=7, missing=("l_hand", "r_foot"))
    kit.splat("Handler's blood", mat("blood"), (hx + 0.9, hy - 0.1, 0.0), 0.75, seed=31, stretch=(1.4, 1.0))
    kit.drag_trail("Pulled about", mat("old blood"), [(hx + 1.0, hy), (5.3, hy + 0.6), (x1 - 0.1, hy + 0.2)], width=0.3, seed=32)
    kit.rod("Catch-pole", mat("steel"), (hx + 0.6, hy + 0.8, 0.03), (hx + 1.9, hy + 0.55, 0.03), 0.02, 6)
    kit.rod("Catch-pole, snapped", mat("steel"), (hx + 2.1, hy + 0.3, 0.03), (hx + 2.4, hy - 0.5, 0.03), 0.02, 6)
    kit.rod("Pole loop", mat("rubber"), (hx + 2.4, hy - 0.5, 0.03), (hx + 2.5, hy - 0.62, 0.05), 0.012, 4)
    reb.prim("cube", "Handler's cap", uniform, (hx + 1.4, hy - 0.8, 0.04), (0.24, 0.2, 0.08), rot=(0.1, 0, 0.7), bevel=0.03)
    reb.prim("cube", "Whistle", mat("steel"), (hx + 0.4, hy + 0.5, 0.01), (0.05, 0.015, 0.015))

    # ---- The paw prints, out of the runs, north to the gate and south to the house.
    pv, pf = [], []
    for start, end, n in (((x1 + 0.3, 7.0), (9.9, WALL_Y + 0.4), 22), ((x1 + 0.3, 9.6), (10.2, Y1 + 0.5), 22), ((x1 + 0.4, 4.6), (9.6, WALL_Y + 0.5), 14), ((x1 + 0.2, 11.8), (9.6, Y1 + 0.5), 14)):
        s, e = Vector(start), Vector(end)
        for k in range(n):
            p = s.lerp(e, k / n) + Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25)))
            for dx, dy, r in ((0, 0, 0.035), (0.04, 0.035, 0.012), (0.05, 0.0, 0.012), (0.04, -0.035, 0.012), (0.065, 0.015, 0.011)):
                kit._stain(pv, pf, rng, (p.x + dx, p.y + dy, height(p.x, p.y) + 0.004), r, 0.0, 0.3, (1, 1), k, points=6, drops=False)
    reb.mesh_object("Paw prints", pv, pf, mat("mud"), smooth=False)

    # ---- The handler's hut: boards, tin roof, a lit window, the door banging.
    hx0, hx1, hy0, hy1 = HUT
    for ob in kit.walls(hx0 + 0.06, hy0 + 0.06, hx1 - 0.06, hy1 - 0.06, 2.4, hut_boards, openings=[
        ("w", HUT_DOOR[0], HUT_DOOR[1], 0.0, 2.0),
        ("w", 6.5, 7.1, 1.0, 1.6),
    ], thick=0.12, floor=mat("planks"), ceiling=mat("dark wood"), name="Hut wall"):
        reb.wall(ob)
    reb.prim("cube", "Hut roof", mat("tin"), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 2.6), (hx1 - hx0 + 0.6, hy1 - hy0 + 0.6, 0.08), rot=(0, 0.1, 0))
    reb.prim("cube", "Window glass", reb.mat_glass("Grimy glass", (0.55, 0.5, 0.45)), (hx0, 6.8, 1.3), (0.01, 0.6, 0.6))
    reb.wall(kit.table("Hut desk", mat("pine"), (hx0 + 0.6, 6.6, 0.0), size=(0.7, 1.2, 0.76)))
    lamp, lamp_light, flame = kit.lantern("Desk lamp", (hx0 + 0.6, 6.4, 0.76), energy=25)
    kit.papers("Logbook", (hx0 + 0.6, 6.85, 0.76), spread=0.15, count=3, seed=3)
    kit.chair("Hut chair", mat("pine"), (hx0 + 1.2, 6.2, 0.0), rot=math.pi + 0.5, tipped=True)
    reb.prim("cube", "Feed chart", mat("paper"), (hx1 - 0.08, 5.5, 1.5), (0.01, 0.7, 0.5))
    for k in range(5):
        reb.prim("cube", "Chart line", mat("black"), (hx1 - 0.09, 5.5, 1.66 - k * 0.08), (0.003, 0.6, 0.012))
    for k in range(3):
        reb.prim("cube", f"Feed sack {k}", mat("canvas"), (hx1 - 0.45, 4.5 + k * 0.5, 0.3), (0.5, 0.45, 0.6), rot=(0, 0, rng.uniform(-0.2, 0.2)), bevel=0.08)
    for k in range(4):
        kit.rod("Lead on a peg", mat("rubber"), (hx1 - 0.08, 6.2 + k * 0.15, 1.8), (hx1 - 0.1, 6.2 + k * 0.15, 1.1), 0.01, 4)
    # The door on its hinge at the door's north jamb, swinging out into the yard.
    hinge = bpy.data.objects.new("Hut door hinge", None)
    bpy.context.scene.collection.objects.link(hinge)
    hinge.location = (hx0, HUT_DOOR[0], 0.0)
    door = reb.prim("cube", "Hut door", hut_boards, (0.03, (HUT_DOOR[1] - HUT_DOOR[0]) / 2, 1.0), (0.05, HUT_DOOR[1] - HUT_DOOR[0] - 0.02, 2.0))
    door.parent = hinge
    kit.scratches("Clawed hut door", mat("pine"), (0.06, 0.45, 1.3), (1, 0), count=7, length=0.8, seed=12).parent = hinge
    # The sign and the lamp over the door.
    reb.prim("cube", "Caution sign", sign_m, (hx0 - 0.08, 6.8, 2.0), (0.02, 0.7, 0.32))
    kit.text("Caution", "CAUTION - DOGS", mat("black"), (hx0 - 0.095, 6.8, 2.0), size=0.075, rot=(math.pi / 2, 0, -math.pi / 2))
    bulk_m = reb.mat_emit("Bulkhead lamp", (1.0, 0.8, 0.5), 12)
    reb.prim("cyl", "Bulkhead lamp", bulk_m, (hx0 - 0.1, 5.65, 2.25), (0.16, 0.16, 0.08), rot=(0, math.pi / 2, 0), segments=12)
    bulk = reb.spot("Bulkhead light", (hx0 - 0.25, 5.65, 2.3), (hx0 - 2.5, 5.65, 0.0), 240, (1.0, 0.8, 0.5), 110, 0.7, 0.1)
    inside = reb.point("Lamp spill from the door", (hx0 + 0.5, 5.65, 1.4), 15, (1.0, 0.6, 0.3), 0.2)

    # ---- The yard: a lamp post, a water trough, a barrow of feed, a hose.
    kit.rod("Lamp post", mat("iron"), (9.0, 7.6, 0), (9.0, 7.6, 3.2), 0.06)
    reb.wall(reb.prim("cube", "Lamp post footprint", None, (9.0, 7.6, 0.5), (0.2, 0.2, 1.0))).hide_render = True
    reb.prim("cone", "Lamp hood", mat("iron"), (9.0, 7.6, 3.3), (0.45, 0.45, 0.18), top=0.2, segments=12)
    post_m = reb.mat_emit("Yard lamp", (1.0, 0.85, 0.6), 15)
    reb.prim("sphere", "Yard lamp bulb", post_m, (9.0, 7.6, 3.15), (0.12, 0.12, 0.14), segments=10)
    yard = reb.point("Yard lamp", (9.0, 7.6, 3.05), 180, (1.0, 0.85, 0.6), 0.1)
    trough = kit.box("Water trough", concrete, (12.2, 11.0, 0.0), (1.6, 0.6, 0.5))
    reb.wall(trough)
    reb.prim("cube", "Trough water", reb.mat_plain("Dark water", (0.01, 0.012, 0.012), 0.05), (12.2, 11.0, 0.45), (1.45, 0.45, 0.01))
    kit.splat("Pink in the water", reb.mat_plain("Bloody water", (0.12, 0.02, 0.02), 0.05), (12.0, 11.0, 0.457), 0.18, seed=12)
    kit.rod("Hose", mat("green paint"), (12.9, 10.7, 0.45), (13.8, 9.6, 0.02), 0.025, 8)
    for i in range(4):
        reb.prim("cone", f"Spilled bowl {i}", mat("steel"), (11.2 + i * 0.5, 9.3 + rng.uniform(-0.3, 0.3), 0.04), (0.28, 0.28, 0.08), top=0.7, rot=(rng.choice((0, 1.5, 3.1)), 0, rng.uniform(0, 3)), segments=16)
    for k in range(3):
        reb.prim("cube", f"Torn sack {k}", mat("canvas"), (14.4 + k * 0.6, 8.6 + rng.uniform(-0.2, 0.2), 0.12), (0.55, 0.4, 0.24), rot=(0, 0, rng.uniform(0, 3)), bevel=0.06)
    fv, ff = [], []
    for _ in range(400):
        p = Vector((rng.gauss(15.0, 0.8), rng.gauss(9.0, 0.5), 0.006))
        kit._stain(fv, ff, rng, tuple(p), 0.012, 0.0, 0.3, (1.6, 0.6), 1, points=5, drops=False)
    reb.mesh_object("Spilled feed", fv, ff, reb.mat_plain("Kibble", (0.15, 0.08, 0.04), 0.7), smooth=False)

    # ---- South: clipped yews gone shaggy either side of the path, the house beyond.
    for x0_, x1_ in ((-6.0, SOUTH[0]), (SOUTH[1], 26.0)):
        reb.prim("cube", "Yew hedge", yew, ((x0_ + x1_) / 2, Y1 + 0.9, 1.1), (x1_ - x0_, 1.2, 2.2), bevel=0.25)
    hv, hf = [], []
    for _ in range(2500):
        x = rng.uniform(-6, 26)
        if SOUTH[0] < x < SOUTH[1]:
            continue
        p = Vector((x, Y1 + 0.3 + rng.uniform(0, 1.2), rng.uniform(0.2, 2.5)))
        a = rng.uniform(0, 2 * math.pi)
        reb.card(hv, hf, p, Vector((math.cos(a), math.sin(a), rng.uniform(0, 1))).normalized(), Vector((0, 0, 1)), 0.06, rng.uniform(0.1, 0.25), 0.3)
    reb.mesh_object("Shaggy growth", hv, hf, mat("needles"), smooth=False)
    mz = Y1 + 22.0
    reb.prim("cube", "Mansion back", dark_stone, (8.0, mz + 8, 9.0), (50.0, 16.0, 18.0))
    for side in (-1, 1):
        reb.prim("cube", "Mansion roof", reb.mat_plain("Slate", (0.015, 0.017, 0.022), 0.6), (8.0, mz + 8 + side * 4.3, 20.5), (50.0, 9.6, 0.3), rot=(-side * 0.68, 0, 0))
    for x in (-8.0, 4.0, 16.0, 24.0):
        reb.prim("cube", "Chimney stack", dark_stone, (x, mz + 8, 23.0), (1.4, 1.4, 4.0))
    for i in range(10):
        x = -12 + i * 4.4
        for z in (4.5, 11.0):
            wm = lit if (i, z) in ((4, 11.0), (7, 4.5)) else reb.mat_plain("Dark glass", (0.008, 0.01, 0.014), 0.2)
            reb.prim("cube", "Mansion window", wm, (x, mz - 0.05, z), (1.2, 0.1, 2.2))
    reb.point("Window glow", (-12 + 4 * 4.4, mz - 0.8, 11.0), 120, (1.0, 0.6, 0.28), 0.4)
    reb.point("Window glow", (-12 + 7 * 4.4, mz - 0.8, 4.5), 120, (1.0, 0.6, 0.28), 0.4)
    kit.forest(rng, lambda x, y: 0.0, lambda x, y: (-8 < x < 30 and y < 30) or (x > -8 and y < 32), (-30, -10, 50, 40), count=30, spacing=3.0, tall=(12, 20), ferns=0, needles=0)
    kit.forest(rng, lambda x, y: 0.0, lambda x, y: not (x > X1 + 2 and y < Y1), (X1 + 2, -6, 34, Y1), count=25, spacing=2.2, tall=(10, 16), ferns=10, needles=0)
    kit.forest(rng, lambda x, y: 0.0, lambda x, y: not (x < -1 and y < Y1), (-16, -6, -1, Y1), count=20, spacing=2.2, tall=(10, 16), ferns=10, needles=0)
    kit.meadow(rng, 900, lambda r: (r.uniform(X0 - 3, X1 + 3), r.choice((r.uniform(WALL_Y + 0.1, 2.6), r.uniform(Y1 - 0.8, Y1 + 0.2)))), height, mat("dead grass"))
    weeds = kit.meadow(rng, 700, lambda r: (r.uniform(6.8, X1 + 1), r.uniform(WALL_Y + 0.2, Y1)), height)

    # ---- Light: moonlight, the yard lamp, the hut's lamps.
    kit.time_light("night", sun_heading=140, sun_energy=0.14)
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(30), 0, math.radians(300)))
    fill = bpy.context.active_object
    fill.name, fill.data.energy, fill.data.color = "Night sky fill", 0.03, (0.35, 0.42, 0.7)

    anim = kit.Anim(16)

    def bang(k):
        a = abs(math.sin(anim.phase(k)))
        hinge.rotation_euler = (0, 0, 1.25 * a)
    anim.custom(bang)
    anim.flicker(yard, post_m, depth=0.35, dropouts=2)
    anim.flicker(lamp_light, flame, depth=0.25, dropouts=0)
    anim.swing(hook, axis=1, degrees=10)
    anim.sway(weeds, amount=0.04)

    # ---- What the game needs.
    room.door("estate-wall", (GATE[0] + 0.1, Y0, GATE[1] - 0.1, Y0 + 0.6), arrive=(10.0, 3.4), face=(0, 1))
    room.door("back-garden", (SOUTH[0], Y1 - 0.6, SOUTH[1], Y1), arrive=(10.0, 12.6), face=(0, -1))
    room.check((x1, RUN_Y[2] + 0.2, x1 + 0.8, RUN_Y[3] - 0.2), "The gate's been torn off its hinges. From the inside.")
    room.check((3.0, RUN_Y[2] + 0.2, 6.0, RUN_Y[3] - 0.2), "Their handler. What's left of him.\nHis catch-pole is snapped in two.")
    room.check((x1 - 1.2, RUN_Y[0] + 0.2, x1, RUN_Y[1] - 0.2), "A chain, snapped at the collar end.\nWhatever was on it pulled until it broke.")
    room.check((x1, RUN_Y[0], x1 + 0.6, RUN_Y[-1]), "REX. BRUTUS. SHADOW. KAISER.\nThe dogs on the mountain came from here.")
    room.check((hx0 - 0.8, HUT_DOOR[0] - 0.3, hx0, HUT_DOOR[1] + 0.3), "The door won't stay shut.\nThere's a lamp lit on the desk. A feed chart on the wall.")
    room.check((11.3, 10.6, 13.1, 11.4), "A water trough. The water's pink.")
    room.check((7.5, 5.5, 9.5, 8.5), "Paw prints, big ones. Heading out to the gate.\nAnd toward the house.")
    room.entry = "Kennels.\nAll the runs are empty."
    room.export(anim, samples=128)


build()
