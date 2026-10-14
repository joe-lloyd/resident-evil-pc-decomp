"""The gate of Logging Camp 4, at noon under cloud.

What it tells: when the men got sick they shut themselves in. They piled
logs across the gateway and drove the camp pickup in behind them, nailed
plywood and tin over the fence rails, and painted SICK - KEEP OUT on a
sheet by the gate. It didn't hold. The barricade has come down outward:
the logs are strewn across the road, the pickup has been shoved out
sideways through the gap, gouging the mud, and the gate leaves hang open
toward the road, one torn off its hinge. The outside of the leaves is
clawed to splinters, as if something wanted in; the inside of the pickup's
door is smeared with bloody hands, as if someone wanted out. A logger lies
dead over what is left of the logs, head down toward the road, and the
crows are at him. A player should work out that the camp is past saving,
and that the way on is through the gap.

Metres: she walks x 1-18, y 2-12.4, a muddy turning space before the fence.
The road comes in from the west edge at y 8.4-11.4 and bends north to the
gate. The fence runs along y 1.7; the gate is between log posts at x 8.4
and 11.8, the gap she walks through at x 9.0-11.2. The barricade's last
logs lie against the west post, x 6.6-9.0, y 2.0-4.0, the dead logger on
them. The pickup sits where it was shoved, x 12.0-16.8, y 4.2-7.0. The
SICK sign is on the fence at x 5.0. Beyond the fence: the camp, its
workshop, the sawmill's grey shed to the north-east.

Moving: the camp sign swinging on its chains, crows on the logger and the
beam, flies, the grass.
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

X0, X1, Y0, Y1 = 1.0, 18.0, 2.0, 12.4
FENCE_Y = 1.7
GATE = (8.4, 11.8)
GAP = (9.0, 11.2)
PICKUP = (14.4, 5.6, 0.45)   # centre x, y and its turn about z
LOGGER = (7.4, 3.0)


def height(x, y):
    """The turning space flat; the forest rolling up south and west, the camp's
    ground flat beyond the fence."""
    n = noise.noise(Vector((x * 0.22, y * 0.22, 4.0)))
    if y < Y0 - 0.3:
        return -0.04 + 0.02 * n
    if X0 - 0.5 < x < X1 + 0.5 and y < Y1 + 0.5:
        return -0.04 + 0.03 * n
    d = max(X0 - 0.5 - x, x - X1 - 0.5, y - Y1 - 0.5, 0)
    return -0.04 + 0.45 * n + d * 0.2


def settle(ob, at, rot):
    """Bake a joined object's parts where they were built, then place it."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def logs_mesh(name, logs, m, sides=10):
    """Logs as one mesh: [(a, b, r)], each a capped cylinder with a ragged bark edge."""
    verts, faces = [], []
    for a, b, r in logs:
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(d).normalized()
        k = len(verts)
        for end in (a, b):
            for i in range(sides):
                t = 2 * math.pi * i / sides
                rr = r * (1 + 0.06 * math.sin(3 * t + a.x))
                verts.append(tuple(end + (side * math.cos(t) + up * math.sin(t)) * rr))
        for i in range(sides):
            faces.append((k + i, k + (i + 1) % sides, k + sides + (i + 1) % sides, k + sides + i))
        faces.append(tuple(k + i for i in reversed(range(sides))))
        faces.append(tuple(k + sides + i for i in range(sides)))
    return reb.mesh_object(name, verts, faces, m)


def corrugated(name, rgb, pitch=0.08):
    """Corrugated tin: ridges every `pitch` metres along x + y, rust in blotches."""
    m = reb.mat_surface(name, [(0.0, rgb), (0.55, tuple(c * 1.25 for c in rgb)), (0.8, (0.28, 0.12, 0.05)), (1.0, (0.18, 0.07, 0.03))], scale=2.2, rough=0.5, bump=0.2)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    tc = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "DIAGONAL"
    wave.inputs["Scale"].default_value = 1.0 / pitch / 2.4
    links.new(tc.outputs["Object"], wave.inputs["Vector"])
    reb.bumped(nodes, links, bsdf, wave.outputs["Fac"], 0.6, 0.02)
    return m


