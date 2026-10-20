"""The creek below the Spencer estate, at dusk: a ford, and the gardener's lodge.

What it tells: the valley path comes down to a creek that runs west under
the trees. A line of stepping stones fords it to the far bank, where the
estate gardener's lodge stands: grey stone, a slate roof, its door shut and
padlocked from outside, a lamp still burning behind the one window. He
hasn't been out for days: the woodpile is untouched, his washing still
hangs on the line, and one shirt on it is stiff with blood. Something was
dragged from his door down to the water; a boot lies in the reeds. Upstream
a dog from the kennels has drowned, caught against a fallen log: one of the
estate's Dobermans, its coat gone in raw patches. On the stones of the
south bank lies an adder cut in two by a spade. A sign at the ford says the
land beyond is the Spencer estate's, and the track goes on south to its
back wall.

Metres: the floor is x 2-17, y 2-14 at z 0. The creek runs west to east
across it, its water about y 6.6-9.2, too deep to wade except at the ford
of stepping stones at x 7.9-9.7. The valley path comes in at the north
edge, x 9-12. The lodge is on the south bank, x 2.4-6.4, y 10.4-14.4, its
door in the east wall at y 11.6-12.5. The track to the estate wall leaves
through the south edge at x 11-13.5. The fallen log crosses the creek at
x 13-16 with the dog against it.

Moving: the water, the reeds and grass, midges over the water, the lamp in
the lodge's window.
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

X0, X1, Y0, Y1 = 2.0, 17.0, 2.0, 14.0
FORD = (7.9, 9.7)
LODGE = (2.4, 6.4, 10.4, 14.4)
LODGE_DOOR = (11.6, 12.5)    # y along its east wall
WATER_Z = -0.3


def centre(x):
    """The creek's middle line, wandering a little."""
    return 7.9 + 0.35 * math.sin(x * 0.22 + 0.6)


def height(x, y):
    """Banks flat where she walks, falling into the creek's channel; the
    stony shallows of the ford; rising into the forest outside the floor."""
    d = abs(y - centre(x))
    h = 0.04 * noise.noise(Vector((x * 0.4, y * 0.4, 5)))
    if d < 1.05:
        bed = -0.75 + 0.1 * noise.noise(Vector((x * 0.8, y * 0.8, 2)))
        if FORD[0] - 0.2 < x < FORD[1] + 0.2:
            bed = -0.38
        h = bed
    elif d < 1.9:
        t = (d - 1.05) / 0.85
        h = -0.62 * (1 - t) ** 1.5 + h * t
    ox = max(0.0, X0 - 0.5 - x, x - X1 - 0.5)
    oy = max(0.0, Y0 - 0.5 - y, y - Y1 - 0.5)
    o = math.hypot(ox, oy)
    if o > 0 and d >= 1.9:
        h += 0.06 * o + 0.3 * noise.noise(Vector((x * 0.15, y * 0.15, 1))) * min(1.0, o / 3)
    return h


