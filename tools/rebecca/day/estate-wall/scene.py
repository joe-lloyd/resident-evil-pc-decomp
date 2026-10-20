"""The Spencer estate's back wall and its iron gate, late in the dusk.

What it tells: the track from the creek ends at a wall twice her height,
grey dressed stone gone green at the foot, ivy pouring over its coping.
The back gate between two stone piers is chained and padlocked. A brass
plaque on the pier says NO TRESPASSING and UMBRELLA CORP., under the red
and white of the company's mark: this is their land. Someone tried to get
out over the gate and didn't: he hangs head down from its spikes on this
side, caught by his trousers, one leg gone below the knee where the dogs
reached him from inside. The crows are at him. His torch lies where it
fell, still on, its battery dying. Over the wall, against the last of the
sky, stand the dark trees of the grounds and, far off, the mansion's
roofline, its tower, and one lit window.

Metres: the floor is x 2-17, y 2-12.4 at z 0. The wall's north face is at
y 12.5, 4.5 m high, with the gate's opening at x 9.2-10.8 between piers.
The track from the creek comes down the wall path (below) into the
clearing's north edge at x 11-13.5 and runs to the gate. Forest on the
other three sides.

The wall path: the way north to the creek is part of the room now. From
the clearing's north edge the track runs on about 8 m, 2.6-3.4 m wide,
between an older wall of the estate's park on the east and a drop to the
creek valley on the west, the spruces' tops level with her and the last of
the sun beyond them. The park wall is 2.8 m high, broken bottle glass set
in its coping, and it steps out 0.6 m at a pier halfway, so the path
jinks. Something came over it from the inside: claw marks run down the
stone from the glass to the ground in three places, pale in the grime,
and a torn shirt hangs bloodied from the glass where it caught. A crow
pecks on the pier. The path's far end is the way on to the creek.

Metres: the scene is built in its own coordinates and shifted y +6.6 at
export. The floor is x 2-17, y -5.95-12.4; north of y 2 only the path is
floor, x 10.8-13.6 to y -1, x 10.2-13.6 to y -3.6, x 11.4-14.2 to the end.
The park wall's west face is at x 13.6 south of y -3.6 and x 14.2 north
of it, with a pier at the step.

State "open-gate" (the lock's flag, scripts.ts): the gate key turns, the
chain slides off into the gravel and the leaves swing in, the man on the
spikes going with the west leaf, played as it happens.

Moving: the ivy in the wind, a crow flapping and a crow pecking, the torch
flickering, the grass, the shirt on the glass flapping, the crow on the
pier pecking.
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

X0, X1, Y0, Y1 = 2.0, 17.0, 2.0, 12.4
WALL_Y, WALL_H, WALL_T = 12.5, 4.5, 0.6
GATE = (9.2, 10.8)
SHIFT = (0.0, 6.6)
Y_N = -5.95   # the floor's north end, the path's far end (0.65 m in the game)
# The wall path north of the clearing: walkable strips (y0, y1, x0, x1), south to north.
STRIPS = ((-1.0, Y0, 10.8, 13.6), (-3.6, -1.0, 10.2, 13.6), (Y_N, -3.6, 11.4, 14.2))
PARK_H = 2.8
PARK = ((13.6, 14.2, -3.6, 1.6), (14.2, 14.8, -40.0, -3.6))   # the park wall's two runs: x0, x1, y0, y1


def lip(y):
    """The drop's edge west of the path, a little short of the walkable strip's side."""
    xs = [s[2] for s in STRIPS if s[0] - 0.5 < y < s[1] + 0.5] or [STRIPS[-1][2]]
    return min(xs) - 0.3 - 0.12 * (1 + noise.noise(Vector((0.0, y * 0.8, 3))))


def height(x, y):
    """Flat where she walks; the ground rising a little into the forest; north of
    the clearing the path flat along the park wall and the valley falling away west."""
    h = 0.04 * noise.noise(Vector((x * 0.4, y * 0.4, 5)))
    if y > WALL_Y - 0.2:
        return -0.05
    ox = max(0.0, X0 - 0.5 - x, x - X1 - 0.5)
    oy = max(0.0, Y0 - 0.5 - y)
    o = math.hypot(ox, oy)
    ground = h + 0.06 * o + 0.3 * noise.noise(Vector((x * 0.15, y * 0.15, 1))) * min(1.0, o / 3)
    if y > 1.0:
        return ground
    e = lip(y)
    if x < e:
        d = e - x
        drop = -min(44.0, 1.5 * d + 0.07 * d * d) + 0.8 * noise.noise(Vector((x * 0.2, y * 0.2, 9))) * min(1.0, d / 4)
        f = min(1.0, (1.0 - y) / 1.2)
        return ground * (1 - f) + drop * f
    t = min(1.0, max(0.0, (x - 14.8) / 2.0))
    return h * (1 - t) + ground * t


def ashlar(name, light, dark, mortar=(0.05, 0.05, 0.045), size=(0.55, 0.3)):
    """Dressed stone in courses on a wall along x or y, each block its own
    shade, mottled with grime and green toward the foot."""
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
    n = reb.noise_tex(nodes, links, 1.5, 8, 0.65)
    g = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, (0.35, 0.4, 0.3)), (0.65, (1, 1, 1))])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.85
    links.new(brick.outputs["Color"], mix.inputs["A"])
    links.new(g.outputs["Color"], mix.inputs["B"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    reb.bumped(nodes, links, bsdf, brick.outputs["Fac"], -0.6, 0.02)
    return m


def fill_sun(name, energy, rgb, elevation, heading):
    """A soft second sun: the sky's light from overhead."""
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(90 - elevation), 0, math.radians(heading)))
    s = bpy.context.active_object
    s.name = name
    s.data.energy = energy
    s.data.color = rgb
    s.data.angle = math.radians(12)
    return s