def build():
    rng = random.Random(4)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((2.2, 12.6, 3.5), (12.5, 5.0, 0.8), 200, "from the road coming in: the gate, the strewn logs, the pickup shoved aside")
    room.camera((17.6, 13.6, 3.8), (3.0, 7.6, 0.3), 200, "from the south-east corner: the strewn logs, the logger on the barricade, the road leaving west into the trees")
    room.camera((11.0, 13.4, 3.7), (9.8, 2.6, 1.6), 200, "from the south, square on: the gate and its sign, the gap, the camp beyond")

    mud = reb.mat_surface("Yard mud", [(0.0, (0.04, 0.03, 0.02)), (0.5, (0.1, 0.075, 0.05)), (0.8, (0.14, 0.11, 0.075)), (1.0, (0.08, 0.075, 0.045))], scale=1.4, rough=0.7, bump=0.6)
    floor_m = reb.mat_surface("Forest floor", [(0.0, (0.05, 0.035, 0.02)), (0.4, (0.11, 0.075, 0.045)), (0.65, (0.15, 0.1, 0.06)), (0.85, (0.07, 0.08, 0.035)), (1.0, (0.05, 0.075, 0.025))], scale=1.2, bump=0.5)
    rut_m = reb.mat_surface("Wet ruts", [(0.0, (0.015, 0.012, 0.008)), (0.6, (0.04, 0.03, 0.02)), (1.0, (0.08, 0.06, 0.04))], scale=4, rough=0.25, bump=0.5)
    logs_m = reb.mat_surface("Log bark", [(0.0, (0.05, 0.035, 0.025)), (0.6, (0.12, 0.085, 0.06)), (1.0, (0.18, 0.14, 0.1))], scale=6, bump=0.9)
    pole_m = reb.mat_surface("Grey poles", [(0.0, (0.12, 0.1, 0.08)), (1.0, (0.24, 0.21, 0.17))], scale=8, bump=0.6)
    end_m = reb.mat_surface("Log ends", [(0.0, (0.28, 0.18, 0.09)), (0.7, (0.42, 0.3, 0.16)), (1.0, (0.2, 0.12, 0.06))], scale=12, bump=0.2)
    ply = reb.mat_surface("Plywood", [(0.0, (0.22, 0.16, 0.09)), (0.7, (0.32, 0.24, 0.14)), (1.0, (0.12, 0.09, 0.06))], scale=5, bump=0.15)
    tin = corrugated("Fence tin", (0.2, 0.2, 0.19))
    truck_m = reb.mat_surface("Pickup paint", [(0.0, (0.05, 0.1, 0.16)), (0.6, (0.08, 0.15, 0.22)), (0.85, (0.06, 0.1, 0.13)), (1.0, (0.2, 0.09, 0.04))], scale=3, rough=0.5, bump=0.15)
    chrome = reb.mat_metal("Dull chrome", (0.5, 0.5, 0.48), 0.25)
    dark = reb.mat_plain("Cab dark", (0.015, 0.014, 0.012), 0.9)
    whitewash = reb.mat_surface("Scrawl paint", [(0.0, (0.55, 0.53, 0.48)), (1.0, (0.65, 0.63, 0.58))], scale=20, bump=0.05)

    # ---- Ground: the forest floor, the muddy turning space, the road in, the camp's ground beyond.
    reb.terrain("Forest floor", floor_m, (-16, 36), (-16, 30), height, step=0.4)
    reb.terrain("Far forest floor", floor_m, (-60, 80), (-60, 80), lambda x, y: height(x, y) - 0.4, step=4.0)
    kit.splat("Turning space", mud, (10.0, 6.8, height(10, 6.8) + 0.002), 5.2, seed=1, stretch=(1.35, 0.9), lumps=0.25)
    kit.path_strip("Road in", mud, [(-14.0, 10.8), (-2.0, 10.2), (3.0, 9.9), (7.0, 8.4), (9.6, 5.6), (10.1, 2.4), (10.1, -6.0)], height, width=1.6, wobble=0.15)
    for off in (-0.85, 0.85):
        kit.path_strip("Rut", rut_m, [(-14.0, 10.8 + off), (-2.0, 10.2 + off), (3.0, 9.9 + off), (7.0 + off * 0.5, 8.4 + off * 0.7), (9.6 + off, 5.6 + off * 0.2), (10.1 + off, 2.4), (10.1 + off, -6.0)], height, width=0.22, wobble=0.15, lift=0.009)
    # Where the pickup was shoved: its tyres gouged the mud sideways.
    for k, (x0, y0) in enumerate(((10.4, 2.4), (10.6, 3.9))):
        kit.drag_trail(f"Gouge {k}", rut_m, [(x0, y0), (x0 + 1.4, y0 + 0.9), (x0 + 2.8, y0 + 1.6), (x0 + 3.6, y0 + 2.1)], width=0.3, seed=10 + k, z=0.004)

    # ---- The fence: log posts and three grey rails, plywood and tin nailed over them in a hurry.
    fence_logs = []
    xs = [x for x in [-12 + i * 2.4 for i in range(19)] if not (GATE[0] - 0.4 < x < GATE[1] + 0.4)]
    for x in xs:
        fence_logs.append(((x, FENCE_Y, -0.3), (x, FENCE_Y, 2.4), 0.11))
    for z in (0.5, 1.2, 1.9):
        fence_logs.append(((-12.0, FENCE_Y + 0.12, z), (GATE[0], FENCE_Y + 0.12, z), 0.07))
        fence_logs.append(((GATE[1], FENCE_Y + 0.12, z), (32.0, FENCE_Y + 0.12, z), 0.07))
    logs_mesh("Fence", fence_logs, pole_m)
    reb.wall(reb.prim("cube", "Fence west footprint", None, ((X0 - 1 + GATE[0]) / 2, FENCE_Y, 1.0), (GATE[0] - X0 + 1, 0.4, 2.0))).hide_render = True
    reb.wall(reb.prim("cube", "Fence east footprint", None, ((GATE[1] + X1 + 1) / 2, FENCE_Y, 1.0), (X1 + 1 - GATE[1], 0.4, 2.0))).hide_render = True
    # Barbed wire along the top.
    for z in (2.2, 2.35):
        for (a, b) in (((-12.0, FENCE_Y, z), (GATE[0], FENCE_Y, z)), ((GATE[1], FENCE_Y, z), (32.0, FENCE_Y, z))):
            kit.rod("Barbed wire", mat("rust"), a, b, 0.006, 4)
    # Sheets over the rails, on the outside, some hanging off.
    sheets = [(-4.6, ply, 0.0), (-1.8, tin, 0.05), (2.2, ply, -0.04), (3.6, tin, 0.0), (6.6, ply, 0.03), (13.4, tin, 0.0), (15.8, ply, -0.05), (18.4, tin, 0.02), (21.2, ply, 0.0)]
    for i, (x, m, tilt) in enumerate(sheets):
        reb.prim("cube", f"Fence sheet {i}", m, (x, FENCE_Y + 0.22, 1.15), (1.22, 0.02, 2.0 if m is ply else 1.8), rot=(0, tilt, 0))
    reb.prim("cube", "Sheet torn half off", tin, (0.6, FENCE_Y + 0.6, 0.7), (1.2, 0.02, 1.8), rot=(0.5, 0.3, 0.2))
    # SICK - KEEP OUT, slapped on in white paint, on the sheet west of the gate.
    sx = 5.0
    reb.prim("cube", "Sign sheet", ply, (sx, FENCE_Y + 0.24, 1.25), (1.6, 0.02, 1.15), rot=(0, 0.02, 0))
    kit.text("Scrawl SICK", "SICK", whitewash, (sx, FENCE_Y + 0.26, 1.47), size=0.42, rot=(math.pi / 2, 0.06, math.pi))
    kit.text("Scrawl KEEP OUT", "KEEP OUT", whitewash, (sx + 0.02, FENCE_Y + 0.26, 1.02), size=0.27, rot=(math.pi / 2, -0.05, math.pi))
    for k in range(4):
        reb.prim("cube", f"Paint run {k}", whitewash, (sx - 0.5 + k * 0.33, FENCE_Y + 0.255, 1.14 - 0.08 * k), (0.015, 0.004, 0.18 + 0.05 * k))

    # ---- The gate: two log posts and a beam, the camp's sign on chains, the leaves hanging open.
    gate_logs = [((GATE[0], FENCE_Y, -0.3), (GATE[0], FENCE_Y, 4.6), 0.2), ((GATE[1], FENCE_Y, -0.3), (GATE[1], FENCE_Y, 4.6), 0.2),
                 ((GATE[0] - 0.5, FENCE_Y, 4.35), (GATE[1] + 0.5, FENCE_Y, 4.35), 0.18)]
    gate_ob = logs_mesh("Gate logs", gate_logs, logs_m)
    for x in GATE:
        reb.mask(reb.wall(reb.prim("cyl", "Gate post footprint", None, (x, FENCE_Y, 1.0), (0.4, 0.4, 2.0)), "circle")).hide_render = True
    reb.mask(gate_ob)
    sign_hook = reb.prim("cube", "Sign hook", mat("iron"), ((GATE[0] + GATE[1]) / 2, FENCE_Y + 0.15, 4.17), (2.6, 0.05, 0.04))
    board = reb.prim("cube", "Camp sign", mat("planks"), (0, 0, -0.42), (2.7, 0.07, 0.5))
    words = kit.text("Camp sign words", "LOGGING CAMP 4", mat("white paint"), (0, 0.04, -0.42), size=0.3, rot=(math.pi / 2, 0, math.pi))
    claws = kit.scratches("Claws on the sign", mat("black"), (0.7, 0.04, -0.25), (0, 1), count=4, length=0.3, seed=3)
    for p in (board, words, claws):
        p.parent = sign_hook
    for dx in (-1.2, 1.2):
        ch = kit.rod("Sign chain", mat("iron"), (dx, 0, 0), (dx, 0, -0.17), 0.012, 4)
        ch.parent = sign_hook
    # The leaves: log frames with a brace, opened outward. The west one is torn off its top hinge.
    leaf_m = mat("logs")

    def leaf(name, hinge, length, yaw, drop=0.0):
        piv = reb.prim("cube", f"{name} hinge", mat("iron"), hinge, (0.06, 0.06, 0.06))
        parts = []
        sgn = 1 if length > 0 else -1
        L = abs(length)
        for z in (0.3, 1.0, 1.7):
            parts.append(reb.prim("cube", "rail", leaf_m, (sgn * L / 2, 0, z - 1.0), (L, 0.12, 0.14)))
        for x in (0.08, L / 2, L - 0.08):
            parts.append(reb.prim("cube", "stile", leaf_m, (sgn * x, 0, 0.0), (0.12, 0.13, 1.7)))
        parts.append(reb.prim("cube", "brace", leaf_m, (sgn * L / 2, 0, 0.0), (math.hypot(L, 1.4), 0.1, 0.12), rot=(0, sgn * math.atan2(1.4, L), 0)))
        ob = kit.join(name, parts)
        settle(ob, (0, 0, 0), (0, 0, 0))
        ob.parent = piv
        piv.rotation_euler = (0, drop, yaw)
        return piv, ob
    leaf("West gate leaf", (GATE[0] + 0.2, FENCE_Y + 0.2, 1.0), 1.6, 1.25, drop=0.35)
    leaf("East gate leaf", (GATE[1] - 0.2, FENCE_Y + 0.2, 1.0), -1.6, -1.05)
    for k, (x, y, z, f) in enumerate(((GATE[0] + 0.55, FENCE_Y + 1.15, 1.25, (-1, 0.3)), (GATE[1] - 0.45, FENCE_Y + 1.2, 1.3, (1, 0.3)), (GATE[1] - 0.3, FENCE_Y + 0.8, 0.8, (1, 0.3)))):
        kit.scratches(f"Claws on the gate {k}", reb.mat_plain("Splintered wood", (0.42, 0.32, 0.2), 0.8), (x, y, z), f, count=5, length=0.55, seed=20 + k)
    reb.wall(reb.prim("cube", "West leaf footprint", None, (GATE[0] + 0.5, FENCE_Y + 0.9, 0.5), (0.6, 1.4, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "East leaf footprint", None, (GATE[1] - 0.6, FENCE_Y + 0.85, 0.5), (0.7, 1.3, 1.0))).hide_render = True

    # ---- What is left of the barricade: logs against the west post, the rest strewn over the road.
    pile = [((6.6, 2.4, 0.3), (9.0, 2.3, 0.3), 0.3), ((6.8, 3.0, 0.28), (9.1, 2.9, 0.28), 0.28), ((6.7, 2.65, 0.78), (8.9, 2.6, 0.78), 0.27),
            ((6.9, 3.5, 0.26), (8.5, 3.6, 0.22), 0.25)]
    strewn = [((9.6, 4.6, 0.27), (12.2, 6.4, 0.27), 0.27), ((5.8, 5.2, 0.25), (8.3, 6.6, 0.25), 0.25), ((9.0, 7.6, 0.24), (11.6, 7.2, 0.24), 0.24),
              ((3.6, 6.4, 0.23), (5.8, 7.8, 0.23), 0.23), ((16.2, 7.6, 0.25), (17.6, 9.6, 0.25), 0.25)]
    pile_ob = logs_mesh("Barricade logs", pile, logs_m)
    strewn_ob = logs_mesh("Strewn logs", strewn, logs_m)
    reb.mask(pile_ob)
    reb.mask(strewn_ob)
    reb.wall(reb.prim("cube", "Barricade footprint", None, (7.8, 3.0, 0.5), (2.6, 1.8, 1.0))).hide_render = True
    for a, b, r in pile + strewn:
        for e, d in ((a, Vector(a) - Vector(b)), (b, Vector(b) - Vector(a))):
            reb.prim("cyl", "Log end", end_m, Vector(e) + d.normalized() * 0.004, (2 * r - 0.02, 2 * r - 0.02, 0.01), rot=d.to_track_quat("Z", "Y").to_euler(), segments=10)
        if (Vector(b) - Vector(a)).length > 2.3 and a[1] > 4:
            mid = (Vector(a) + Vector(b)) / 2
            dd = (Vector(b) - Vector(a)).normalized()
            for t in (-0.9, 0.0, 0.9):
                q = mid + dd * t
                reb.wall(reb.prim("cube", "Strewn log footprint", None, (q.x, q.y, 0.25), (0.7, 0.7, 0.5))).hide_render = True
    # Spikes and wire the men put in it, a gas can, sandbags.
    for k in range(5):
        x = 6.8 + k * 0.5
        kit.rod("Spike", mat("rust"), (x, 2.0, 0.9), (x + 0.1, 2.5 + 0.1 * k, 1.35), 0.012, 4)
    for k in range(4):
        reb.prim("cube", f"Sandbag {k}", mat("canvas"), (5.6 + k * 0.42, 2.2 + 0.08 * (k % 2), 0.13), (0.4, 0.26, 0.24), rot=(0, 0, 0.1 * k), bevel=0.07)
    reb.prim("cube", "Gas can", reb.mat_plain("Can red", (0.3, 0.03, 0.02), 0.5), (5.9, 3.4, 0.18), (0.24, 0.14, 0.34), rot=(math.pi / 2, 0, 0.6), bevel=0.02)

    # ---- The logger, dead over the logs, head down toward the road, the crows at him.
    logger = kit.body("Logger on the barricade", (LOGGER[0] - 0.2, LOGGER[1] - 1.0, 1.05), 0.0, pose="front",
                      top=reb.mat_stripes("Red check", [(0.3, 0.04, 0.03), (0.04, 0.03, 0.03)], across=22), legs=mat("denim"), seed=12)
    logger.rotation_euler = (0, 0.55, math.pi / 2 + 0.15)
    kit.splat("Blood down the logs", mat("old blood"), (LOGGER[0], LOGGER[1] + 0.9, 0.33), 0.2, rot=(1.2, 0, 0), seed=13, stretch=(0.7, 1.6))
    kit.splat("Blood under him", mat("blood"), (LOGGER[0] + 0.1, LOGGER[1] + 1.3, height(*LOGGER) + 0.004), 0.42, seed=14, stretch=(1.2, 1.0))
    hat = reb.mat_plain("Hard hat", (0.55, 0.38, 0.03), 0.4)
    reb.prim("sphere", "His hard hat", hat, (LOGGER[0] + 0.9, LOGGER[1] + 1.9, 0.07), (0.3, 0.26, 0.2), rot=(0.3, 0.2, 0), segments=14)
    reb.prim("cyl", "Hard hat brim", hat, (LOGGER[0] + 0.9, LOGGER[1] + 1.92, 0.04), (0.36, 0.32, 0.015), rot=(0.3, 0.2, 0), segments=16)
    crow_pecking, _ = kit.crow("Crow on the logger", (LOGGER[0] + 0.3, LOGGER[1] + 0.1, 0.88), heading=2.0)
    kit.crow("Crow on the logs", (LOGGER[0] - 0.8, LOGGER[1] - 0.2, 1.06), heading=0.5)
    kit.crow("Crow on the beam", (GATE[0] + 0.6, FENCE_Y, 4.55), heading=1.6)
    flapper, wings = kit.crow("Crow landing", (GATE[0] + 1.6, FENCE_Y, 4.56), heading=3.6, perched=False)
    kit.crow("Crow in the mud", (LOGGER[0] + 1.5, LOGGER[1] + 2.4, 0.0), heading=4.2)

    # ---- The pickup, shoved out sideways through the gap: flat tyres, glass gone, bloody hands inside the door.
    px, py, pr = PICKUP
    parts = []
    parts.append(reb.prim("cube", "bed", truck_m, (-1.2, 0, 0.95), (1.9, 1.75, 0.55), bevel=0.03))
    parts.append(reb.prim("cube", "bed floor", dark, (-1.2, 0, 1.2), (1.8, 1.6, 0.04)))
    parts.append(reb.prim("cube", "cab", truck_m, (0.55, 0, 1.25), (1.4, 1.75, 1.15), bevel=0.05))
    parts.append(reb.prim("cube", "hood", truck_m, (1.85, 0, 0.92), (1.3, 1.72, 0.5), bevel=0.05))
    parts.append(reb.prim("cube", "grille", chrome, (2.52, 0, 0.88), (0.05, 1.5, 0.35)))
    parts.append(reb.prim("cube", "bumper", chrome, (2.6, 0, 0.6), (0.1, 1.85, 0.16)))
    parts.append(reb.prim("cube", "back bumper", chrome, (-2.2, 0, 0.62), (0.1, 1.8, 0.14)))
    parts.append(reb.prim("cube", "dark cab glass hole", dark, (0.6, 0, 1.6), (1.2, 1.77, 0.38)))
    parts.append(reb.prim("cube", "windshield hole", dark, (1.26, 0, 1.55), (0.04, 1.5, 0.4), rot=(0, -0.3, 0)))
    for x in (1.7, -1.4):
        for s in (-1, 1):
            parts.append(reb.prim("cyl", "tyre", mat("rubber"), (x, s * 0.78, 0.33), (0.66, 0.66, 0.24), rot=(math.pi / 2, 0, 0), segments=16))
            parts.append(reb.prim("cyl", "hubcap", chrome, (x, s * 0.91, 0.33), (0.3, 0.3, 0.02), rot=(math.pi / 2, 0, 0), segments=12))
    pickup = kit.join("Pickup", parts)
    settle(pickup, (px, py, -0.06), (0.04, -0.02, pr))
    reb.mask(pickup)
    reb.wall(reb.prim("cube", "Pickup footprint", None, (px, py, 0.6), (4.4, 1.9, 1.2), rot=(0, 0, pr))).hide_render = True
    c, s_ = math.cos(pr), math.sin(pr)

    def on_truck(lx, ly):
        return Vector((px + lx * c - ly * s_, py + lx * s_ + ly * c))
    # Its driver's door hangs open on the south side, the bloody hands inside it.
    hinge_at = on_truck(1.2, 0.9)
    hinge = reb.prim("cube", "Pickup door hinge", mat("iron"), (hinge_at.x, hinge_at.y, 1.0), (0.04, 0.04, 0.8))
    pdoor = reb.prim("cube", "Pickup door", truck_m, (-0.55, 0.03, 0.15), (1.1, 0.06, 1.0), bevel=0.02)
    hands = []
    for k in range(3):
        hands.append(kit.splat(f"Hand inside the door {k}", mat("blood"), (-0.3 - k * 0.25, -0.004, 0.25 + 0.12 * (k % 2)), 0.06, rot=(math.pi / 2, 0, 0), seed=30 + k))
    smear = reb.prim("cube", "Smear inside the door", mat("old blood"), (-0.5, -0.004, 0.05), (0.5, 0.004, 0.06), rot=(0, 0.3, 0))
    for p in [pdoor, smear] + hands:
        p.parent = hinge
    hinge.rotation_euler = (0, 0, pr - 1.1)
    kit.scratches("Claws on the pickup", reb.mat_plain("Bare metal", (0.35, 0.35, 0.33), 0.3), tuple(on_truck(-1.0, -0.9).to_3d() + Vector((0, 0, 1.1))), (s_, -c), count=5, length=0.4, seed=40)
    kit.shards("Pickup glass", (px + 0.3, py + 1.2, 0.0), spread=0.9, count=26, seed=41)
    for k in range(3):
        reb.prim("cube", f"Sandbag in the bed {k}", mat("canvas"), tuple(on_truck(-1.6 + k * 0.5, 0.3 * (k - 1)).to_3d() + Vector((0, 0, 1.33))), (0.42, 0.26, 0.2), rot=(0, 0, pr + 0.2 * k), bevel=0.06)

    # ---- Beyond the fence: the camp. The workshop's tin, the sawmill's tall grey shed, a bunkhouse roof.
    camp_tin = corrugated("Camp tin", (0.12, 0.13, 0.12), pitch=0.1)
    grey = corrugated("Mill grey", (0.14, 0.14, 0.13))
    roof = corrugated("Roof tin", (0.16, 0.16, 0.15))
    boards_m = kit.boards("Bunkhouse boards", (0.2, 0.13, 0.08), width=0.2)
    def shed(name, x0, x1, y0, y1, h, m, ridge_x=True, rise=1.0):
        """A camp building: walls, and a gable roof of tin on top, its ridge along x or y."""
        reb.prim("cube", name, m, ((x0 + x1) / 2, (y0 + y1) / 2, h / 2), (x1 - x0, y1 - y0, h))
        if ridge_x:
            half = (y1 - y0) / 2 + 0.3
            ang = math.atan2(rise, half)
            for s_ in (-1, 1):
                reb.prim("cube", f"{name} roof", roof, ((x0 + x1) / 2, (y0 + y1) / 2 + s_ * half / 2, h + rise / 2), (x1 - x0 + 0.5, half / math.cos(ang), 0.08), rot=(-s_ * ang, 0, 0))
        else:
            half = (x1 - x0) / 2 + 0.3
            ang = math.atan2(rise, half)
            for s_ in (-1, 1):
                reb.prim("cube", f"{name} roof", roof, ((x0 + x1) / 2 + s_ * half / 2, (y0 + y1) / 2, h + rise / 2), (half / math.cos(ang), y1 - y0 + 0.5, 0.08), rot=(0, s_ * ang, 0))
    shed("Workshop", 13.4, 19.2, -3.4, -0.6, 3.0, camp_tin, rise=0.8)
    shed("Sawmill", 18.5, 32.0, -14.3, -4.7, 6.0, grey, ridge_x=True, rise=1.6)
    shed("Bunkhouse", 6.0, 17.0, -20.3, -15.3, 2.8, boards_m)
    shed("Mess hall", -3.4, 2.0, -11.9, -2.9, 3.0, whitewash, ridge_x=False)
    reb.prim("cube", "Workshop door", dark, (15.2, -0.58, 1.1), (1.2, 0.02, 2.2))
    reb.prim("cube", "Workshop window", dark, (17.6, -0.58, 1.6), (1.2, 0.02, 0.8))
    for x in (7.6, 9.8, 12.0, 14.2):
        reb.prim("cube", "Bunkhouse window", dark, (x, -15.28, 1.5), (0.9, 0.02, 0.8))
    reb.prim("cube", "Mess door", dark, (2.02, -7.4, 1.0), (0.02, 0.9, 2.0))
    reb.prim("cube", "Mill doors", dark, (18.48, -9.5, 1.7), (0.02, 3.0, 3.4))
    reb.prim("cube", "Mill window", dark, (18.48, -12.0, 4.3), (0.02, 1.6, 1.0))
    kit.text("Mill sign", "CAMP 4 SAWMILL", mat("black"), (18.45, -9.5, 4.1), size=0.3, rot=(math.pi / 2, 0, -math.pi / 2))
    sk = reb.mat_plain("Skidder yellow", (0.45, 0.32, 0.03), 0.5)
    sk_parts = [reb.prim("cube", "body", sk, (0, 0, 1.2), (3.2, 1.6, 0.9)), reb.prim("cube", "blade", sk, (2.0, 0, 0.6), (0.2, 2.4, 0.8))]
    for x in (-1.0, 1.0):
        for s_ in (-1, 1):
            sk_parts.append(reb.prim("cyl", "wheel", mat("rubber"), (x, s_ * 1.0, 0.75), (1.5, 1.5, 0.5), rot=(math.pi / 2, 0, 0), segments=16))
    for x in (-0.2, 0.8):
        for s_ in (-1, 1):
            sk_parts.append(kit.rod("cage", mat("black"), (x, s_ * 0.7, 1.65), (x, s_ * 0.7, 2.9), 0.04, 6))
    sk_parts.append(reb.prim("cube", "cage roof", sk, (0.3, 0, 2.95), (1.2, 1.6, 0.08)))
    settle(kit.join("Skidder", sk_parts), (8.0, -3.8, 0.0), (0, 0, 0.1))
    kit.drum("Drum in the camp", mat("rust"), (4.0, -1.0, 0.0))
    kit.drum("Drum on its side", mat("rust"), (12.0, -0.8, 0.0), tipped=True, rot=0.6)
    # The fuel depot's wire compound north-west, inside the fence: a tank on its stand, drums.
    wire = reb.mat_surface("Depot wire", [(0.0, (0.1, 0.1, 0.1)), (1.0, (0.26, 0.26, 0.25))], scale=60, rough=0.5, bump=0.8)
    for x0, y0, x1, y1 in ((-2.0, -2.0, 6.6, -2.0), (6.6, -2.0, 6.6, 1.3), (-2.0, -2.0, -2.0, 1.3)):
        reb.prim("cube", "Depot fence", wire, ((x0 + x1) / 2, (y0 + y1) / 2, 0.9), (max(x1 - x0, 0.02), max(y1 - y0, 0.02), 1.8))
    for x, y in ((-2.0, -2.0), (6.6, -2.0), (6.6, 1.3), (-2.0, 1.3), (2.3, -2.0)):
        kit.rod("Depot post", mat("rust"), (x, y, 0), (x, y, 1.9), 0.04)
    tank = reb.prim("cyl", "Diesel tank", reb.mat_plain("Tank red", (0.22, 0.04, 0.02), 0.6), (1.0, -0.6, 1.6), (1.3, 1.3, 3.2), rot=(0, math.pi / 2, 0), segments=18)
    for x in (-0.2, 2.2):
        kit.rod("Tank leg", mat("rust"), (x, -0.6, 0), (x, -0.6, 1.0), 0.06)
    for i, (x, y) in enumerate(((4.4, -1.2), (5.0, -0.6), (4.6, 0.2), (5.6, -1.4))):
        kit.drum(f"Depot drum {i}", mat("rust") if i % 2 else reb.mat_plain("Drum blue", (0.04, 0.08, 0.14), 0.5), (x, y, 0.0), tipped=(i == 3), rot=0.8)
    reb.prim("cube", "Quarantine board", mat("white paint"), (7.4, -0.0, 1.3), (1.4, 0.05, 0.8))
    kit.text("Quarantine board words", "QUARANTINE", mat("red paint"), (7.4, 0.03, 1.4), size=0.2, rot=(math.pi / 2, 0, math.pi))
    kit.rod("Board post", mat("dark wood"), (7.4, 0.0, 0.0), (7.4, 0.0, 0.9), 0.05)

    # ---- The forest round the clearing, cut back from the fence.
    cams = ((2.2, 12.6), (17.6, 13.6), (11.0, 13.4))

    def keep_out(x, y):
        if y < FENCE_Y + 2.5:
            return True
        if X0 - 1.0 < x < X1 + 1.0 and y < Y1 + 0.8:
            return True
        if x < X0 + 1 and abs(y - 10.5) < 1.8:
            return True
        return any((x - cx) ** 2 + (y - cy) ** 2 < 25 for cx, cy in cams)
    kit.forest(rng, height, keep_out, (-16, -2, 36, 30), count=110, spacing=1.7, tall=(13, 22), ferns=150, needles=900, dead=0.1)
    far_m = reb.mat_surface("Far spruce", [(0.0, (0.008, 0.016, 0.01)), (1.0, (0.025, 0.045, 0.022))], scale=0.6, bump=0.3)
    kit.forest(rng, height, lambda x, y: (-6 < x < 34 and -23 < y < 1.0) or y > 1.0, (-18, -30, 40, 1), count=70, spacing=2.0, tall=(14, 22), ferns=0, needles=0, dead=0.1)
    fv, ff = [], []
    placed = 0
    while placed < 320:
        x, y = rng.uniform(-60, 80), rng.uniform(-60, 80)
        if -16 < x < 36 and -24 < y < 30:
            continue
        placed += 1
        z = height(x, y) - 0.4
        h = rng.uniform(14, 24)
        for tier in range(4):
            z0 = z + h * (0.25 + 0.19 * tier)
            r = h * 0.2 * (1 - 0.22 * tier) * rng.uniform(0.8, 1.1)
            k0 = len(fv)
            for j in range(9):
                a = 2 * math.pi * j / 9 + rng.uniform(-0.2, 0.2)
                rr = r * rng.uniform(0.75, 1.05)
                fv.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z0 - rng.uniform(0, 0.8)))
            fv.append((x, y, z0 + h * 0.3))
            ff.extend((k0 + j, k0 + (j + 1) % 9, k0 + 9) for j in range(9))
        reb.box(fv, ff, (x, y, z + h * 0.15), (0.4, 0.4, h * 0.3))
    reb.mesh_object("Far spruces", fv, ff, far_m, smooth=False)
    # Stumps in the cleared strip, grass along the fence and the verges.
    for i, (x, y, r) in enumerate(((2.0, 4.0, 0.4), (17.5, 3.0, 0.38), (1.6, 7.0, 0.35), (17.4, 8.6, 0.42))):
        st = reb.prim("cyl", f"Stump {i}", mat("bark"), (x, y, 0.2), (2 * r, 2 * r, 0.5), segments=10)
        reb.mask(reb.wall(st, "circle"))
        reb.prim("cyl", f"Stump top {i}", end_m, (x, y, 0.455), (2 * r - 0.04, 2 * r - 0.04, 0.01), segments=10)

    def verge(r_):
        while True:
            x, y = r_.uniform(X0 - 4, X1 + 4), r_.uniform(Y0 - 0.2, Y1 + 3)
            if ((x - 10.0) / 6.6) ** 2 + ((y - 6.8) / 4.6) ** 2 > 1.0 and not (x < 4 and abs(y - 10.2) < 1.2):
                return x, y
    grass = kit.meadow(rng, 1500, verge, height)

    # ---- Light: noon under cloud; the clearing a little brighter than the woods.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.2, mist=((10.0, 2.0, 5.0), (90.0, 90.0, 18.0), 0.011),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.15))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(30)

    anim = kit.Anim(16)
    anim.swing(sign_hook, axis=0, degrees=5)
    anim.bob(crow_pecking, height=0.05, speed=2)
    anim.flap(wings, degrees=45)
    anim.bob(flapper, height=0.12, speed=1)
    anim.flies((LOGGER[0], LOGGER[1] + 0.5, 0.7), count=10, radius=0.5)
    anim.sway(grass, amount=0.06)

    # ---- What the game needs.
    room.door("logging-road", (X0, 8.4, X0 + 0.6, 11.4), arrive=(2.6, 9.9), face=(1, 0))
    room.door("camp-yard", (GAP[0], Y0, GAP[1], Y0 + 0.6), arrive=(10.1, 3.8), face=(0, 1))
    room.check((sx - 0.9, Y0, sx + 0.9, Y0 + 0.8), "SICK - KEEP OUT. Painted in a hurry, the paint still running.")
    room.check((GAP[0], Y0 + 0.6, GAP[1], Y0 + 1.4), "LOGGING CAMP 4. Someone's clawed the sign.\nThe gate's hanging open.")
    room.check((GATE[1] - 1.0, Y0 + 0.4, GATE[1] + 0.2, Y0 + 1.6), "The outside of the gate is clawed to splinters.\nSomething wanted in.")
    room.check((LOGGER[0] - 0.6, LOGGER[1] + 1.0, LOGGER[0] + 1.6, LOGGER[1] + 2.0), "A logger, dead over the logs they piled up. The crows have had his eyes.")
    room.check((13.2, 6.6, 15.0, 7.8), "The camp truck, shoved out of the gate.\nBloody hands all over the inside of the door. Someone wanted out.")
    room.check((5.2, 4.6, 8.6, 7.0), "The barricade. Logs, sandbags, spikes. Pulled down, or pushed.")
    room.entry = "They shut themselves in. It didn't help."
    room.export(anim)


build()
