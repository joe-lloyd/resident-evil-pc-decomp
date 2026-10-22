"""The gate of the Arklay Timber logging camp, at noon under cloud.

What it tells: when the men got sick they shut themselves in. They rolled
logs off the cold deck by the fence across the gateway, drove the camp
pickup in behind them, nailed plywood and tin over the fence rails and
painted KEEP OUT on a sheet by the gate. It didn't hold. The barricade has
come down outward: logs lie strewn over the road, the pickup has been
shoved out sideways through the gap, its tyres scoring the mud, and the
gate leaves hang open toward the road. The outside of the leaves is clawed
to splinters, as if something wanted in; the inside of the pickup's door is
smeared with bloody hands, as if someone wanted out. A logger lies face
down in the mud in front of the logs, where he fell running for the road.
A player should work out that the camp is past saving, and that the way
on is through the gap.

Metres: she walks x 1-18, y 2-12.4, a muddy turning space before the fence.
The road comes in from the west edge at y 8.4-11.4 and bends north to the
gate. The fence runs along y 1.7; the gate is between log posts at x 8.4
and 11.8, the gap she walks through at x 9.0-11.2. The cold deck the
barricade came from lies along the fence at x 1.4-5.6; what is left of the
barricade lies against the west post, x 6.6-9.0, y 2.0-4.0, the dead
logger in front of it. The pickup sits where it was shoved, x 12.0-16.8,
y 4.2-7.0. Beyond the fence is the camp as the yard's own scene builds it,
17.2 m north: the workshop's back wall, the depot's wire, the skidder, the
mess hall, the sawmill.

Moving: the company sign stirring on its chains, flies over the logger.
The grass is still: there is no wind in the forest.
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

X0, X1, Y0, Y1 = 1.0, 17.4, 2.0, 12.0
FENCE_Y = 1.7
GATE = (8.4, 11.8)
GAP = (9.0, 11.2)
PICKUP = (14.4, 5.6, 0.45)   # centre x, y and its turn about z
LOGGER = (6.6, 4.9, 2.4)     # where he lies and the way his head points
YARD = -17.2                 # the yard's scene, moved onto this one's floor
ROAD = [(-14.0, 10.8), (-2.0, 10.2), (3.0, 9.9), (6.8, 8.8), (9.2, 6.4), (10.1, 3.4), (10.1, 0.0), (10.2, -4.0)]
T = 0.12


def height(x, y):
    """The turning space flat; the forest rolling up south and west, the camp's
    ground flat beyond the fence."""
    n = noise.noise(Vector((x * 0.22, y * 0.22, 4.0)))
    if y < Y0 - 0.3:
        return -0.03 + 0.012 * n
    if X0 - 0.5 < x < X1 + 0.5 and y < Y1 + 0.5:
        return -0.04 + 0.03 * n
    d = max(X0 - 0.5 - x, x - X1 - 0.5, y - Y1 - 0.5, 0)
    return -0.04 + 0.45 * n + d * 0.2


def far_land(x, y, z):
    """The kit's ranges, eased into the mountainside round the camp."""
    r = math.hypot(x - 9.0, y - 4.0)
    w = max(0.0, min(1.0, (220.0 - r) / 160.0))
    return z + (height(x, y) - 0.5 - z) * w * w * (3 - 2 * w)