def clear_view(cams, reach=12.0, half_angle=42.0):
    """True where a tree would stand in front of a lens."""
    def f(x, y):
        for (ex, ey), (lx, ly) in cams:
            vx, vy = x - ex, y - ey
            d = math.hypot(vx, vy)
            if d < 4.5:
                return True
            if d < reach:
                fx, fy = lx - ex, ly - ey
                if (vx * fx + vy * fy) / (d * math.hypot(fx, fy)) > math.cos(math.radians(half_angle)):
                    return True
        return False
    return f


def ivy(rng, verts, faces, x0, x1, z0, z1, count, y=WALL_Y - 0.02, facing=-1):
    """Ivy leaves flat on a wall's face (normal `facing` in y), thick at the top, thinning down."""
    up = Vector((0, facing, 0))
    for _ in range(count):
        x = rng.uniform(x0, x1)
        z = z1 - (z1 - z0) * rng.random() ** 1.6
        a = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(a), 0, math.sin(a) - 0.4)).normalized()
        reb.card(verts, faces, Vector((x, y + facing * rng.uniform(0.0, 0.05), z)), out, up, rng.uniform(0.07, 0.12), rng.uniform(0.08, 0.14), -0.5)


def umbrella_mark(name, centre, r, facing_rot):
    """The company's octagon: eight wedges, red and white in turn, in a vertical plane."""
    reds, whites = ([], []), ([], [])
    for i in range(8):
        a0, a1 = 2 * math.pi * i / 8 + math.pi / 8, 2 * math.pi * (i + 1) / 8 + math.pi / 8
        v, f = reds if i % 2 == 0 else whites
        k = len(v)
        v += [(0, 0, 0), (math.cos(a0) * r, 0, math.sin(a0) * r), (math.cos(a1) * r, 0, math.sin(a1) * r)]
        f.append((k, k + 1, k + 2))
    out = []
    for (v, f), m in ((reds, mat("red paint")), (whites, mat("white paint"))):
        ob = reb.mesh_object(name, v, f, m, smooth=False)
        ob.location = centre
        ob.rotation_euler = (0, 0, facing_rot)
        out.append(ob)
    return out