def ashlar(name, light, dark, mortar=(0.05, 0.05, 0.045), size=(0.5, 0.26), floor=False):
    """Dressed stone in courses: blocks `size` (long, high) metres with mortar
    between, each block its own shade, on walls along x or y alike (or a
    floor of flags). Grime mottles it."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.85
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
    brick.inputs["Mortar Size"].default_value = 0.018
    brick.inputs["Color1"].default_value = (*light, 1)
    brick.inputs["Color2"].default_value = (*dark, 1)
    brick.inputs["Mortar"].default_value = (*mortar, 1)
    links.new(comb.outputs["Vector"], brick.inputs["Vector"])
    n = reb.noise_tex(nodes, links, 3.0, 8, 0.6)
    g = reb.ramp(nodes, links, n.outputs["Fac"], [(0.3, (0.45, 0.42, 0.38)), (0.7, (1, 1, 1))])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.8
    links.new(brick.outputs["Color"], mix.inputs["A"])
    links.new(g.outputs["Color"], mix.inputs["B"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    inv = nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    links.new(brick.outputs["Fac"], inv.inputs[1])
    add2 = nodes.new("ShaderNodeMath")
    add2.operation = "MULTIPLY_ADD"
    add2.inputs[2].default_value = 0.0
    links.new(inv.outputs[0], add2.inputs[0])
    add2.inputs[1].default_value = 1.0
    reb.bumped(nodes, links, bsdf, add2.outputs[0], 0.6, 0.02)
    return m


def fill_sun(name, energy, rgb, elevation, heading):
    """A soft second sun: the sky's light from overhead, which spot lamps far up can't give."""
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(90 - elevation), 0, math.radians(heading)))
    s = bpy.context.active_object
    s.name = name
    s.data.energy = energy
    s.data.color = rgb
    s.data.angle = math.radians(12)
    return s


def clear_view(cams, reach=9.0, half_angle=32.0):
    """True where a tree would stand in front of a lens: within `reach` of a
    camera and inside its view, so the forest leaves it a clear look."""
    def f(x, y):
        for (ex, ey), (lx, ly) in cams:
            vx, vy = x - ex, y - ey
            d = math.hypot(vx, vy)
            if d < 2.5:
                return True
            if d < reach:
                fx, fy = lx - ex, ly - ey
                c = (vx * fx + vy * fy) / (d * math.hypot(fx, fy))
                if c > math.cos(math.radians(half_angle)):
                    return True
        return False
    return f


def dog(name, at, heading, fur, skin, submerged=0.0, seed=0):
    """A dead Doberman lying on its side, legs out stiff, raw where its coat has gone."""
    rng = random.Random(seed)
    parts = [
        reb.prim("sphere", "torso", fur, (0, 0, 0.2), (0.85, 0.32, 0.34), segments=16),
        reb.prim("sphere", "chest", fur, (0.32, 0, 0.22), (0.4, 0.3, 0.38), segments=12),
        reb.prim("sphere", "head", fur, (0.66, 0.02, 0.24), (0.26, 0.17, 0.19), segments=12),
        reb.prim("cone", "snout", fur, (0.85, 0.02, 0.22), (0.12, 0.12, 0.2), rot=(0, math.pi / 2, 0), segments=10, top=0.55),
        reb.prim("cone", "ear", fur, (0.62, 0.06, 0.36), (0.06, 0.04, 0.12), rot=(0.3, -0.2, 0), segments=6),
        reb.prim("cube", "teeth", reb.mat_plain("Teeth", (0.5, 0.45, 0.35), 0.5), (0.86, 0.07, 0.18), (0.14, 0.01, 0.03)),
    ]
    for x in (0.3, -0.28):
        for dz in (0.0, 0.12):
            parts.append(kit.rod("leg", fur, (x, 0.08, 0.12 + dz), (x + rng.uniform(-0.1, 0.12), 0.5, 0.1 + dz), 0.035, 6))
    parts.append(kit.rod("tail", fur, (-0.42, 0, 0.22), (-0.6, 0.05, 0.2), 0.025, 6))
    for i in range(4):
        parts.append(reb.prim("sphere", "raw patch", skin, (rng.uniform(-0.3, 0.3), -0.1, rng.uniform(0.25, 0.32)), (rng.uniform(0.12, 0.22), 0.25, 0.12), segments=8))
    ob = kit.join(name, parts)
    ob.location = (at[0], at[1], at[2] - submerged)
    ob.rotation_euler = (0, 0, heading)
    return ob


def build():
    rng = random.Random(31)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # grass and the dirt paths
    room.floor((FORD[0], 6.6, FORD[1], 9.2), "water")  # the ford
    room.camera((2.8, 2.5, 3.4), (10.0, 10.2, 0.0), 200, "from the north bank, west: the creek, the ford, the lodge's lit window across the water")
    room.camera((18.4, 1.3, 3.9), (8.0, 9.5, 0.0), 200, "from the north bank, east: the drowned dog at the log, the ford, the lodge beyond")
    room.camera((16.6, 13.7, 3.3), (8.0, 6.5, 0.0), 200, "from the south bank, east: back across the creek to the path in, the track south")
    room.camera((12.6, 13.8, 3.2), (5.0, 10.8, 0.6), 200, "on the south bank: the lodge's door, padlocked, the drag marks to the water")
    room.camera((11.4, 2.3, 3.8), (8.8, 11.0, 0.0), 200, "from the valley path: down to the ford and over to the far bank")

    stone = ashlar("Estate stone", (0.24, 0.235, 0.22), (0.15, 0.15, 0.145))
    slate = reb.mat_surface("Slate", [(0.0, (0.03, 0.035, 0.04)), (1.0, (0.08, 0.085, 0.09))], scale=9, rough=0.6, bump=0.4)
    door_m = kit.boards("Lodge door", (0.16, 0.1, 0.05), width=0.14, grime=0.7)
    fur = reb.mat_surface("Wet dog", [(0.0, (0.02, 0.015, 0.012)), (0.7, (0.05, 0.035, 0.025)), (1.0, (0.25, 0.12, 0.05))], scale=9, rough=0.3, bump=0.3)
    raw = reb.mat_surface("Raw flesh", [(0.0, (0.15, 0.02, 0.02)), (0.6, (0.3, 0.06, 0.05)), (1.0, (0.35, 0.2, 0.15))], scale=15, rough=0.4, bump=0.4)
    adder = reb.mat_stripes("Adder", [(0.1, 0.09, 0.06), (0.02, 0.02, 0.015)], across=30, axis="X")
    shirt = reb.mat_surface("Bloody shirt", [(0.0, (0.4, 0.38, 0.33)), (0.5, (0.42, 0.4, 0.34)), (0.65, (0.2, 0.02, 0.01)), (1.0, (0.1, 0.004, 0.003))], scale=4, bump=0.1)
    bed_m = reb.mat_surface("Creek bed", [(0.0, (0.03, 0.03, 0.02)), (1.0, (0.09, 0.08, 0.06))], scale=4, bump=0.6)
    window_glow = reb.mat_emit("Lodge window", (1.0, 0.55, 0.22), 3.0)

    # ---- Ground, creek bed, the water.
    reb.terrain("Banks", kit.dirtied(mat("grass"), 0.6, scale=0.7), (-14, 33), (-12, 30), height, step=0.4)
    reb.terrain("Creek bed", bed_m, (-14, 33), (5.0, 11.0), lambda x, y: height(x, y) - 0.02, step=0.5)
    water = reb.prim("cube", "Creek", mat("water"), (9.5, 8.0, WATER_Z - 0.01), (48, 3.6, 0.02))
    room.void((X0, 6.6, FORD[0], 9.2))
    room.void((FORD[1], 6.6, X1, 9.2))
    kit.path_strip("Valley path", mat("dirt"), [(10.6, -8.0), (10.5, -2.0), (10.4, 2.5), (9.6, 5.0), (8.8, 6.3)], height, width=0.6)
    kit.path_strip("Track to the wall", mat("dirt"), [(8.8, 9.6), (9.6, 11.0), (11.0, 12.2), (12.2, 13.6), (12.6, 18.0), (12.9, 30.0)], height, width=0.65)
    kit.path_strip("To the lodge door", mat("dirt"), [(9.4, 11.4), (8.0, 12.0), (6.6, 12.05)], height, width=0.4)

    # ---- The ford: stepping stones, wet, the water pushing round them; rocks along the banks.
    sv, sf = [], []
    y = 6.55
    i = 0
    while y < 9.5:
        x = 8.8 + 0.25 * math.sin(i * 1.7)
        reb.boulder(rng, (x, y, -0.18), rng.uniform(0.26, 0.33), sv, sf, squash=0.65)
        y += rng.uniform(0.5, 0.62)
        i += 1
    reb.mesh_object("Stepping stones", sv, sf, mat("wet rock"))
    rv, rf = [], []
    for _ in range(40):
        x = rng.uniform(-6, 26)
        side = rng.choice((-1, 1))
        y = centre(x) + side * rng.uniform(0.9, 1.5)
        if FORD[0] - 0.3 < x < FORD[1] + 0.3:
            continue
        reb.boulder(rng, (x, y, height(x, y) + 0.05), rng.uniform(0.15, 0.4), rv, rf, squash=0.6)
    reb.mesh_object("Bank stones", rv, rf, mat("wet rock"))
    # Foam where the water breaks on the stones.
    fv, ff = [], []
    for _ in range(90):
        x = rng.uniform(FORD[0], FORD[1])
        yy = rng.uniform(6.7, 9.2)
        kit._stain(fv, ff, rng, (x, yy, WATER_Z + 0.005), rng.uniform(0.02, 0.05), rng.uniform(0, 3), 0.4, (2.5, 0.5), i, points=8, drops=False)
    reb.mesh_object("Foam", fv, ff, reb.mat_plain("Foam", (0.16, 0.17, 0.16), 0.7), smooth=False)

    # ---- The fallen log across the creek upstream, and the dog caught against it.
    log = kit.rod("Fallen log", mat("bark"), (12.6, 5.6, 0.05), (16.6, 10.4, 0.0), 0.28, 10)
    reb.mask(log)
    for t in (0.0, 1.0):
        p = Vector((12.6, 5.6)).lerp(Vector((16.6, 10.4)), t)
        reb.prim("cyl", "Log end", reb.mat_wood("Rotten heartwood", (0.25, 0.17, 0.09)), (p.x, p.y, 0.03), (0.54, 0.54, 0.02), rot=(math.pi / 2, 0, math.atan2(4.8, 4.0) + math.pi / 2), segments=10)
    for k in (0.15, 0.85):
        p = Vector((12.6, 5.6)).lerp(Vector((16.6, 10.4)), k)
        reb.wall(reb.prim("cube", "Log footprint", None, (p.x, p.y, 0.3), (0.7, 0.7, 0.6))).hide_render = True
    for i in range(6):
        p = Vector((12.6, 5.6, 0.05)).lerp(Vector((16.6, 10.4, 0.0)), rng.uniform(0.1, 0.9))
        a = rng.uniform(0, 2 * math.pi)
        kit.rod("Dead branch", mat("bark"), p, p + Vector((math.cos(a) * 0.8, math.sin(a) * 0.8, rng.uniform(0.2, 0.8))), 0.03, 5)
    dog("Drowned dog", (14.1, 7.6, WATER_Z - 0.02), 0.9 + math.pi, fur, raw, submerged=0.0, seed=2)
    kit.splat("Scum round the dog", reb.mat_plain("Scum", (0.12, 0.1, 0.06), 0.6), (14.3, 7.8, WATER_Z + 0.004), 0.55, seed=9, stretch=(1.4, 0.8))
    kit.rod("Collar chain", mat("rust"), (14.45, 7.4, WATER_Z + 0.08), (14.7, 7.0, WATER_Z + 0.02), 0.012, 4)
    reb.prim("cube", "Tag", mat("steel"), (14.75, 6.95, WATER_Z + 0.02), (0.05, 0.04, 0.005))

    # ---- The lodge: grey stone, a slate roof, a chimney, the door padlocked, the window lit.
    lx0, lx1, ly0, ly1 = LODGE
    for ob in kit.walls(lx0 + 0.5, ly0 + 0.5, lx1 - 0.5, ly1 - 0.5, 2.6, stone, openings=[
        ("e", LODGE_DOOR[0], LODGE_DOOR[1], 0.0, 2.0),
        ("n", 3.6, 4.6, 1.0, 1.8),
    ], thick=0.5, name="Lodge wall"):
        reb.wall(ob)
        reb.mask(ob)
    for side in (-1, 1):
        reb.prim("cube", "Roof slope", slate, ((lx0 + lx1) / 2 + side * 1.1, (ly0 + ly1) / 2, 3.36), (2.75, ly1 - ly0 + 0.6, 0.12), rot=(0, side * 0.57, 0))
    gable_v = [(lx0 + 0.1, ly0 + 0.1, 2.6), (lx1 - 0.1, ly0 + 0.1, 2.6), ((lx0 + lx1) / 2, ly0 + 0.1, 4.0)]
    reb.mesh_object("Gable north", gable_v, [(0, 1, 2)], stone, smooth=False)
    reb.mesh_object("Gable south", [(x, ly1 - 0.1, z) for x, _, z in gable_v], [(0, 2, 1)], stone, smooth=False)
    reb.prim("cube", "Ridge tiles", slate, ((lx0 + lx1) / 2, (ly0 + ly1) / 2, 4.0), (0.25, ly1 - ly0 + 0.6, 0.12))
    reb.prim("cube", "Chimney", stone, (lx0 + 0.8, ly1 - 1.0, 4.0), (0.6, 0.6, 1.6))
    reb.prim("cube", "Chimney cap", mat("concrete"), (lx0 + 0.8, ly1 - 1.0, 4.85), (0.75, 0.75, 0.1))
    # Window: four lit panes in a white frame, the lamp's glow behind.
    reb.prim("cube", "Window glow", window_glow, (4.1, ly0 + 0.4, 1.4), (0.96, 0.05, 0.76))
    for x in (4.1,):
        reb.prim("cube", "Mullion", mat("white paint"), (x, ly0 + 0.15, 1.4), (0.05, 0.08, 0.8))
    reb.prim("cube", "Transom", mat("white paint"), (4.1, ly0 + 0.15, 1.4), (1.0, 0.08, 0.05))
    reb.prim("cube", "Sill", mat("concrete"), (4.1, ly0 + 0.1, 0.97), (1.2, 0.2, 0.06))
    kit.splat("Smear on the glass", mat("blood"), (4.3, ly0 + 0.12, 1.3), 0.12, rot=(math.pi / 2, 0, 0), seed=4, stretch=(0.6, 1.5))
    lamp_light = reb.spot("Window spill", (4.1, ly0 - 0.1, 1.75), (4.1, ly0 - 2.5, 0.0), 90, (1.0, 0.55, 0.25), 80, 0.8, 0.4)
    # The door in the east wall, shut, a hasp and padlock, the frame splintered round it.
    reb.prim("cube", "Lodge door", door_m, (lx1 - 0.3, (LODGE_DOOR[0] + LODGE_DOOR[1]) / 2, 1.0), (0.06, LODGE_DOOR[1] - LODGE_DOOR[0], 2.0))
    reb.prim("cube", "Door lintel", stone, (lx1 - 0.25, (LODGE_DOOR[0] + LODGE_DOOR[1]) / 2, 2.1), (0.55, 1.2, 0.2))
    reb.prim("cube", "Hasp", mat("rust"), (lx1 - 0.26, LODGE_DOOR[0] + 0.12, 1.05), (0.02, 0.2, 0.05))
    reb.prim("cube", "Padlock", mat("iron"), (lx1 - 0.24, LODGE_DOOR[0] + 0.06, 0.97), (0.04, 0.07, 0.09), bevel=0.01)
    reb.prim("cube", "Door step", stone, (lx1 + 0.05, (LODGE_DOOR[0] + LODGE_DOOR[1]) / 2, 0.06), (0.4, 1.2, 0.12))
    kit.scratches("Gouges in the door", mat("pine"), (lx1 - 0.26, 12.05, 1.5), (1, 0), count=6, length=0.7, seed=3)
    kit.splat("Blood on the step", mat("old blood"), (lx1 + 0.1, 12.0, 0.125), 0.2, seed=5)
    # Drag marks from the door down to the water, and a boot in the reeds.
    kit.drag_trail("Drag to the water", mat("old blood"), [(lx1 + 0.4, 12.0), (7.4, 11.0), (7.2, 10.0), (7.0, 9.4)], width=0.35, seed=6, height=height)
    reb.prim("cube", "Boot in the reeds", mat("rubber"), (6.4, 9.7, height(6.4, 9.7) + 0.06), (0.3, 0.12, 0.14), rot=(0.3, 0.2, 2.0), bevel=0.03)
    # Round the lodge: a woodpile, a chopping block, the washing line, a water butt.
    wv, wf = [], []
    for row in range(4):
        for k in range(9 - row):
            x = lx0 + 0.6 + k * 0.32 + row * 0.16
            reb.box(wv, wf, (x, ly0 - 0.3, 0.13 + row * 0.24), (0.26, 0.6, 0.24))
    reb.mesh_object("Woodpile", wv, wf, mat("logs"))
    reb.wall(reb.prim("cube", "Woodpile footprint", None, (lx0 + 1.85, ly0 - 0.3, 0.5), (3.0, 0.7, 1.0))).hide_render = True
    reb.prim("cyl", "Chopping block", mat("logs"), (7.4, 13.3, 0.25), (0.55, 0.55, 0.5), segments=14)
    reb.prim("cube", "Axe head", mat("iron"), (7.4, 13.3, 0.56), (0.18, 0.04, 0.12), rot=(0, 0.2, 0.5))
    kit.rod("Axe handle", mat("pine"), (7.4, 13.3, 0.55), (7.0, 13.6, 1.1), 0.02, 6)
    reb.wall(reb.prim("cube", "Block footprint", None, (7.4, 13.3, 0.3), (0.6, 0.6, 0.6))).hide_render = True
    kit.rod("Line post", mat("dark wood"), (7.0, 14.6, 0), (7.0, 14.6, 1.9), 0.04)
    kit.rod("Line post", mat("dark wood"), (7.4, 17.4, 0), (7.4, 17.4, 1.9), 0.04)
    kit.rod("Washing line", mat("canvas"), (7.0, 14.6, 1.85), (7.4, 17.4, 1.8), 0.006, 4)
    washing = []
    for i, (t, m) in enumerate(((0.2, mat("flannel")), (0.45, shirt), (0.7, mat("sheet")), (0.88, mat("denim")))):
        y = 14.6 + 2.8 * t
        w, hgt = (0.5, 0.6) if i != 2 else (0.9, 1.0)
        washing.append(reb.cloth(f"Washing {i}", m, (7.0 + 0.4 * t, y, 1.8 - hgt / 2), (w, hgt), rot=(math.pi / 2, 0, math.pi / 2 - 0.14), cuts=8, lumps=0.03, seed=i))
    kit.drum("Water butt", reb.mat_wood("Butt staves", (0.15, 0.1, 0.06)), (lx1 + 0.4, ly1 - 0.6, 0.0))
    reb.wall(reb.prim("cube", "Butt footprint", None, (lx1 + 0.4, ly1 - 0.6, 0.5), (0.6, 0.6, 1.0))).hide_render = True
    for i in range(5):
        x, y = lx1 + 0.4 + rng.uniform(-0.1, 0.5), 10.2 + i * 0.25
        reb.prim("cone", f"Flower pot {i}", reb.mat_plain("Terracotta", (0.3, 0.12, 0.06), 0.8), (x, y, 0.1), (0.2, 0.2, 0.2), rot=(math.pi, 0, 0), top=0.7, segments=10)
    reb.prim("cone", "Pot, broken", reb.mat_plain("Terracotta", (0.3, 0.12, 0.06), 0.8), (lx1 + 1.1, 10.7, 0.08), (0.2, 0.2, 0.2), rot=(math.pi / 2, 0, 1.0), top=0.7, segments=10)
    # The adder he cut in two with a spade, on the stones by the bank.
    for k, (x0, y0, x1, y1) in enumerate(((10.4, 9.9, 10.75, 9.75), (10.85, 9.7, 11.3, 9.85))):
        kit.rod(f"Adder half {k}", adder, (x0, y0, height(x0, y0) + 0.03), (x1, y1, height(x1, y1) + 0.03), 0.02, 8)
    kit.splat("Adder blood", mat("blood"), (10.8, 9.75, height(10.8, 9.75)), 0.05, seed=7)
    reb.prim("cube", "Spade blade", mat("rust"), (11.3, 10.3, height(11.3, 10.3) + 0.02), (0.18, 0.25, 0.01), rot=(0, 0, 0.3))
    kit.rod("Spade handle", mat("pine"), (11.35, 10.45, height(11.3, 10.3) + 0.03), (11.7, 11.3, height(11.7, 11.3) + 0.03), 0.018, 6)
    # A shed adder skin on a sunny stone, north bank: there are more.
    kit.rod("Shed skin", reb.mat_plain("Shed skin", (0.4, 0.37, 0.28), 0.6), (6.0, 5.3, height(6.0, 5.3) + 0.02), (6.5, 5.1, height(6.5, 5.1) + 0.02), 0.012, 6)

    # ---- The estate's sign at the ford.
    kit.rod("Sign post", mat("dark wood"), (10.2, 5.8, 0), (10.2, 5.8, 1.6), 0.05)
    reb.wall(reb.prim("cube", "Sign footprint", None, (10.2, 5.8, 0.5), (0.15, 0.15, 1.0))).hide_render = True
    reb.prim("cube", "Estate sign", mat("white paint"), (10.2, 5.78, 1.4), (0.8, 0.04, 0.4))
    kit.text("Sign words", "PRIVATE", mat("black"), (10.2, 5.755, 1.47), size=0.12)
    kit.text("Sign words 2", "SPENCER ESTATE", mat("black"), (10.2, 5.755, 1.33), size=0.075)
    kit.splat("Sign rust", mat("rust"), (10.4, 5.755, 1.3), 0.08, rot=(math.pi / 2, 0, 0), seed=3)

    # ---- Reeds along both banks, the midges over the water.
    rdv, rdf = [], []
    for _ in range(260):
        x = rng.uniform(-4, 24)
        if FORD[0] - 0.4 < x < FORD[1] + 0.4:
            continue
        side = rng.choice((-1, 1))
        y = centre(x) + side * rng.uniform(1.05, 1.6)
        base = Vector((x, y, height(x, y)))
        for _ in range(rng.randint(3, 6)):
            b = base + Vector((rng.gauss(0, 0.07), rng.gauss(0, 0.07), 0))
            h = rng.uniform(0.7, 1.4)
            lean = Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0))
            w = Vector((0.012, 0.012, 0))
            k = len(rdv)
            rdv.extend([tuple(b - w), tuple(b + w), tuple(b + lean + Vector((0, 0, h)))])
            rdf.append((k, k + 1, k + 2))
    reeds = reb.mesh_object("Reeds", rdv, rdf, reb.mat_cards("Reeds", (0.08, 0.08, 0.03), (0.22, 0.2, 0.09)), smooth=False)

    # ---- The forest round it; through the trees to the south, the estate's wall.
    view = clear_view([((c['from'][0] / 1700, c['from'][2] / 1700), (c['to'][0] / 1700, c['to'][2] / 1700)) for c in room.cameras])

    def keep_out(x, y):
        return (X0 - 1.0 < x < X1 + 1.0 and Y0 - 1.0 < y < Y1 + 1.0) or abs(y - centre(x)) < 2.2 or (9.0 < x < 12.2 and y < Y0) or (11.6 < x < 14.0 and y > Y1) or view(x, y)
    kit.forest(rng, height, keep_out, (-10, -9, 29, 26), count=100, ferns=30, needles=500, dead=0.06)
    kit.forest(rng, height, lambda x, y: (-6 < x < 25 and -5 < y < 21) or abs(y - centre(x)) < 3 or (10 < x < 15 and y > 0), (-26, -24, 45, 40), count=60, spacing=3.0, tall=(15, 22), ferns=0, needles=0)
    reb.prim("cube", "Estate wall, far off", stone, (12.0, 34.0, 2.0), (60.0, 0.8, 5.0))
    reb.prim("cube", "Estate wall coping", mat("concrete"), (12.0, 34.0, 4.55), (60.0, 1.0, 0.12))

    def turf(r):
        while True:
            x, y = r.uniform(X0 - 2, X1 + 2), r.uniform(Y0 - 2, Y1 + 2)
            if abs(y - centre(x)) > 1.6 and not (lx0 - 0.2 < x < lx1 + 0.2 and ly0 - 0.2 < y < ly1 + 0.2):
                return x, y
    grass = kit.meadow(rng, 2000, turf, height)

    # ---- Light: the sun gone behind the ridge in the west, the sky red over the water.
    kit.time_light("dusk", sun_heading=272, sun_energy=2.4)
    reb.spot("Last light", (-9.0, 8.0, 8.0), (10.0, 8.0, 0.0), 2600, (1.0, 0.42, 0.22), 45, 0.8, 1.5)
    fill_sun("Sky fill", 0.6, (0.42, 0.48, 0.85), 55, 200)

    anim = kit.Anim(16)
    anim.ripple(mat("water"))
    anim.sway(reeds, amount=0.06, every=3, tip=2)
    anim.sway(grass, amount=0.04)
    anim.flicker(lamp_light, window_glow, depth=0.3, dropouts=1)
    anim.sway(washing[2], amount=0.04, every=2, tip=0)
    anim.flies((5.0, 8.1, WATER_Z + 0.4), count=12, radius=0.9, size=0.01)
    anim.flies((13.2, 8.3, WATER_Z + 0.3), count=10, radius=0.6, size=0.01)

    # ---- What the game needs.
    room.door("valley-path", (9.0, Y0, 12.0, Y0 + 0.6), arrive=(10.4, 3.4), face=(0, 1))
    room.door("lodge", (lx1, LODGE_DOOR[0], lx1 + 0.6, LODGE_DOOR[1]), arrive=(7.5, 12.05), face=(1, 0), walk=False)
    room.door("estate-wall", (11.0, Y1 - 0.6, 13.5, Y1), arrive=(12.2, 12.6), face=(0, -1))
    room.check((lx1, LODGE_DOOR[0] - 0.3, lx1 + 0.8, LODGE_DOOR[1] + 0.3), "The door's padlocked. From the outside.\nThere's light inside. Gouges in the wood, low down.")
    room.check((3.4, ly0 - 0.9, 4.8, ly0 - 0.2), "A lamp's burning in there. There's a smear on the glass.")
    room.check((13.0, 6.0, 15.4, 7.0), "A dog, drowned against the log. A Doberman.\nIts coat's come away in patches. It has a collar tag: SPENCER KENNELS.")
    room.check((6.6, 13.4, 8.2, 14.0), "Washing on the line. One shirt is stiff with blood.")
    room.check((10.2, 9.5, 11.8, 10.6), "An adder, cut in two. A spade beside it.")
    room.check((9.6, 5.3, 10.8, 6.3), "PRIVATE. SPENCER ESTATE.")
    room.check((6.0, 9.3, 7.4, 10.4), "Something was dragged down to the water.\nOne boot, in the reeds.")
    room.export(anim, samples=128)


build()