def corrugated(name, rgb, rust=(0.3, 0.13, 0.05), pitch=0.076):
    """Corrugated tin: ridges every `pitch` metres along x + y, rust in blotches."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.3
    n = reb.noise_tex(nodes, links, 1.6, 8, 0.65)
    col = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, tuple(c * 0.6 for c in rgb)), (0.55, rgb), (0.72, rust), (1.0, tuple(c * 0.6 for c in rust))])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    add = nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    links.new(sep.outputs["X"], add.inputs[0])
    links.new(sep.outputs["Y"], add.inputs[1])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / pitch
    links.new(add.outputs[0], mul.inputs[0])
    sine = nodes.new("ShaderNodeMath")
    sine.operation = "SINE"
    links.new(mul.outputs[0], sine.inputs[0])
    reb.bumped(nodes, links, bsdf, sine.outputs[0], 0.6, 0.01)
    return m


def chain_link():
    """Wire mesh you can see through: mostly transparent, grey where the wire is."""
    m, nodes, links, bsdf = reb.nodes_material("Chain link")
    bsdf.inputs["Base Color"].default_value = (0.12, 0.12, 0.115, 1)
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.5
    out = nodes["Material Output"]
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, 3, 4, 0.5)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.3, (0.65, 0.65, 0.65)), (0.7, (0.82, 0.82, 0.82))])
    links.new(r.outputs["Color"], mix.inputs["Fac"])
    links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    links.new(clear.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


def logs_mesh(name, logs, m, sides=10):
    """Fence rails and posts as one mesh: [(a, b, r)], capped cylinders with a ragged bark edge."""
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
                rr = r * (1 + 0.08 * math.sin(3 * t + a.x) + 0.04 * math.sin(7 * t + a.y))
                verts.append(tuple(end + (side * math.cos(t) + up * math.sin(t)) * rr))
        for i in range(sides):
            faces.append((k + i, k + (i + 1) % sides, k + sides + (i + 1) % sides, k + sides + i))
        faces.append(tuple(k + i for i in reversed(range(sides))))
        faces.append(tuple(k + sides + i for i in range(sides)))
    return reb.mesh_object(name, verts, faces, m)


def settle(ob, at, rot):
    """Bake a joined object's parts where they were built, then place it."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def build():
    rng = random.Random(4)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # mud and forest floor
    cams = [
        ((1.6, 12.0, 3.4), (11.6, 4.2, 0.7), "from the road coming in: the ruts bending to the gate, the strewn logs, the pickup shoved aside"),
        ((13.0, 2.6, 3.6), (4.2, 10.6, 0.3), "from beside the gate, looking back down the road: the barricade, the logger, the road into the trees"),
        ((11.0, 13.4, 3.7), (9.8, 2.6, 1.6), "from the south, square on: the gate and its sign, the gap, the camp beyond"),
    ]
    for eye, look, note in cams:
        room.camera(eye, look, 200, note)

    mud = kit.dirtied(reb.mat_surface("Yard mud", [(0.0, (0.04, 0.03, 0.02)), (0.35, (0.08, 0.06, 0.04)), (0.6, (0.13, 0.1, 0.07)), (0.8, (0.1, 0.09, 0.06)), (1.0, (0.07, 0.075, 0.04))], scale=1.4, detail=14, rough=0.75, bump=0.7), 0.7, scale=0.35)
    logs_m = mat("bark")
    end_m = reb.mat_surface("Sawn log ends", [(0.0, (0.2, 0.13, 0.07)), (0.5, (0.4, 0.29, 0.16)), (1.0, (0.28, 0.18, 0.1))], scale=9, bump=0.3)
    pole_m = reb.mat_surface("Grey poles", [(0.0, (0.12, 0.1, 0.08)), (1.0, (0.24, 0.21, 0.17))], scale=8, bump=0.6)
    ply = reb.mat_surface("Plywood", [(0.0, (0.22, 0.16, 0.09)), (0.7, (0.32, 0.24, 0.14)), (1.0, (0.12, 0.09, 0.06))], scale=5, bump=0.15)
    tin = corrugated("Fence tin", (0.2, 0.2, 0.19))
    truck_m = reb.mat_surface("Pickup paint", [(0.0, (0.05, 0.1, 0.16)), (0.6, (0.08, 0.15, 0.22)), (0.85, (0.06, 0.1, 0.13)), (1.0, (0.2, 0.09, 0.04))], scale=3, rough=0.5, bump=0.15)
    whitewash = reb.mat_surface("Scrawl paint", [(0.0, (0.55, 0.53, 0.48)), (1.0, (0.65, 0.63, 0.58))], scale=20, bump=0.05)

    # ---- Ground: mud over everything, grassed off the road and the turning space; the road and its ruts.
    reb.terrain("Ground", mat("grassed earth"), (-30, 50), (-40, 40), height, step=0.4)
    reb.terrain("Camp ground", mud, (-6, 34), (-24, FENCE_Y - 0.1), lambda x, y: height(x, y) + 0.006, step=0.5)
    on_road = kit.dirt_path("Road in", ROAD, height, width=3.4)
    # It runs on past both edges of the floor, so where the mud ends square the grass
    # keep-out ends with it: no bald ground between the two.
    on_turn = kit.dirt_path("Turning space", [(-2.0, 7.4), (3.6, 6.4), (9.8, 5.2), (16.2, 6.6), (21.0, 7.6)], height, width=7.0, m=mud)
    kit.lay_on_ground(kit.ruts("Ruts", ROAD, height, gauge=1.65, width=0.36, seed=4.0), height, 0.02)
    # Where the pickup was shoved out sideways: its tyres scored the mud in two short arcs.
    kit.lay_on_ground(kit.ruts("Pickup's skid", [(10.2, 2.6), (11.4, 3.3), (12.6, 4.2), (13.4, 5.0)], height, gauge=1.5, width=0.26, seed=9.0), height, 0.021)

    stones = [(rng.uniform(X0, X1), rng.uniform(Y0, Y1), rng.uniform(0.02, 0.07)) for _ in range(90)]
    kit.rocks("Stones in the mud", rng, stones, height, kit.dirtied(mat("rock"), 0.7), grass=False)
    cv, cf = [], []
    for _ in range(700):
        x, y = rng.uniform(X0 - 2, X1 + 2), rng.uniform(Y0 - 0.2, Y1 + 2)
        reb.card(cv, cf, Vector((x, y, height(x, y) + 0.008)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), rng.uniform(0.03, 0.07), rng.uniform(0.06, 0.2), 0.0)
    reb.mesh_object("Bark and needles in the mud", cv, cf, mat("dead needles"), smooth=False)

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
    for z in (2.2, 2.35):
        for (a, b) in (((-12.0, FENCE_Y, z), (GATE[0], FENCE_Y, z)), ((GATE[1], FENCE_Y, z), (32.0, FENCE_Y, z))):
            kit.rod("Barbed wire", mat("rust"), a, b, 0.006, 4)
    sheets = [(-4.6, ply, 0.0), (-1.8, tin, 0.05), (2.2, ply, -0.04), (3.6, tin, 0.0), (6.6, ply, 0.03), (13.4, tin, 0.0), (15.8, ply, -0.05), (18.4, tin, 0.02), (21.2, ply, 0.0)]
    for i, (x, m, tilt) in enumerate(sheets):
        reb.prim("cube", f"Fence sheet {i}", m, (x, FENCE_Y + 0.22, 1.15), (1.22, 0.02, 2.0 if m is ply else 1.8), rot=(0, tilt, 0))
    reb.prim("cube", "Sheet torn half off", tin, (0.6, FENCE_Y + 0.6, 0.7), (1.2, 0.02, 1.8), rot=(0.5, 0.3, 0.2))
    # KEEP OUT, slapped on in white paint, on the sheet west of the gate.
    sx = 5.0
    reb.prim("cube", "Sign sheet", ply, (sx, FENCE_Y + 0.24, 1.25), (1.6, 0.02, 1.15), rot=(0, 0.02, 0))
    kit.fit_text(kit.text("Scrawl KEEP OUT", "KEEP OUT", whitewash, (sx, FENCE_Y + 0.26, 1.3), size=0.3, rot=(math.pi / 2, -0.05, math.pi)), 1.4)
    for k in range(4):
        reb.prim("cube", f"Paint run {k}", whitewash, (sx - 0.5 + k * 0.33, FENCE_Y + 0.255, 1.08 - 0.05 * k), (0.015, 0.004, 0.16 + 0.05 * k))

    # ---- The gate: two log posts and a beam, the company's sign on chains, the leaves hanging open.
    for x in GATE:
        reb.mask(kit.rough_log("Gate post", (x, FENCE_Y, -0.3), (x + 0.02, FENCE_Y, 4.6), 0.2, m=logs_m, seed=int(x * 10), stubs=0, sawn=end_m))
        reb.mask(reb.wall(reb.prim("cyl", "Gate post footprint", None, (x, FENCE_Y, 1.0), (0.4, 0.4, 2.0)), "circle")).hide_render = True
    reb.mask(kit.rough_log("Gate beam", (GATE[0] - 0.5, FENCE_Y, 4.35), (GATE[1] + 0.5, FENCE_Y, 4.38), 0.18, m=logs_m, seed=5, stubs=0, sawn=end_m))
    sign_hook = reb.prim("cube", "Sign hook", mat("iron"), ((GATE[0] + GATE[1]) / 2, FENCE_Y + 0.15, 4.17), (2.6, 0.05, 0.04))
    board = reb.prim("cube", "Company sign", kit.boards("Sign boards", (0.22, 0.15, 0.09), width=0.16, grime=0.8), (0, 0, -0.42), (2.7, 0.07, 0.5))
    words = kit.text("Company sign words", "ARKLAY TIMBER CO.", mat("white paint"), (0, 0.04, -0.42), size=0.24, rot=(math.pi / 2, 0, math.pi))
    kit.fit_text(words, 2.4)
    claws = kit.scratches("Claws on the sign", mat("black"), (0.7, 0.04, -0.25), (0, 1), count=4, length=0.3, seed=3)
    for p in (board, words, claws):
        p.parent = sign_hook
    for dx in (-1.2, 1.2):
        kit.rod("Sign chain", mat("iron"), (dx, 0, 0), (dx, 0, -0.17), 0.012, 4).parent = sign_hook
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
    leaf("West gate leaf", (GATE[0] + 0.2, FENCE_Y + 0.2, 1.0), 1.6, 1.25, drop=0.25)
    leaf("East gate leaf", (GATE[1] - 0.2, FENCE_Y + 0.2, 1.0), -1.6, -1.05)
    for k, (x, y, z, f) in enumerate(((GATE[0] + 0.55, FENCE_Y + 1.15, 1.25, (-1, 0.3)), (GATE[1] - 0.45, FENCE_Y + 1.2, 1.3, (1, 0.3)), (GATE[1] - 0.3, FENCE_Y + 0.8, 0.8, (1, 0.3)))):
        kit.scratches(f"Claws on the gate {k}", reb.mat_plain("Splintered wood", (0.42, 0.32, 0.2), 0.8), (x, y, z), f, count=5, length=0.55, seed=20 + k)
    reb.wall(reb.prim("cube", "West leaf footprint", None, (GATE[0] + 0.5, FENCE_Y + 0.9, 0.5), (0.6, 1.4, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "East leaf footprint", None, (GATE[1] - 0.6, FENCE_Y + 0.85, 0.5), (0.7, 1.3, 1.0))).hide_render = True

    # ---- The cold deck the barricade came from, along the fence west of the gate.
    deck = []
    for row, (n, z) in enumerate(((5, 0.26), (4, 0.72), (2, 1.16))):
        for i in range(n):
            x0 = 1.3 + rng.uniform(-0.2, 0.2)
            deck.append(((x0, 2.15 + 0.47 * i + 0.23 * row, z), (x0 + 4.2 + rng.uniform(-0.3, 0.3), 2.2 + 0.47 * i + 0.23 * row + rng.uniform(-0.08, 0.08), z + rng.uniform(-0.03, 0.03)), rng.uniform(0.21, 0.26)))
    for k, (a, b, r) in enumerate(deck):
        reb.mask(kit.rough_log(f"Cold deck log {k}", a, b, r, m=logs_m, seed=60 + k, stubs=1, sawn=end_m))
    reb.mask(reb.wall(reb.prim("cube", "Cold deck footprint", None, (3.4, 3.1, 0.5), (4.6, 2.4, 1.0)))).hide_render = True

    # ---- What is left of the barricade: logs against the west post, the rest strewn over the road.
    pile = [((6.6, 2.4, 0.26), (9.0, 2.3, 0.27), 0.27), ((6.8, 3.0, 0.25), (9.1, 2.9, 0.25), 0.26), ((6.7, 2.65, 0.7), (8.9, 2.6, 0.72), 0.25),
            ((6.9, 3.5, 0.22), (8.5, 3.6, 0.2), 0.23)]
    strewn = [((9.6, 4.5, 0.2), (12.0, 6.3, 0.2), 0.25), ((3.8, 6.2, 0.18), (6.2, 7.3, 0.18), 0.24), ((8.4, 8.4, 0.18), (11.0, 7.9, 0.18), 0.23),
              ((16.0, 8.4, 0.2), (17.3, 10.4, 0.2), 0.24), ((2.4, 5.0, 0.17), (4.4, 4.4, 0.17), 0.22)]
    for k, (a, b, r) in enumerate(pile):
        reb.mask(kit.rough_log(f"Barricade log {k}", a, b, r, m=logs_m, seed=80 + k, stubs=1, sawn=end_m))
    reb.wall(reb.prim("cube", "Barricade footprint", None, (7.8, 3.0, 0.5), (2.6, 1.8, 1.0))).hide_render = True
    for k, (a, b, r) in enumerate(strewn):
        a = (a[0], a[1], height(a[0], a[1]) + r * 0.8)
        b = (b[0], b[1], height(b[0], b[1]) + r * 0.8)
        reb.mask(kit.rough_log(f"Strewn log {k}", a, b, r, m=logs_m, seed=90 + k, stubs=1, sawn=end_m))
        mid, d = (Vector(a) + Vector(b)) / 2, (Vector(b) - Vector(a)).normalized()
        for t in (-0.9, 0.0, 0.9):
            q = mid + d * t
            reb.wall(reb.prim("cube", "Strewn log footprint", None, (q.x, q.y, 0.25), (0.7, 0.7, 0.5))).hide_render = True
    # The rest of it, shoved east along the fence when the pickup came out: logs, torn tin.
    shoved = [((12.5, 2.4), (15.2, 2.6), 0.26), ((15.4, 2.5), (17.9, 2.2), 0.25), ((12.9, 3.15), (15.6, 3.5), 0.24), ((14.2, 2.8), (16.8, 3.0), 0.23)]
    for k, ((ax, ay), (bx, by), r) in enumerate(shoved):
        z = 0.48 if k == 3 else r * 0.85
        reb.mask(kit.rough_log(f"Shoved log {k}", (ax, ay, height(ax, ay) + z), (bx, by, height(bx, by) + z), r, m=logs_m, seed=110 + k, stubs=1, sawn=end_m))
    reb.prim("cube", "Tin torn off the fence", tin, (16.4, 3.85, 0.3), (1.2, 0.02, 1.8), rot=(1.25, 0.1, -0.15))
    reb.wall(reb.prim("cube", "Shoved logs footprint", None, (15.1, 3.0, 0.5), (6.2, 2.2, 1.0))).hide_render = True
    # Spikes and wire the men drove into it, sandbags, a gas can.
    for k in range(5):
        x = 6.8 + k * 0.5
        kit.rod("Spike", mat("rust"), (x, 2.0, 0.85), (x + 0.1, 2.5 + 0.1 * k, 1.3), 0.012, 4)
    for k in range(4):
        reb.prim("cube", f"Sandbag {k}", mat("canvas"), (5.9 + k * 0.4, 4.05 + 0.08 * (k % 2), 0.11), (0.4, 0.26, 0.22), rot=(0, 0, 0.1 * k), bevel=0.07)
    reb.prim("cube", "Gas can", reb.mat_plain("Can red", (0.3, 0.03, 0.02), 0.5), (5.4, 6.0, 0.08), (0.24, 0.14, 0.34), rot=(math.pi / 2, 0, 0.6), bevel=0.02)

    # ---- The logger, face down in the mud in front of the logs, where he fell running for the road.
    lx, ly, lh = LOGGER
    kit.body("Logger in the mud", (lx, ly, height(lx, ly) + 0.01), lh, pose="front",
             top=reb.mat_stripes("Red check", [(0.3, 0.04, 0.03), (0.04, 0.03, 0.03)], across=22), legs=mat("denim"), seed=12)
    soaked = reb.mat_surface("Soaked blood", [(0.0, (0.02, 0.006, 0.004)), (0.5, (0.045, 0.012, 0.007)), (0.8, (0.07, 0.025, 0.014)), (1.0, (0.05, 0.03, 0.02))], scale=25, detail=8, rough=0.92, bump=0.1)
    kit.lay_on_ground(kit.splat("Blood soaked in under him", soaked, (lx - 0.3, ly + 0.2, 0), 0.38, seed=14, stretch=(1.3, 0.9), lumps=0.7), height, 0.01)
    kit.lay_on_ground(kit.drag_trail("Where he crawled", soaked, [(7.6, 4.0), (7.3, 4.3), (7.0, 4.55)], width=0.18, seed=15, height=height), height, 0.011)
    hat = reb.mat_plain("Hard hat", (0.55, 0.38, 0.03), 0.4)
    reb.prim("sphere", "His hard hat", hat, (lx - 1.4, ly + 1.0, 0.07), (0.3, 0.26, 0.2), rot=(0.3, 0.2, 0), segments=14)
    reb.prim("cyl", "Hard hat brim", hat, (lx - 1.4, ly + 1.02, 0.04), (0.36, 0.32, 0.015), rot=(0.3, 0.2, 0), segments=16)
    reb.prim("cube", "His work glove", reb.mat_plain("Leather glove", (0.3, 0.2, 0.1), 0.8), (lx + 0.9, ly + 0.5, 0.02), (0.1, 0.22, 0.04), rot=(0, 0, 0.8), bevel=0.02)

    # ---- The pickup, shoved out sideways through the gap: a slashed tyre, glass gone, bloody hands inside the door.
    px, py, pr = PICKUP
    pickup, hinge = kit.pickup("Pickup", truck_m, door_open=1.1, door_side=1, glass_gone=True, flat=0.18)
    pickup.location = (px, py, height(px, py) + 0.01)
    pickup.rotation_euler = (0.0, 0.0, pr)
    reb.mask(pickup)
    reb.wall(reb.prim("cube", "Pickup footprint", None, (px, py, 0.6), (4.4, 1.9, 1.2), rot=(0, 0, pr))).hide_render = True
    c, s_ = math.cos(pr), math.sin(pr)

    def on_truck(lx_, ly_):
        return Vector((px + lx_ * c - ly_ * s_, py + lx_ * s_ + ly_ * c))
    hands = []
    for k in range(3):
        hands.append(kit.splat(f"Hand inside the door {k}", mat("blood"), (-0.3 - k * 0.25, -0.037, 0.05 + 0.12 * (k % 2)), 0.06, rot=(math.pi / 2, 0, 0), seed=30 + k))
    smear = kit.splat("Smear inside the door", mat("old blood"), (-0.5, -0.037, -0.15), 0.12, rot=(math.pi / 2, 0, 0), seed=34, stretch=(2.2, 0.5))
    for p in [smear] + hands:
        p.parent = hinge
    kit.scratches("Claws on the pickup", reb.mat_plain("Bare metal", (0.35, 0.35, 0.33), 0.3), tuple(on_truck(-1.0, -0.9).to_3d() + Vector((0, 0, 1.1))), (s_, -c), count=5, length=0.4, seed=40)
    kit.shards("Pickup glass", (px + 0.3, py + 1.2, height(px, py)), spread=0.9, count=26, seed=41)
    for k in range(3):
        reb.prim("cube", f"Sandbag in the bed {k}", mat("canvas"), tuple(on_truck(-1.6 + k * 0.5, 0.3 * (k - 1)).to_3d() + Vector((0, 0, 0.88))), (0.42, 0.26, 0.2), rot=(0, 0, pr + 0.2 * k), bevel=0.06)

    # ---- The south side of the turning space: stumps where the clearing was cut, slash, a drum dumped there.
    for i, (x, y, r) in enumerate(((2.0, 7.4, 0.38), (17.5, 3.0, 0.38), (13.6, 11.6, 0.42), (17.2, 7.0, 0.35), (5.6, 12.0, 0.4))):
        st = kit.rough_log(f"Stump {i}", (x, y, height(x, y) - 0.3), (x + 0.03, y - 0.02, height(x, y) + 0.45), r, seed=220 + i, stubs=0, sawn=end_m)
        reb.mask(st)
        reb.wall(reb.prim("cyl", f"Stump {i} footprint", None, (x, y, 0.3), (2 * r, 2 * r, 0.6)), "circle").hide_render = True
    kit.tree_roots(rng, [(Vector((x, y, height(x, y) - 0.2)), 3.0) for x, y in ((2.0, 7.4), (17.5, 3.0), (13.6, 11.6), (17.2, 7.0), (5.6, 12.0))], height)
    for k in range(9):
        x, y = rng.uniform(14.4, 17.6), rng.uniform(9.4, 11.8)
        a = rng.uniform(0, math.tau)
        L = rng.uniform(1.0, 2.2)
        kit.rough_log(f"Slash {k}", (x, y, height(x, y) + 0.04 + 0.05 * (k % 3)), (x + math.cos(a) * L, y + math.sin(a) * L * 0.6, height(x, y) + 0.1 + 0.04 * (k % 3)), rng.uniform(0.03, 0.07), seed=240 + k, stubs=3)
    reb.wall(reb.prim("cube", "Slash footprint", None, (16.0, 10.6, 0.3), (3.4, 2.6, 0.6))).hide_render = True
    stencil_m = kit.dirtied(reb.mat_plain("Stencil white", (0.5, 0.48, 0.42), 0.6), 0.6, scale=20)
    d = kit.drum("Drum by the slash", kit.drum_paint("Gate drum paint", (0.3, 0.06, 0.03)), (13.2, 9.6, height(13.2, 9.6)), rot=0.4)
    kit.stencil(d, ["DIESEL", "No 55-4392"], stencil_m, size=0.11, turn=0.6)
    reb.wall(d, "circle")
    kit.drum("Drum on its side", kit.drum_paint("Gate drum paint 2", (0.06, 0.1, 0.05)), (12.3, 10.4, height(12.3, 10.4)), tipped=True, rot=2.2)
    kit.splat("Diesel soaked in", reb.mat_surface("Oil soak", [(0.0, (0.008, 0.007, 0.006)), (1.0, (0.035, 0.03, 0.024))], scale=10, rough=0.35, bump=0.15),
              (11.6, 10.7, height(11.6, 10.7) + 0.004), 0.35, seed=16, stretch=(1.5, 0.7), lumps=0.6)
    reb.wall(reb.prim("cube", "Tipped drum footprint", None, (12.3, 10.4, 0.3), (0.9, 0.9, 0.6))).hide_render = True

    # On the verge south of the road, by the way in: a windfall across the ditch, ferns and rocks round it.
    reb.mask(kit.rough_log("Windfall on the verge", (3.6, 13.0, height(3.6, 13.0) + 0.12), (8.4, 14.1, height(8.4, 14.1) + 0.15), 0.3, seed=301, stubs=5))
    vv, vf = [], []
    for _ in range(22):
        x, y = rng.uniform(2.4, 8.8), rng.uniform(12.5, 14.6)
        if not on_road(x, y, 0.4):
            reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.65), vv, vf)
    reb.mesh_object("Ferns on the verge", vv, vf, mat("ferns"))
    kit.rocks("Verge rocks", rng, [(4.6, 12.8, 0.35), (7.2, 13.0, 0.28), (2.8, 13.9, 0.4)], height)

    # ---- Beyond the fence: the camp as the yard's scene builds it, moved 17.2 m north.
    def Yd(rect):
        x0, x1, y0, y1 = rect
        return (x0, x1, y0 + YARD, y1 + YARD)
    tin_roof = corrugated("Roof tin", (0.26, 0.26, 0.25))
    tin_wall = corrugated("Workshop tin", (0.22, 0.24, 0.23), pitch=0.1)
    frame_m = mat("dark wood")
    glass_m = reb.mat_glass("Grimy glass", (0.32, 0.34, 0.3))
    work = (13.4, 19.2, 13.8 + YARD, FENCE_Y - 0.4 - T)
    kit.hut("Workshop", work, 3.0, tin_wall, tin_roof, [("w", 15.4 + YARD, 16.6 + YARD, 1.1, 1.9)], ridge="x", pitch=0.42, thick=T, blocks=False)
    kit.hut_window(work, "w", 15.4 + YARD, 16.6 + YARD, 1.1, 1.9, frame_m, glass_m, thick=T, boarded=True)
    mess = Yd((-3.4, 2.0, 5.0, 14.0))
    kit.hut("Mess", mess, 2.8, kit.boards("Mess boards", (0.42, 0.4, 0.36), width=0.18, grime=0.9), tin_roof,
            [("e", 9.0 + YARD, 9.9 + YARD, 0.0, 2.1), ("e", 6.0 + YARD, 7.4 + YARD, 1.0, 1.9), ("e", 11.2 + YARD, 12.6 + YARD, 1.0, 1.9)], ridge="y", pitch=0.46, thick=T, blocks=False)
    for a, b in ((6.0, 7.4), (11.2, 12.6)):
        kit.hut_window(mess, "e", a + YARD, b + YARD, 1.0, 1.9, frame_m, reb.mat_glass("Steamy glass", (0.45, 0.42, 0.36)), thick=T)
    kit.shut_door("Mess door", mess, "e", 9.0 + YARD, 9.9 + YARD, 2.1, mat("white paint"), thick=T)
    reb.prim("cube", "Mess chimney", mat("brick"), (-0.4, 6.0 + YARD, 3.6), (0.6, 0.6, 2.4))
    office = Yd((1.0, 4.6, 0.6, 3.6))
    kit.hut("Office", office, 2.5, kit.boards("Office boards", (0.08, 0.14, 0.09), width=0.16, grime=0.8), tin_roof, [("s", 2.5, 3.4, 0.0, 2.05)], ridge="y", pitch=0.5, eaves=0.3, thick=T, blocks=False)
    kit.shut_door("Office door", office, "s", 2.5, 3.4, 2.05, mat("green paint"), thick=T)
    bunk = Yd((6.0, 17.0, -3.4, 1.6))
    bwin = [(7.0, 8.0), (8.9, 9.9), (13.0, 14.0), (15.0, 16.0)]
    kit.hut("Bunkhouse", bunk, 2.4, kit.boards("Bunkhouse boards", (0.17, 0.11, 0.07), width=0.22, grime=0.8), tin_roof,
            [("s", 11.0, 11.9, 0.0, 2.05)] + [("s", a, b, 1.0, 1.7) for a, b in bwin], ridge="x", pitch=0.48, thick=T, blocks=False)
    for a, b in bwin:
        kit.hut_window(bunk, "s", a, b, 1.0, 1.7, frame_m, glass_m, thick=T)
    kit.shut_door("Bunkhouse door", bunk, "s", 11.0, 11.9, 2.05, mat("planks"), thick=T)
    mill = Yd((18.5, 32.0, 2.6, 12.2))
    kit.hut("Sawmill", mill, 6.0, kit.boards("Mill boards", (0.2, 0.19, 0.17), width=0.3, grime=0.8), tin_roof,
            [("w", 6.0 + YARD, 9.0 + YARD, 0.0, 3.4), ("w", 3.4 + YARD, 5.0 + YARD, 3.8, 4.8)], ridge="x", pitch=0.42, thick=T, blocks=False)
    kit.hut_window(mill, "w", 3.4 + YARD, 5.0 + YARD, 3.8, 4.8, frame_m, glass_m, thick=T)
    for a, b in ((6.0, 7.5), (7.5, 9.0)):
        kit.shut_door("Mill door", mill, "w", a + YARD, b + YARD, 3.4, kit.boards("Mill door boards", (0.2, 0.19, 0.17), width=0.3, grime=0.8), thick=T, handle_m=mat("rust"))
    kit.skidder("Skidder", (7.95, 13.0 + YARD, height(7.95, 13.0 + YARD)), heading=0.0)
    # The fuel depot's wire, in the corner west of the gate inside the fence.
    wire = chain_link()
    for a, b in (((-2.0, -2.0), (6.6, -2.0)), ((6.6, -2.0), (6.6, 1.3)), ((-2.0, -2.0), (-2.0, 1.3))):
        a, b = Vector(a), Vector(b)
        dd = b - a
        reb.prim("cube", "Depot wire", wire, ((a.x + b.x) / 2, (a.y + b.y) / 2, 1.0), (dd.length if abs(dd.x) > 0.1 else 0.02, dd.length if abs(dd.y) > 0.1 else 0.02, 2.0))
        n = int(dd.length / 2.0) + 1
        for i in range(n + 1):
            p = a.lerp(b, i / n)
            kit.rod("Depot post", mat("rust"), (p.x, p.y, 0), (p.x, p.y, 2.1), 0.035, 6)
    reb.prim("cyl", "Depot tank", reb.mat_plain("Tank green", (0.1, 0.14, 0.09), 0.5), (2.6, -0.3, 1.6), (1.4, 1.4, 3.4), rot=(0, math.pi / 2, 0), segments=20)
    for x in (1.4, 3.8):
        reb.prim("cube", "Tank stand", mat("rust"), (x, -0.3, 0.45), (0.15, 1.2, 0.9))

    # ---- The forest: dense spruce right round the clearing and the camp, far spruce beyond, then the ranges.
    eyes = [(e[0], e[1]) for e, _, _ in cams]

    def keep_out(x, y):
        if -5.0 < x < 34.0 and -24.0 < y < FENCE_Y + 2.4:
            return True
        if X0 - 1.0 < x < X1 + 1.0 and y < Y1 + 0.8:
            return True
        if on_road(x, y, 1.6):
            return True
        return any((x - cx) ** 2 + (y - cy) ** 2 < 16 for cx, cy in eyes)
    kit.forest(rng, height, keep_out, (-18, -34, 40, 32), count=260, spacing=1.7, tall=(14, 23), ferns=160, needles=900, dead=0.08)
    kit.forest(rng, height, lambda x, y: keep_out(x, y) or any((x - cx) ** 2 + (y - cy) ** 2 < 36 for cx, cy in eyes), (-6, -2, 26, 22), count=90, spacing=1.4, tall=(12, 20), ferns=40, needles=300)
    kit.far_spruces(rng, height, keep_out=lambda x, y: -18 < x < 40 and -34 < y < 32 or on_road(x, y, 2.5), count=1000, area=(-70, -70, 90, 90))

    def no_grass(x, y):
        return y < FENCE_Y + 0.3 or on_road(x, y) or on_turn(x, y)
    grass = kit.grass_ground(rng, (-4, FENCE_Y, 22, 16), height, keep_out=no_grass, per_m2=22)
    kit.grass_ground(rng, (-4, FENCE_Y, 22, 16), height, keep_out=no_grass, per_m2=4, m=mat("dead grass"))
    kit.rocks("Rocks", rng, [(-1.5, 6.0, 0.8), (19.6, 12.0, 0.9), (0.2, 13.4, 0.7), (19.4, 4.6, 0.6)], height)

    # ---- Light: noon under cloud; the RE0 sky and ranges over the trees.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.2, mist=((10.0, 2.0, 5.0), (90.0, 90.0, 18.0), 0.011),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.15))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(30)
    kit.overcast_sky(glow=(0.6, -1.0))
    kit.backdrop((9.0, 4.0, 3.5), spread=360, below=-40.0, near=60.0, forest_to=1800.0, trees=110000,
                 keep_out=lambda x, y: math.hypot(x - 9.0, y - 4.0) < 56, shape=far_land, mist=30.0, rng=random.Random(12))

    anim = kit.Anim(16)
    anim.swing(sign_hook, axis=0, degrees=2)
    anim.flies((lx, ly, 0.3), count=9, radius=0.5)

    # ---- What the game needs.
    room.door("logging-road", (X0, 8.4, X0 + 0.6, 11.4), arrive=(2.6, 9.9), face=(1, 0))
    room.door("camp-yard", (GAP[0], Y0, GAP[1], Y0 + 0.6), arrive=(10.1, 3.8), face=(0, 1))
    room.check((sx - 0.9, Y0, sx + 0.9, Y0 + 0.8), "KEEP OUT. Painted in a hurry, the paint still running.")
    room.check((GAP[0], Y0 + 0.6, GAP[1], Y0 + 1.4), "ARKLAY TIMBER CO. Someone's clawed the sign.\nThe gate's hanging open.")
    room.check((GATE[1] - 1.0, Y0 + 0.4, GATE[1] + 0.2, Y0 + 1.6), "The outside of the gate is clawed to splinters.\nSomething wanted in.")
    room.check((lx - 1.6, ly - 0.3, lx + 1.0, ly + 1.5), "A logger, face down in the mud. He was running for the road.")
    room.check((13.2, 6.6, 15.0, 7.8), "The camp truck, shoved out of the gate.\nBloody hands all over the inside of the door. Someone wanted out.")
    room.check((8.4, 3.9, 9.4, 4.6), "The barricade. Logs off the deck, sandbags, spikes. Pulled down, or pushed.")
    room.check((X0, 4.4, 4.6, 5.2), "Logs off the cold deck. They rolled them across the gate.")
    room.export(anim)


build()