def build():
    rng = random.Random(61)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y_N, X1, Y1), shift=SHIFT)
    room.ground("earth")  # grass and the track
    room.floor((X0, 11.8, X1, Y1), "gravel")  # the strip at the wall's foot
    room.camera((12.3, 0.4, 3.9), (9.8, 12.5, 1.4), 200, "from the track in: the gate, the wall, the mansion's roof over it")
    room.camera((2.6, 11.0, 3.0), (12.5, 9.8, 1.4), 200, "along the wall from the west: the ivy, the piers, the man on the gate")
    room.camera((16.6, 10.8, 3.2), (6.0, 10.2, 1.2), 200, "along the wall from the east: the plaque, the gate, the crows on the coping")
    room.camera((7.4, 8.4, 2.7), (10.0, 12.5, 2.0), 195, "close at the gate: the hanging man, the chain and padlock, the plaque")
    room.camera((1.4, 1.6, 3.9), (10.5, 12.0, 0.4), 200, "from the woods' edge, north-west: the whole wall and the gate")
    room.camera((10.9, 2.6, 3.3), (13.2, -6.0, 0.7), 200, "up the wall path north: the park wall and its glass on the left, the drop and the last of the sun on the right")
    room.camera((10.7, -6.4, 3.4), (12.6, 1.5, 0.6), 200, "down the wall path from its north end: the claw marks, the shirt on the glass, the clearing beyond")

    stone = ashlar("Estate wall", (0.25, 0.25, 0.235), (0.15, 0.155, 0.145))
    pier_stone = ashlar("Pier stone", (0.28, 0.275, 0.26), (0.18, 0.18, 0.17), size=(0.4, 0.32))
    coping_m = reb.mat_surface("Coping", [(0.0, (0.15, 0.155, 0.14)), (0.7, (0.28, 0.28, 0.26)), (1.0, (0.12, 0.16, 0.1))], scale=4, bump=0.5)
    moss = reb.mat_surface("Moss", [(0.0, (0.03, 0.05, 0.02)), (1.0, (0.08, 0.12, 0.04))], scale=8, bump=0.8)
    gate_iron = reb.mat_metal("Gate iron", (0.035, 0.035, 0.035), 0.55)
    brass = reb.mat_metal("Brass", (0.45, 0.33, 0.12), 0.45)
    dark_stone = reb.mat_plain("Mansion stone", (0.025, 0.025, 0.03), 0.9)
    lit = reb.mat_emit("Lit window", (1.0, 0.62, 0.28), 6)
    uniform = reb.mat_surface("Grey uniform", [(0.0, (0.06, 0.065, 0.07)), (0.8, (0.1, 0.105, 0.11)), (1.0, (0.15, 0.02, 0.015))], scale=10, bump=0.2)

    # ---- Ground: the track to the gate, gravel and weeds at the wall's foot.
    reb.terrain("Ground", kit.dirtied(mat("grass"), 0.6, scale=0.7), (-34, 40), (-34, WALL_Y + 0.3), height, step=0.45)
    kit.path_strip("Track from the creek", mat("dirt"), [(12.9, -34.0), (12.9, -7.0), (12.6, -4.6), (11.9, -2.6), (11.9, -0.6), (12.2, 2.5), (11.4, 7.0), (10.3, 10.5), (10.0, 12.4)], height, width=0.7)
    reb.prim("cube", "Gravel at the foot", mat("gravel"), ((X0 + X1) / 2, WALL_Y - 0.35, -0.03), (40.0, 0.7, 0.06))
    reb.prim("cube", "Ground beyond", mat("gravel"), (10.0, WALL_Y + 12.0, -0.08), (60.0, 24.0, 0.1))

    # ---- The wall: dressed stone, buttressed every five metres, coped, mossy at the foot.
    for x0, x1 in ((-22.0, GATE[0] - 0.8), (GATE[1] + 0.8, 42.0)):
        w = reb.prim("cube", "Wall", stone, ((x0 + x1) / 2, WALL_Y + WALL_T / 2, WALL_H / 2), (x1 - x0, WALL_T, WALL_H))
        reb.wall(w)
        reb.prim("cube", "Coping", coping_m, ((x0 + x1) / 2, WALL_Y + WALL_T / 2, WALL_H + 0.08), (x1 - x0, WALL_T + 0.2, 0.16))
        reb.prim("cube", "Moss at the foot", moss, ((x0 + x1) / 2, WALL_Y - 0.005, 0.25), (x1 - x0, 0.01, 0.5))
    for x in (-3.0, 2.0, 6.0, 14.0, 18.0, 23.0):
        reb.wall(reb.prim("cube", "Buttress", stone, (x, WALL_Y - 0.2, 1.2), (0.6, 0.4, 2.4)))
        reb.prim("cube", "Buttress cap", coping_m, (x, WALL_Y - 0.2, 2.45), (0.7, 0.5, 0.12), rot=(-0.4, 0, 0))
    # The gate piers, ball finials on them.
    for side, x in ((-1, GATE[0] - 0.4), (1, GATE[1] + 0.4)):
        pier = reb.prim("cube", "Gate pier", pier_stone, (x, WALL_Y + WALL_T / 2 - 0.1, 2.6), (0.8, 0.85, 5.2))
        reb.mask(reb.wall(pier))
        reb.prim("cube", "Pier cap", coping_m, (x, WALL_Y + WALL_T / 2 - 0.1, 5.28), (0.95, 1.0, 0.16))
        reb.prim("cyl", "Finial neck", coping_m, (x, WALL_Y + WALL_T / 2 - 0.1, 5.45), (0.3, 0.3, 0.2), segments=12)
        reb.prim("sphere", "Finial ball", coping_m, (x, WALL_Y + WALL_T / 2 - 0.1, 5.78), (0.55, 0.55, 0.55), segments=16)
    # The plaque on the west pier: the company's mark over its words.
    px, py = GATE[0] - 0.4, WALL_Y + WALL_T / 2 - 0.1 - 0.425 - 0.016
    reb.prim("cube", "Plaque", brass, (px, py, 1.75), (0.62, 0.03, 0.8), bevel=0.01)
    umbrella_mark("Umbrella mark", (px, py - 0.02, 1.92), 0.17, 0.0)
    kit.text("Plaque words", "NO TRESPASSING", mat("black"), (px, py - 0.02, 1.62), size=0.058)
    kit.text("Plaque words 2", "UMBRELLA CORP.", mat("black"), (px, py - 0.02, 1.52), size=0.058)
    kit.splat("Verdigris", reb.mat_plain("Verdigris", (0.08, 0.2, 0.15), 0.8), (px + 0.2, py - 0.018, 1.45), 0.07, rot=(math.pi / 2, 0, 0), seed=3)

    # ---- The gate: two leaves of spear-topped bars, chained shut. Each leaf
    # turns on its pier, so the gate can swing open into the grounds.
    gy = WALL_Y + 0.2
    gx0, gx1 = GATE
    mid = (gx0 + gx1) / 2
    leaves = []
    for leaf in (0, 1):
        gate_parts = []
        a, b = (gx0, mid - 0.02) if leaf == 0 else (mid + 0.02, gx1)
        n = 7
        for i in range(n):
            x = a + 0.06 + (b - a - 0.12) * i / (n - 1)
            top = 3.0 + 0.35 * math.sin(math.pi * (x - gx0) / (gx1 - gx0))
            gate_parts.append(kit.rod("Bar", gate_iron, (x, gy, 0.05), (x, gy, top), 0.016, 6))
            gate_parts.append(reb.prim("cone", "Spear tip", gate_iron, (x, gy, top + 0.08), (0.06, 0.03, 0.16), segments=4))
        for z in (0.25, 1.4, 2.7):
            gate_parts.append(reb.prim("cube", "Rail", gate_iron, ((a + b) / 2, gy, z), (b - a, 0.04, 0.05)))
        for i in range(3):
            c = Vector(((a + b) / 2 + (i - 1) * 0.22, gy, 2.05))
            for k in range(8):
                t0, t1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
                gate_parts.append(kit.rod("Scroll", gate_iron, c + Vector((math.cos(t0) * 0.1, 0, math.sin(t0) * 0.1)), c + Vector((math.cos(t1) * 0.1, 0, math.sin(t1) * 0.1)), 0.008, 4))
        leaves.append(kit.join(f"Gate leaf {leaf}", gate_parts, origin=(gx0 if leaf == 0 else gx1, gy, 0.0)))
    # It stays a wall once open: the way in is the gate's own zone (room.door).
    reb.wall(reb.prim("cube", "Gate footprint", None, (mid, gy, 0.5), (gx1 - gx0, 0.2, 1.0))).hide_render = True
    links = []
    for k in range(9):
        t0, t1 = k / 9, (k + 1) / 9
        links.append(kit.rod("Chain", mat("rust"), (mid - 0.15 + 0.3 * t0, gy - 0.05, 1.45 - 0.2 * math.sin(math.pi * t0)), (mid - 0.15 + 0.3 * t1, gy - 0.05, 1.45 - 0.2 * math.sin(math.pi * t1)), 0.015, 5))
    gate_chain = kit.join("Gate chain", links, origin=(mid, gy - 0.05, 1.45))
    padlock = reb.prim("cube", "Padlock", brass, (mid, gy - 0.08, 1.2), (0.09, 0.04, 0.11), bevel=0.01)

    # ---- The man on the gate: head down, caught on the spikes, one leg gone; blood down the bars.
    hang = kit.body("Hanging man", (mid - 0.35, gy - 0.32, 3.3), pose="front", top=uniform, legs=uniform, seed=6, missing=("r_foot",))
    hang.rotation_euler = (0.08, math.pi / 2, math.pi / 2)
    trouser = reb.cloth("Torn trouser on a spike", uniform, (mid - 0.42, gy - 0.05, 3.3), (0.12, 0.35), rot=(math.pi / 2, 0, 0.1), cuts=6, lumps=0.02, seed=4)
    for i in range(5):
        kit.rod(f"Blood down the bars {i}", mat("blood"), (mid - 0.5 + i * 0.1, gy - 0.025, 3.0 - rng.uniform(0, 0.4)), (mid - 0.5 + i * 0.1, gy - 0.025, rng.uniform(0.3, 1.6)), 0.008, 4)
    kit.splat("Pool under him", mat("blood"), (mid - 0.3, gy - 0.6, height(mid, gy - 0.6)), 0.5, seed=8, stretch=(1.4, 0.8))
    on_leaf = [hang, trouser] + [ob for ob in bpy.data.objects if ob.name.startswith("Blood down the bars")]
    on_leaf.append(kit.rod("Stump", mat("old blood"), (mid - 0.15, gy - 0.24, 2.86), (mid - 0.15, gy - 0.24, 2.74), 0.065, 8))
    for i in range(4):
        on_leaf.append(kit.rod(f"Drip from the stump {i}", mat("blood"), (mid - 0.15 + rng.uniform(-0.04, 0.04), gy - 0.24, 2.74), (mid - 0.15 + rng.uniform(-0.05, 0.05), gy - 0.24, 2.74 - rng.uniform(0.1, 0.35)), 0.006, 4))
    kit.bones("What fell", (mid + 0.3, gy - 0.9, height(mid, gy - 0.9)), spread=0.4, seed=5, skull=False)
    # His torch, where it fell, still on.
    tx, ty = 8.6, 10.6
    reb.prim("cyl", "Torch", mat("black"), (tx, ty, 0.04), (0.06, 0.06, 0.26), rot=(math.pi / 2, 0, 2.59), segments=10)
    torch_m = reb.mat_emit("Torch lens", (1.0, 0.92, 0.7), 8)
    reb.prim("cyl", "Torch lens", torch_m, (tx + 0.068, ty + 0.11, 0.04), (0.07, 0.07, 0.01), rot=(math.pi / 2, 0, 2.59), segments=10)
    torch = reb.spot("Torch beam", (tx + 0.08, ty + 0.14, 0.06), (mid - 0.3, gy - 0.3, 2.3), 160, (1.0, 0.9, 0.7), 24, 0.4, 0.02)
    kit.papers("Torn papers", (7.6, 10.2, 0.0), spread=0.6, count=3, seed=2)
    reb.prim("cube", "Cap", uniform, (8.0, 9.6, 0.05), (0.25, 0.22, 0.08), rot=(0.1, 0, 0.5), bevel=0.03)

    # ---- Ivy over the coping and down the face, hanging strands; crows along the top.
    iv, if_ = [], []
    for x0, x1, z0, n in ((-4.0, 3.5, 0.6, 1100), (4.5, 8.4, 1.8, 700), (11.8, 15.5, 1.0, 750), (16.5, 25.0, 2.2, 700)):
        ivy(rng, iv, if_, x0, x1, z0, WALL_H + 0.1, n)
    for x0, x1, z0, n in ((GATE[0] - 0.85, GATE[0] + 0.05, 2.6, 160), (GATE[1] - 0.05, GATE[1] + 0.85, 3.4, 140)):
        ivy(rng, iv, if_, x0, x1, z0, 5.2, n, y=WALL_Y - 0.15)
    ivy_ob = reb.mesh_object("Ivy", iv, if_, mat("ivy"), smooth=False)
    for i in range(40):
        x = rng.uniform(-4, 25)
        if GATE[0] - 1 < x < GATE[1] + 1:
            continue
        kit.rod("Ivy stem", reb.mat_plain("Ivy stem", (0.06, 0.05, 0.03), 0.9), (x, WALL_Y - 0.03, WALL_H), (x + rng.uniform(-0.3, 0.3), WALL_Y - 0.04, WALL_H - rng.uniform(0.8, 2.5)), 0.01, 4)
    crows = []
    for i, (x, hd) in enumerate(((5.0, 0.3), (6.3, 3.0), (13.2, 2.2), (15.0, 0.6))):
        crows.append(kit.crow(f"Crow {i}", (x, WALL_Y + 0.25, WALL_H + 0.16), heading=hd))
    pecker, _ = kit.crow("Crow on him", (mid - 0.55, gy - 0.3, 3.36), heading=0.4)
    # He hangs from the west leaf's spikes, and the crow on him: they go with it.
    bpy.context.view_layer.update()
    for ob in on_leaf + [pecker]:
        world = ob.matrix_world.copy()
        ob.parent = leaves[0]
        ob.matrix_world = world
    chain_rest = [(ob, ob.location.copy(), ob.rotation_euler.copy()) for ob in (gate_chain, padlock)]
    ground = height(mid, gy - 0.3)

    def open_gate(t):
        """t 0: chained shut; to 0.3 the unlocked chain slides off the bars
        into the gravel; then the leaves swing in, into the grounds."""
        t = float(t)
        fall = min(1.0, t / 0.3) ** 2
        for k, (ob, loc, rot) in enumerate(chain_rest):
            ob.location = loc + Vector((0.1 * fall * (1 - 2 * k), -0.25 * fall, (ground + 0.03 - loc.z) * fall))
            ob.rotation_euler = (rot.x + 1.4 * fall, rot.y, rot.z + 0.5 * fall * (1 - 2 * k))
        swing = max(0.0, (t - 0.3) / 0.7)
        swing = swing * swing * (3 - 2 * swing)
        leaves[0].rotation_euler = (0, 0, math.radians(78) * swing)
        leaves[1].rotation_euler = (0, 0, -math.radians(84) * swing)
    room.state("open-gate", open_gate, motion=(12, 4))
    flapper, flap_wings = kit.crow("Crow taking off", (GATE[1] + 0.4, WALL_Y + 0.2, 5.95), heading=2.6, perched=False)

    # ---- The wall path north to the creek: the park wall east of it, glass set in its
    # coping, claw marks down it, a strip of uniform caught on the glass; the drop west.
    for x0, x1, y0, y1 in PARK:
        reb.wall(reb.prim("cube", "Park wall", stone, ((x0 + x1) / 2, (y0 + y1) / 2, PARK_H / 2), (x1 - x0, y1 - y0, PARK_H)))
        reb.prim("cube", "Park wall coping", coping_m, ((x0 + x1) / 2, (y0 + y1) / 2, PARK_H + 0.07), (x1 - x0 + 0.16, y1 - y0, 0.14))
        reb.prim("cube", "Moss at the park wall's foot", moss, (x0 - 0.005, (y0 + y1) / 2, 0.22), (0.01, y1 - y0, 0.44))
    pier = reb.prim("cube", "Park wall pier", pier_stone, (14.2, -3.6, 1.65), (1.3, 0.7, 3.3))
    reb.mask(reb.wall(pier))
    reb.prim("cube", "Park pier cap", coping_m, (14.2, -3.6, 3.37), (1.45, 0.85, 0.14))
    # The south end broken down into the thicket, its stones fallen.
    reb.wall(reb.prim("cube", "Park wall stump", stone, (13.9, 1.9, 0.6), (0.6, 0.6, 1.2)))
    sv, sf = [], []
    for _ in range(9):
        reb.boulder(rng, (rng.uniform(13.7, 14.9), rng.uniform(1.9, 3.0), 0.0), rng.uniform(0.12, 0.25), sv, sf, squash=0.7)
    for _ in range(14):
        y = rng.uniform(-14.0, 1.0)
        x = lip(y) - rng.uniform(0.0, 0.5)
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.15, 0.4), sv, sf, squash=0.8)
    reb.mesh_object("Fallen wall stones", sv, sf, mat("rock"))
    green_glass = reb.mat_plain("Bottle glass", (0.06, 0.16, 0.08), 0.08)
    brown_glass = reb.mat_plain("Brown glass", (0.16, 0.08, 0.02), 0.08)
    gv, gf, hv, hf = [], [], [], []
    for x0, x1, y0, y1 in PARK:
        y = max(y0, -24.0)
        while y < y1:
            for _ in range(2):
                v, f = (gv, gf) if rng.random() < 0.6 else (hv, hf)
                base = Vector(((x0 + x1) / 2 + rng.uniform(-0.22, 0.22), y + rng.uniform(-0.03, 0.03), PARK_H + 0.13))
                a = rng.uniform(0, math.pi)
                side = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.04, 0.09)
                k = len(v)
                v += [tuple(base - side), tuple(base + side), tuple(base + side * rng.uniform(-0.6, 0.6) + Vector((0, 0, rng.uniform(0.08, 0.22))))]
                f.append((k, k + 1, k + 2))
            y += 0.09
    reb.mesh_object("Glass on the wall", gv, gf, green_glass, smooth=False)
    reb.mesh_object("Glass on the wall, brown", hv, hf, brown_glass, smooth=False)
    # Claws dragged down the stone from the glass: pale gouges in the grime.
    cv, cf = [], []
    for fx, cy, n in ((PARK[0][0], -1.6, 4), (PARK[0][0], -0.4, 3), (PARK[1][0], -5.0, 4)):
        lean = rng.uniform(-0.25, 0.25)
        for i in range(n):
            ln = rng.uniform(1.5, PARK_H - 0.3)
            z = PARK_H - rng.uniform(0.02, 0.15)
            y = cy + i * 0.09
            steps = 7
            for k in range(steps):
                dz = ln / steps
                dy = lean * dz + rng.uniform(-0.012, 0.012)
                reb.box(cv, cf, (fx - 0.006, y + dy / 2, z - dz / 2), (0.014, 0.035 * (1 - 0.5 * k / steps), dz + 0.01))
                y += dy
                z -= dz
    reb.mesh_object("Claw marks", cv, cf, reb.mat_plain("Fresh-cut stone", (0.44, 0.41, 0.36), 0.9), smooth=False)
    kit.splat("Blood under the claw marks", mat("old blood"), (PARK[1][0] - 0.35, -5.1, height(13.8, -5.1)), 0.25, seed=21, stretch=(0.7, 1.4))
    # The torn shirt on the glass, hanging down the path side.
    rv_, rf_ = [], []
    cols, rows = 4, 8
    for j in range(rows + 1):
        for i in range(cols + 1):
            rv_.append((0.0, (i / cols - 0.5) * (0.45 - 0.15 * j / rows), -j / rows * 1.1))
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            rf_.append((a, a + 1, a + cols + 2, a + cols + 1))
    shirt = reb.mat_surface("Torn shirt", [(0.0, (0.5, 0.48, 0.44)), (0.75, (0.62, 0.6, 0.55)), (0.9, (0.3, 0.03, 0.02)), (1.0, (0.2, 0.02, 0.01))], scale=6, bump=0.2)
    rag = reb.mesh_object("Shirt on the glass", rv_, rf_, shirt, smooth=True)
    rag.location = (PARK[0][0] - 0.04, -2.5, PARK_H + 0.14)
    rag_rest = [Vector(v.co) for v in rag.data.vertices]
    park_crow, _ = kit.crow("Crow on the pier", (14.0, -3.6, 3.44), heading=math.pi - 0.3)
    # Brambles along the clearing's north edge, where the ground starts to fall.
    bv0, bf0 = [], []
    for _ in range(46):
        x, y = rng.uniform(4.0, lip(1.0) - 0.2), rng.uniform(0.7, 2.0)
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.5, 0.85), bv0, bf0)
    reb.mesh_object("Brambles on the edge", bv0, bf0, mat("ferns"))
    def verge(r):
        """Dead grass on the lip of the drop and at the park wall's foot."""
        y = r.uniform(-14.0, 1.5)
        if r.random() < 0.6:
            return lip(y) - r.uniform(-0.1, 0.5), y
        face = PARK[0][0] if y > PARK[0][2] else PARK[1][0]
        return face - r.uniform(0.05, 0.5), y
    lip_grass = kit.meadow(rng, 500, verge, height, mat("dead grass"))

    # ---- Over the wall: the grounds' trees, chain-link runs through the gate, the mansion far off.
    def beyond(x, y):
        return y < WALL_Y + 3 or (8.0 < x < 12.0 and y < WALL_Y + 14)
    kit.forest(rng, lambda x, y: -0.1, lambda x, y: beyond(x, y), (-20, WALL_Y + 3, 40, WALL_Y + 30), count=45, spacing=2.5, tall=(9, 15), ferns=0, needles=0)
    for x in (8.4, 10.2, 12.0):
        kit.rod("Run post", mat("steel"), (x, WALL_Y + 7.0, 0), (x, WALL_Y + 7.0, 2.0), 0.03)
    reb.prim("cube", "Chain-link", reb.mat_surface("Chain link", [(0.0, (0.15, 0.15, 0.14)), (1.0, (0.25, 0.25, 0.23))], scale=60, rough=0.5, bump=0.8), (10.2, WALL_Y + 7.0, 1.0), (3.6, 0.02, 2.0))
    reb.prim("cube", "Kennel hut roof", mat("tin"), (13.5, WALL_Y + 10.0, 2.3), (3.0, 2.5, 0.08), rot=(0.15, 0, 0))
    reb.prim("cube", "Kennel hut", mat("planks"), (13.5, WALL_Y + 10.0, 1.1), (2.6, 2.2, 2.2))
    mz = WALL_Y + 70.0
    reb.prim("cube", "Mansion", dark_stone, (10.0, mz + 10, 8.0), (64.0, 20.0, 16.0))
    for side in (-1, 1):
        reb.prim("cube", "Mansion roof", reb.mat_plain("Mansion slate", (0.018, 0.02, 0.026), 0.6), (10.0, mz + 10 + side * 5.2, 19.0), (64.0, 11.5, 0.4), rot=(-side * 0.68, 0, 0))
    for x, w in ((-14.0, 10.0), (34.0, 10.0)):
        reb.prim("cube", "Mansion wing", dark_stone, (x, mz + 4, 9.5), (w, 14.0, 19.0))
        reb.prim("cone", "Wing roof", reb.mat_plain("Mansion slate", (0.018, 0.02, 0.026), 0.6), (x, mz + 4, 21.5), (w * 1.35, 19.0, 5.0), segments=4, top=0.0, rot=(0, 0, math.pi / 4))
    reb.prim("cube", "Mansion tower", dark_stone, (6.0, mz + 1.0, 14.0), (7.0, 7.0, 28.0))
    reb.prim("cone", "Tower roof", reb.mat_plain("Mansion slate", (0.018, 0.02, 0.026), 0.6), (6.0, mz + 1.0, 31.0), (10.5, 10.5, 6.0), segments=4, top=0.0, rot=(0, 0, math.pi / 4))
    for x in (-5.0, 18.0, 26.0, -10.0):
        reb.prim("cube", "Chimney stack", dark_stone, (x, mz + 9, 22.5), (1.6, 1.6, 4.0))
    for i in range(14):
        x = -18 + i * 4.0
        if 2.0 < x < 10.0:
            continue
        reb.prim("cube", "Dark window", reb.mat_plain("Dark glass", (0.008, 0.01, 0.014), 0.2), (x, mz - 0.05, 12.5), (1.3, 0.1, 2.2))
    reb.prim("cube", "The lit window", lit, (6.0, mz - 2.55, 21.0), (1.4, 0.1, 2.4))
    reb.point("Lit window glow", (6.0, mz - 3.2, 21.0), 400, (1.0, 0.6, 0.28), 0.5)

    # ---- The forest on this side, grass and weeds.
    # The clearing's cameras only: the wall path's look along it, between the park wall and the drop.
    view = clear_view([((c["from"][0] / 1700, c["from"][2] / 1700), (c["to"][0] / 1700, c["to"][2] / 1700)) for c in room.cameras[:5]])

    def keep_out(x, y):
        return (X0 - 1.0 < x < X1 + 1.0 and Y0 - 1.0 < y) or (-16.0 < y < Y0 and lip(y) - 9.0 < x < 17.6) or math.hypot(x - 1.4, y - 1.6) < 8.0 or (y <= -16.0 and abs(x - 12.9) < 1.2) or y > WALL_Y - 1.0 or view(x, y)
    kit.forest(rng, height, keep_out, (-30, -34, 29, WALL_Y), count=170, ferns=30, needles=500, dead=0.08)
    # Tall spruces on the slope below the clearing and the path, their tops at her height and over;
    # the woods closing over the track north of the path, and the park's trees behind its wall.
    kit.forest(rng, height, keep_out, (-14, -16, 4.0, 0.5), count=40, spacing=2.2, tall=(18, 26), ferns=0, needles=0)
    kit.forest(rng, height, keep_out, (4, -34, 26, -14), count=45, spacing=2.0, tall=(12, 20), ferns=10, needles=200)
    kit.forest(rng, height, lambda x, y: keep_out(x, y) or (y > 0.0 and x < 22.0), (15.5, -16, 36, 6.0), count=55, spacing=1.8, tall=(12, 19), ferns=6, needles=150)

    def turf(r):
        while True:
            x, y = r.uniform(X0 - 2, X1 + 2), r.uniform(Y0 - 2, WALL_Y - 0.1)
            if not (GATE[0] - 0.3 < x < GATE[1] + 0.3 and y > WALL_Y - 1.5):
                return x, y
    grass = kit.meadow(rng, 2200, turf, height)
    kit.meadow(rng, 400, lambda r: (r.uniform(-4, 24), r.uniform(WALL_Y - 0.9, WALL_Y - 0.05)), height, mat("dead grass"))
    fv, ff = [], []
    for _ in range(16):
        x = rng.uniform(X0, X1)
        if GATE[0] - 0.5 < x < GATE[1] + 0.5:
            continue
        reb.fern(rng, (x, WALL_Y - 0.5, 0.0), rng.uniform(0.35, 0.6), fv, ff)
    reb.mesh_object("Nettles", fv, ff, mat("ferns"))
    # Brambles and holly crowd the two north corners: the track comes in between them.
    bv, bf, hv, hf, rv, rf = [], [], [], [], [], []
    for (x0, y0, x1, y1) in ((X0 - 1.0, Y0 - 1.0, 4.3, 5.2), (14.8, Y0 - 1.0, X1 + 1.0, 4.6)):
        reb.wall(reb.prim("cube", "Thicket footprint", None, ((x0 + x1) / 2, (y0 + y1) / 2, 0.5), (x1 - x0, y1 - y0, 1.0))).hide_render = True
        for _ in range(int((x1 - x0) * (y1 - y0) * 2.2)):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.5, 0.9), bv, bf)
        for _ in range(int((x1 - x0) * (y1 - y0) * 0.6)):
            c = Vector((rng.uniform(x0 + 0.3, x1 - 0.3), rng.uniform(y0 + 0.3, y1 - 0.3), 0))
            c.z = height(c.x, c.y)
            for _ in range(120):
                d = Vector((rng.gauss(0, 0.4), rng.gauss(0, 0.4), abs(rng.gauss(0.6, 0.35))))
                a_ = rng.uniform(0, 2 * math.pi)
                reb.card(hv, hf, c + d, Vector((math.cos(a_), math.sin(a_), 0.3)).normalized(), Vector((0, 0, 1)), 0.1, 0.14, 0.6)
        reb.boulder(rng, ((x0 + x1) / 2, (y0 + y1) / 2, height((x0 + x1) / 2, (y0 + y1) / 2)), 0.5, rv, rf)
    reb.mesh_object("Brambles", bv, bf, mat("ferns"))
    reb.mesh_object("Holly", hv, hf, mat("leaves"))
    reb.mesh_object("Thicket rocks", rv, rf, mat("rock"))

    # ---- Light: the last red low in the west, blue coming down from above.
    kit.time_light("dusk", sun_heading=280, sun_energy=1.6, sky=((0.62, 0.22, 0.12), (0.05, 0.05, 0.12), 0.65))
    reb.spot("Last light", (-12.0, 4.0, 7.0), (10.0, 11.0, 2.0), 2200, (1.0, 0.4, 0.22), 40, 0.8, 1.5)
    fill_sun("Sky fill", 0.55, (0.4, 0.46, 0.85), 55, 20)
    vb = set(bpy.data.objects)
    kit.vista(rng, (6.0, -8.0), (-1.0, -0.15), below=-46.0, far=(320, 640), haze=(0.4, 0.22, 0.22))
    for ob in set(bpy.data.objects) - vb:
        ob.visible_shadow = False

    anim = kit.Anim(16)
    anim.sway(ivy_ob, amount=0.03, along=(1.0, 0.0), every=2, tip=2)
    anim.sway(grass, amount=0.05)
    anim.flap(flap_wings, degrees=55)
    anim.bob(flapper, height=0.06, speed=2)
    anim.custom(lambda k: setattr(pecker, "rotation_euler", (0, 0.35 * max(0.0, math.sin(anim.phase(k, 3))), 0.4)))
    anim.flicker(torch, torch_m, depth=0.5, dropouts=3)
    anim.sway(lip_grass, amount=0.05)

    def flutter(k):
        ph = anim.phase(k)
        for v, rest in zip(rag.data.vertices, rag_rest):
            t = -rest.z / 1.1
            v.co = (-0.03 - 0.16 * t * (1 + math.sin(ph + t * 3.5)) / 2, rest.y + 0.05 * t * math.sin(2 * ph + t * 4), rest.z + 0.06 * t * t * (1 + math.sin(ph)) / 2)
        rag.data.update()
    anim.custom(flutter)
    anim.custom(lambda k: setattr(park_crow, "rotation_euler", (0, 0.4 * max(0.0, math.sin(anim.phase(k, 2))), math.pi - 0.3)))

    # ---- What the game needs.
    for y0, y1, x0, x1 in STRIPS:
        room.void((X0, y0, x0, y1))
        room.void((x1, y0, X1, y1))
    room.door("creek", (STRIPS[-1][2], Y_N, STRIPS[-1][3], Y_N + 0.6), arrive=(12.8, -4.3), face=(0, 1))
    room.door("kennels", (GATE[0] + 0.1, Y1 - 0.6, GATE[1] - 0.1, Y1), arrive=(10.0, 10.9), face=(0, -1))
    room.check((GATE[0] + 0.1, Y1 - 0.9, GATE[1] - 0.1, Y1), "The estate's back gate. A chain and a padlock.\nI'll need the key.")
    room.check((GATE[0] - 1.0, Y1 - 0.7, GATE[0], Y1), "NO TRESPASSING. UMBRELLA CORP.\nUmbrella. Out here?")
    room.check((mid - 1.0, Y1 - 1.6, mid + 0.6, Y1 - 0.9), "He tried to climb out over the gate.\nSomething on the other side got his leg first.")
    room.check((tx - 0.5, ty - 0.5, tx + 0.5, ty + 0.5), "His torch. It's still on.\nThe batteries are nearly gone.")
    room.check((6.5, 9.0, 8.6, 10.0), "A grey uniform cap. Estate security?")
    room.check((PARK[1][0] - 0.8, -5.3, PARK[1][0], -4.4), "Claw marks, from the glass right down to the ground.\nSomething came over this wall. From the inside.")
    room.check((PARK[0][0] - 0.8, -3.0, PARK[0][0], -2.0), "A shirt, torn on the glass. There's blood on it.\nSomeone tried to get over. Or something dragged them.")
    room.export(anim, samples=128)


build()
