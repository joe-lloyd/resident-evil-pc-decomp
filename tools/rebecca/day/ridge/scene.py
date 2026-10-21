"""Rebecca alone at dawn after Billy has left. From the cliff edge she looks
down over forested ridges that fall away in layers into valley mist, to far
blue ranges and pale peaks under the dawn sky. Miles off, on a wooded slope
across the valley, the Spencer mansion: a pale front with a few lit windows.
The rock face closes the back and west of the clearing. The only way down
is the worn path east, between the rock shoulder and the pines.

Moving: grass bends in the wind. Distant hills fade into the dawn haze.
Game units: the clearing floor is X 3900-11000, Z 3000-10000, Y = 0;
the east exit is X 11000-13000, Z 3800-6800. RE1_OUT names the output.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402

# Laid out when a metre was taken as 1000 units, and its world stays that
# way (reb.UNITS = 1000): the cameras, the clearing and the valley keep their
# places. What grows or lies in it is GROW (1700 / 1000) times its real size,
# so it stands right next to her (reb.UNITS has the measured scale), and the
# trees stand back from the clearing to leave the view open.
reb.UNITS = 1000.0
GROW = 1.7
FRAMES = 16
import bpy  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))

CAMERAS = [
    # 0: from the back of the clearing, out over the edge to the valley.
    {"from": (5600, -4300, 2400), "to": (8600, 2600, 20000), "fov": 240, "clip_end": 16000},
    # 1: from the cliff edge, back at the rock face and the trail out (east).
    {"from": (5200, -3200, 11200), "to": (8300, -400, 3500), "fov": 250},
]


def ground_height(x, y):
    """Metres. The clearing is flat; the rock face rises behind (y < 3), the
    slope climbs gently either side, and past the edge (y > 10) the mountain
    falls away to the valley."""
    h = 0.0
    if y < 3.0:
        h += min(2.0, (3.0 - y) * 0.7)
    if x < 3.0:
        h += (3.0 - x) * 0.35
    if x > 11.0 and not (3.8 < y < 6.8):
        h += (x - 11.0) * 0.3
    if y > 10.0:
        # The mountain falls away below the edge, steep at first, to a valley
        # floor some 80 m down.
        d = y - 10.0
        h -= 80.0 * (1.0 - math.exp(-d / 9.0))
    lumps = noise.noise(Vector((x * 0.4, y * 0.4, 0))) * 0.35 + noise.noise(Vector((x * 1.9, y * 1.9, 5))) * 0.06
    # The clearing floor stays nearly flat: the game's floor is Y = 0 everywhere.
    inside = 3.0 <= x <= 11.0 and 3.0 <= y <= 10.0
    return h + lumps * (0.15 if inside else 1.0)


# ---------------------------------------------------------------------------
# The view from the edge (camera 0): forested ridges falling away in layers,
# bluer and paler with distance, mist in the valleys between them, far peaks
# against a dawn sky, and the Spencer mansion small on a far slope.
# ---------------------------------------------------------------------------

EYE = Vector((5.6, 2.4, 4.3))  # camera 0, metres
LOOK = (Vector((8.6, 20.0, -2.6)) - EYE).normalized()
PITCH = math.asin(-LOOK.z)
YAW = math.atan2(LOOK.x, LOOK.y)
FOCAL = 240.0  # pixels: a 24 mm lens on the 32 mm sensor, 320 wide

# Each range: its distance and depth in metres, then where its crest sits
# on camera 0's 320 x 240 picture, as (column, row) points, and how much the
# crest breaks up into peaks (rows). The picture is designed first and the
# heights worked out from it, so every layer lands where it should.
RANGES = [
    ("near west spur", 380, 260, [(-80, 60), (30, 66), (110, 94), (175, 132)], 6, 1),
    ("near east spur", 540, 320, [(150, 132), (230, 100), (300, 78), (400, 70)], 6, 2),
    ("middle ridge", 880, 380, [(-80, 74), (60, 80), (150, 88), (200, 96), (260, 86), (400, 80)], 5, 3),
    ("mansion slope", 1650, 900, [(-80, 50), (90, 45), (170, 41), (215, 38), (300, 46), (400, 44)], 4, 4),
    ("blue range", 3000, 900, [(-80, 38), (70, 33), (190, 37), (290, 32), (400, 35)], 5, 5),
    ("far range", 5200, 1400, [(-80, 30), (110, 27), (240, 30), (400, 26)], 6, 6),
    ("peaks", 8500, 2200, [(-80, 24), (40, 14), (100, 20), (170, 11), (240, 18), (300, 13), (400, 19)], 10, 7),
    ("last range", 12500, 2600, [(-80, 25), (400, 25)], 3, 8),
]
# The mansion: its picture column and row, and its distance.
MANSION = (204, 54, 1300)


def _row_angle(row):
    """Angle below the horizon of picture row `row` at the centre column."""
    return PITCH - math.atan((120 - row) / FOCAL)


def _column(x, y):
    """Picture column of ground point (x, y), near enough for laying out."""
    a = math.atan2(x - EYE.x, y - EYE.y) - YAW
    return 160 + FOCAL * math.tan(max(-1.4, min(1.4, a)))


def _height_at_row(row, dist):
    return EYE.z - dist * math.tan(_row_angle(row))


def _ground_at(column, row, dist):
    """The point at `dist` metres ahead that camera 0 sees at (column, row)."""
    a = YAW + math.atan((column - 160) / FOCAL)
    return Vector((EYE.x + math.sin(a) * dist, EYE.y + math.cos(a) * dist, _height_at_row(row, dist)))


def _crest_row(points, column):
    if column <= points[0][0]:
        return points[0][1]
    for (c0, r0), (c1, r1) in zip(points, points[1:]):
        if column <= c1:
            t = (column - c0) / (c1 - c0)
            t = t * t * (3 - 2 * t)
            return r0 + (r1 - r0) * t
    return points[-1][1]


def _floor(y):
    """The valley floor: deep and misty, a little deeper with distance."""
    return -85.0 - 175.0 * (1.0 - math.exp(-(y - 40.0) / 140.0)) - 0.004 * y


def _ridged(x, y, seed):
    """Sharp-crested ridge noise, 0 to 1."""
    n = 1.0 - abs(noise.noise(Vector((x, y, seed))))
    return n * n


MANSION_AT = _ground_at(*MANSION)


def backdrop_height(x, y):
    """The land beyond the edge: the union of the ranges over the valley floor."""
    floor = _floor(y)
    z = floor
    for name, dist, depth, points, rough, seed in RANGES:
        wobble = 0.16 * depth * math.sin(x / (0.9 * depth) + seed * 1.7) + 0.07 * depth * noise.noise(Vector((x / depth * 2.3, seed, 0.5)))
        t = (y - dist - wobble) / depth
        if abs(t) >= 1.0:
            continue
        column = _column(x, dist)
        crest = _height_at_row(_crest_row(points, column), dist)
        # Peaks and saddles along the crest, as rows of the picture.
        crest -= dist * math.tan(math.radians(rough * 0.22)) * (noise.noise(Vector((column * 0.045, seed, 3.1))) + 0.5 * noise.noise(Vector((column * 0.13, seed, 7.7))))
        relief = crest - floor
        if relief <= 0:
            continue
        # The mansion's slope is full-bellied, so its terrace lies on the face.
        profile = (1.0 - abs(t)) ** ((0.8 if name == "mansion slope" else 1.35) if t < 0 else 1.1)
        # Spurs and gullies running down the faces.
        gullies = (0.16 if dist < 4000 else 0.3) * relief * profile * (_ridged(x / (0.22 * depth), y / (0.5 * depth), seed) - 0.45)
        z = max(z, floor + relief * profile + gullies)
    # A terrace for the mansion, cut into the face of its slope.
    d = math.hypot(x - MANSION_AT.x, y - MANSION_AT.y)
    if d < 150:
        k = max(0.0, min(1.0, (150 - d) / 70))
        k = k * k * (3 - 2 * k)
        z += (MANSION_AT.z - 1.0 - z) * k
    return z + 4.0 * noise.noise(Vector((x * 0.02, y * 0.02, 11)))


def _mix_rgb(nodes, links, fac, a, b):
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    sock = {s.identifier: s for s in mix.inputs}
    for name, value in (("Factor_Float", fac), ("A_Color", a), ("B_Color", b)):
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, sock[name])
        else:
            sock[name].default_value = value if name == "Factor_Float" else (*value, 1)
    return next(s for s in mix.outputs if s.identifier == "Result_Color")


def _math(nodes, links, op, a, b=None, clamp=False):
    n = nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, bpy.types.NodeSocket):
            links.new(v, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n.outputs[0]


def _smooth(nodes, links, value, lo, hi):
    """0 at `lo`, 1 at `hi`, smoothly, clamped."""
    n = nodes.new("ShaderNodeMapRange")
    n.interpolation_type = "SMOOTHSTEP"
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = lo, hi
    links.new(value, n.inputs["Value"])
    return n.outputs["Result"]


HAZE_NEAR = (0.2, 0.25, 0.37)   # blue air over the near ranges
HAZE_FAR = (0.62, 0.48, 0.47)   # the far air takes the dawn's colour
MIST = (0.62, 0.6, 0.66)        # valley mist


def hazed(m, scale=2800.0, most=0.82):
    """Air between camera 0 and the land: what is far fades into a blue,
    then dawn-coloured haze, and low ground lies in mist. Camera rays only,
    so the haze does not light the clearing."""
    m["worn"] = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    out = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    surface = out.inputs["Surface"].links[0].from_socket
    dist = nodes.new("ShaderNodeCameraData").outputs["View Distance"]
    pos = nodes.new("ShaderNodeNewGeometry").outputs["Position"]
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos, sep.inputs[0])
    air = _math(nodes, links, "MULTIPLY", _math(nodes, links, "SUBTRACT", 1.0, _math(nodes, links, "EXPONENT", _math(nodes, links, "DIVIDE", dist, -scale))), most)
    colour = _mix_rgb(nodes, links, _smooth(nodes, links, dist, 1500, 10000), HAZE_NEAR, HAZE_FAR)
    # The mist's top rises and falls, so it lies in banks, not as a lake.
    banks = nodes.new("ShaderNodeTexNoise")
    banks.inputs["Scale"].default_value = 0.0035
    banks.inputs["Detail"].default_value = 3
    links.new(pos, banks.inputs["Vector"])
    top = _math(nodes, links, "ADD", sep.outputs["Z"], _math(nodes, links, "MULTIPLY", _math(nodes, links, "SUBTRACT", banks.outputs["Fac"], 0.5), -150.0))
    low = _math(nodes, links, "SUBTRACT", 1.0, _smooth(nodes, links, top, -245, -160))
    mist = _math(nodes, links, "MULTIPLY", low, _math(nodes, links, "MULTIPLY", _smooth(nodes, links, dist, 150, 900), 0.75))
    colour = _mix_rgb(nodes, links, mist, colour, MIST)
    total = _math(nodes, links, "SUBTRACT", 1.0, _math(nodes, links, "MULTIPLY", _math(nodes, links, "SUBTRACT", 1.0, air), _math(nodes, links, "SUBTRACT", 1.0, mist)))
    gate = _math(nodes, links, "MULTIPLY", total, nodes.new("ShaderNodeLightPath").outputs["Is Camera Ray"])
    glow = nodes.new("ShaderNodeEmission")
    links.new(colour, glow.inputs["Color"])
    both = nodes.new("ShaderNodeMixShader")
    links.new(gate, both.inputs["Fac"])
    links.new(surface, both.inputs[1])
    links.new(glow.outputs[0], both.inputs[2])
    links.new(both.outputs[0], out.inputs["Surface"])
    return m


def _tree_colours(name, dark, light):
    """Each tier of each pine a shade of its own, no cut-outs: at this
    distance a crown is a pixel or two, and holes would only be noise."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.95
    geo = nodes.new("ShaderNodeNewGeometry")
    col = reb.ramp(nodes, links, geo.outputs["Random Per Island"], [(0.0, dark), (1.0, light)])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def _land_material():
    """The ground under the canopy, going to bare rock up on the peaks."""
    m, nodes, links, bsdf = reb.nodes_material("Backdrop land")
    bsdf.inputs["Roughness"].default_value = 1.0
    pos = nodes.new("ShaderNodeNewGeometry").outputs["Position"]
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos, sep.inputs[0])
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 0.004
    tex.inputs["Detail"].default_value = 8
    links.new(pos, tex.inputs["Vector"])
    forest = reb.ramp(nodes, links, tex.outputs["Fac"], [(0.35, (0.012, 0.026, 0.016)), (0.65, (0.045, 0.07, 0.035))])
    rock = reb.ramp(nodes, links, tex.outputs["Fac"], [(0.3, (0.09, 0.085, 0.085)), (0.7, (0.2, 0.18, 0.17))])
    up = _smooth(nodes, links, sep.outputs["Z"], 60, 380)
    links.new(_mix_rgb(nodes, links, up, forest.outputs["Color"], rock.outputs["Color"]), bsdf.inputs["Base Color"])
    return hazed(m)


def mansion(rng):
    """The Spencer mansion as the opening film shows it (pu.avi, about
    170 s; the endings' aerial shots): a central block under a broad
    pediment, an entrance portico with its own pediment, long wings either
    side ending in taller pavilions, rear wings round a court, and tall
    chimneys. Pale stone, a dark slate roof, a few windows lit. Built at
    its real size and stood on the terrace, facing back up the valley."""
    walls, roofs, lit = ([], []), ([], []), ([], [])

    def block(cx, cy, w, d, h):
        reb.box(*walls, (cx, cy, h / 2 - 2), (w, d, h + 4))

    def gable(cx, cy, w, d, eave, peak, along_y):
        """A pitched roof; its gable ends are stone, so a pediment reads pale."""
        v, f = roofs
        k = len(v)
        if along_y:
            pts = ((cx - w / 2, cy - d / 2, eave), (cx + w / 2, cy - d / 2, eave), (cx + w / 2, cy + d / 2, eave), (cx - w / 2, cy + d / 2, eave), (cx, cy - d / 2, peak), (cx, cy + d / 2, peak))
            quads = ((0, 1, 4), (2, 3, 5), (0, 4, 5, 3), (1, 2, 5, 4))
        else:
            pts = ((cx - w / 2, cy - d / 2, eave), (cx + w / 2, cy - d / 2, eave), (cx + w / 2, cy + d / 2, eave), (cx - w / 2, cy + d / 2, eave), (cx - w / 2 + d / 2, cy, peak), (cx + w / 2 - d / 2, cy, peak))
            quads = ((0, 3, 4), (1, 5, 2), (0, 4, 5, 1), (3, 2, 5, 4))
        v.extend(pts)
        f.extend(tuple(k + i for i in q) for q in quads[2:])
        sv, sf = walls
        k = len(sv)
        sv.extend(pts)
        sf.extend(tuple(k + i for i in q) for q in quads[:2])

    # Centre block, its pediment facing the valley, and the portico.
    block(0, 0, 30, 26, 22)
    gable(0, 0, 31, 27, 22, 33, True)
    block(0, -16, 12, 6, 12)
    gable(0, -16.5, 13, 7, 12, 16.5, True)
    for side in (-1, 1):
        block(side * 32.5, 2, 35, 18, 17)
        gable(side * 32.5, 2, 36, 19, 17, 23, False)
        block(side * 56, 0, 12, 24, 20)
        gable(side * 56, 0, 13, 25, 20, 29, True)
        block(side * 44, 27, 12, 34, 17)
        gable(side * 44, 27, 13, 35, 17, 23, True)
        for x, y, top in ((side * 20, 7, 28), (side * 44, 8, 27), (side * 56, 9, 33), (side * 9, 9, 36)):
            reb.box(*walls, (x, y, top - 4), (2.2, 2.2, 9))
    # A few windows lit on the front: someone is in there.
    fronts = [(-13, 13, -13.05, (5.0, 12.0)), (-50, -15, -7.05, (4.5, 10.5)), (15, 50, -7.05, (4.5, 10.5)), (-62, -50, -12.05, (5.0, 12.5)), (50, 62, -12.05, (5.0, 12.5))]
    spots = [(x0 + (x1 - x0) * (i + 0.5) / max(1, round((x1 - x0) / 5)), y, z) for x0, x1, y, zs in fronts for i in range(max(1, round((x1 - x0) / 5))) for z in zs]
    for x, y, z in rng.sample(spots, 9):
        reb.box(*lit, (x, y, z), (2.6, 0.2, 3.4))
    stone = hazed(reb.mat_surface("Mansion stone", [(0.3, (0.5, 0.45, 0.38)), (0.7, (0.66, 0.6, 0.5))], scale=0.6, bump=0.0), most=0.55)
    slate = hazed(reb.mat_plain("Mansion slate", (0.05, 0.05, 0.06), 0.6), most=0.55)
    glow = hazed(reb.mat_emit("Mansion lit windows", (1.0, 0.58, 0.24), 14.0), most=0.5)
    turn = math.radians(12.0)
    for name, (v, f), m in (("Spencer mansion", walls, stone), ("Spencer mansion roofs", roofs, slate), ("Spencer mansion windows", lit, glow)):
        ob = reb.mesh_object(name, v, f, m, smooth=False)
        ob.location = MANSION_AT - Vector((0, 0, 1.0))
        ob.rotation_euler[2] = turn


def backdrop(rng):
    """Everything past the edge, for camera 0. Camera 1 looks the other way."""
    # The land: rows spread out with distance, each row as wide as the view.
    rows, cols = 300, 340
    v, f = [], []
    for j in range(rows + 1):
        y = 40.0 * (15500.0 / 40.0) ** (j / rows)
        centre, half = EYE.x + math.tan(YAW) * y, 1.05 * y + 160
        for i in range(cols + 1):
            x = centre - half + 2 * half * i / cols
            v.append((x, y, backdrop_height(x, y)))
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            f.append((a, a + 1, a + cols + 2, a + cols + 1))
    land = reb.mesh_object("Backdrop land", v, f, _land_material())
    land.visible_shadow = True

    # Pines over every slope out to the mansion's ridge, thinning to the
    # canopy's texture beyond. Three tiers to a tree, as the near pines.
    layers = [([], []) for _ in range(3)]
    placed = 0
    while placed < 90000:
        y = math.sqrt(rng.uniform(42.0 ** 2, 2100.0 ** 2))
        centre, half = EYE.x + math.tan(YAW) * y, 0.8 * y + 30
        x = rng.uniform(centre - half, centre + half)
        # The mansion's lawn, opening toward the camera so its front shows.
        to = Vector((x - MANSION_AT.x, y - MANSION_AT.y))
        if to.length < 95 or (to.length < 170 and to.y < 0 and abs(to.x) < 0.4 * -to.y + 60):
            continue
        z = backdrop_height(x, y) - 0.5
        h = rng.uniform(13, 24)
        tv, tf = layers[0 if y < 500 else 1 if y < 1100 else 2]
        lean = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3))
        for tier in range(3):
            k = len(tv)
            tv.append((x + lean[0], y + lean[1], z + h * (0.62 + tier * 0.19)))
            for s in range(6):
                a = math.tau * s / 6 + tier
                radius = h * (0.2 - tier * 0.045)
                tv.append((x + math.cos(a) * radius, y + math.sin(a) * radius, z + h * (0.08 + tier * 0.24)))
            tf.extend((k, k + 1 + s, k + 1 + (s + 1) % 6) for s in range(6))
        placed += 1
    shades = (((0.008, 0.02, 0.012), (0.04, 0.07, 0.035)),
              ((0.01, 0.024, 0.016), (0.045, 0.075, 0.04)),
              ((0.012, 0.026, 0.018), (0.05, 0.08, 0.045)))
    for i, (tv, tf) in enumerate(layers):
        reb.mesh_object(f"Backdrop pines {i}", tv, tf, hazed(_tree_colours(f"Backdrop pine {i}", *shades[i])), smooth=False)
    mansion(rng)


def camera_sky():
    """What camera 0 sees of the sky, low over the ranges at dawn: gold at
    the horizon going up to dusty rose and blue, brighter toward the sun
    (east, right of the picture), and a band of thin cloud lit from below.
    The world's own light on the clearing stays as kit.time_light set it."""
    world = bpy.context.scene.world
    nodes, links = world.node_tree.nodes, world.node_tree.links
    out = next(n for n in nodes if n.type == "OUTPUT_WORLD")
    light = out.inputs["Surface"].links[0].from_socket
    tc = nodes.new("ShaderNodeTexCoord").outputs["Generated"]
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc, sep.inputs[0])
    up = sep.outputs["Z"]
    sky = reb.ramp(nodes, links, _math(nodes, links, "DIVIDE", up, 0.14, clamp=True), [(0.0, (1.0, 0.7, 0.42)), (0.18, (0.95, 0.6, 0.48)), (0.5, (0.62, 0.5, 0.6)), (1.0, (0.33, 0.37, 0.56))]).outputs["Color"]
    sun = bpy.data.objects["Sun"].matrix_world.to_quaternion() @ Vector((0, 0, 1))
    toward = nodes.new("ShaderNodeVectorMath")
    toward.operation = "DOT_PRODUCT"
    links.new(tc, toward.inputs[0])
    toward.inputs[1].default_value = tuple(sun)
    warm = _math(nodes, links, "POWER", _math(nodes, links, "MAXIMUM", toward.outputs["Value"], 0.0), 3.0)
    sky = _mix_rgb(nodes, links, _math(nodes, links, "MULTIPLY", warm, 0.45), sky, (1.0, 0.78, 0.5))
    # Clouds on a flat layer overhead, so they close into streaks low down.
    flat = nodes.new("ShaderNodeVectorMath")
    flat.operation = "DIVIDE"
    links.new(tc, flat.inputs[0])
    lift = nodes.new("ShaderNodeCombineXYZ")
    for k in "XYZ":
        links.new(_math(nodes, links, "ADD", up, 0.035), lift.inputs[k])
    links.new(lift.outputs[0], flat.inputs[1])
    stretch = nodes.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (0.18, 0.55, 0.0)
    links.new(flat.outputs[0], stretch.inputs["Vector"])
    cloud = nodes.new("ShaderNodeTexNoise")
    cloud.inputs["Scale"].default_value = 2.2
    cloud.inputs["Detail"].default_value = 7
    cloud.inputs["Roughness"].default_value = 0.62
    links.new(stretch.outputs[0], cloud.inputs["Vector"])
    cover = _math(nodes, links, "MULTIPLY", _smooth(nodes, links, cloud.outputs["Fac"], 0.44, 0.58), _smooth(nodes, links, up, 0.004, 0.035))
    lit = _math(nodes, links, "SUBTRACT", 1.0, _smooth(nodes, links, cloud.outputs["Fac"], 0.5, 0.66))
    tint = _mix_rgb(nodes, links, _math(nodes, links, "ADD", _math(nodes, links, "MULTIPLY", lit, 0.6), _math(nodes, links, "MULTIPLY", warm, 0.6), clamp=True), (0.36, 0.28, 0.36), (1.0, 0.64, 0.4))
    sky = _mix_rgb(nodes, links, cover, sky, tint)
    bg = nodes.new("ShaderNodeBackground")
    links.new(sky, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    pick = nodes.new("ShaderNodeMixShader")
    links.new(nodes.new("ShaderNodeLightPath").outputs["Is Camera Ray"], pick.inputs["Fac"])
    links.new(light, pick.inputs[1])
    links.new(bg.outputs[0], pick.inputs[2])
    links.new(pick.outputs[0], out.inputs["Surface"])


def build():
    rng = random.Random(31)
    reb.clear_scene()
    earth = reb.mat_surface("Earth", [(0.0, (0.03, 0.025, 0.02)), (0.4, (0.09, 0.07, 0.05)), (0.7, (0.06, 0.07, 0.04)), (1.0, (0.13, 0.11, 0.09))], scale=3)
    rock = reb.mat_surface("Rock", [(0.25, (0.04, 0.04, 0.04)), (0.5, (0.12, 0.115, 0.11)), (0.7, (0.2, 0.19, 0.18)), (0.9, (0.07, 0.08, 0.05))], scale=1.8, detail=14, bump=1.2)
    needles = reb.mat_cards("Needles", (0.012, 0.03, 0.018), (0.06, 0.12, 0.06))
    grass = reb.mat_cards("Grass", (0.04, 0.05, 0.02), (0.14, 0.15, 0.07))
    bark = reb.mat_wood("Bark", (0.07, 0.05, 0.035))

    reb.terrain("Mountain top", earth, (-30, 45), (-25, 60), ground_height, step=0.45)

    # The rock face behind the clearing: a cliff, its face displaced into
    # ledges and cracks, with fallen boulders at its foot.
    verts, faces = [], []
    nx, nz = 90, 40
    for j in range(nz + 1):
        z = -1.0 + 16.0 * j / nz
        for i in range(nx + 1):
            x = -6.0 + 26.0 * i / nx
            ledge = noise.noise(Vector((x * 0.25, 0, z * 0.6))) * 1.4 + noise.noise(Vector((x * 1.3, 3, z * 1.3))) * 0.35
            y = 1.6 - 0.12 * z + ledge - max(0.0, (z - 9.0)) * 0.5
            verts.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    reb.wall(reb.mesh_object("Rock face", verts, faces, rock))
    verts, faces = [], []
    for i in range(14):
        x = rng.uniform(-1, 15)
        y = rng.uniform(2.2, 3.0)
        reb.boulder(rng, (x, y, ground_height(x, y) + 0.2), rng.uniform(0.35, 0.9) * GROW, verts, faces)
    reb.mesh_object("Fallen rocks", verts, faces, rock)
    # Boulders in the clearing, two near camera 1 that she can walk behind.
    for name, (x, y, r, in_front) in {
        "Boulder west": (4.0, 8.2, 0.7, True),
        "Boulder east": (9.6, 8.6, 0.6, True),
        "Boulder north": (8.6, 4.2, 0.55, False),
    }.items():
        verts, faces = [], []
        reb.boulder(rng, (x, y, ground_height(x, y) + r * 0.3 * GROW), r * GROW, verts, faces)
        ob = reb.wall(reb.mesh_object(name, verts, faces, rock), "circle")
        if in_front:
            reb.mask(ob)

    # Close the false west path with rock, rooted below the clearing.
    # Each piece exports its own footprint, rather than one box over the path.
    for i, y in enumerate((3.0, 5.0, 7.0)):
        v, f = [], []
        reb.boulder(rng, (1.6, y, 1.0), 2.0, v, f)
        reb.wall(reb.mesh_object(f"West rock shoulder {i}", v, f, rock))

    v, f = [], []
    reb.boulder(rng, (4.0, 2.5, 1.2), 1.7, v, f)
    reb.wall(reb.mesh_object("West path rockfall", v, f, rock))

    # A worn strip leads to the single east exit, at floor height throughout.
    path_m = reb.mat_surface("Worn trail", [(0.0, (0.08, 0.065, 0.045)), (1.0, (0.2, 0.16, 0.1))], scale=5)
    v, f = [], []
    for i in range(16):
        x = 8.8 + i * 0.65
        lo, hi = 4.5 + 0.12 * math.sin(i), 6.2 + 0.12 * math.sin(i)
        k = len(v)
        v += [(x, lo, 0.035), (x + 0.65, lo, 0.035), (x + 0.65, hi, 0.035), (x, hi, 0.035)]
        f.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Trail east", v, f, path_m)

    # Pines around the clearing: the west edge, the east edge either side of
    # the trail out, and the forest down the valley.
    needle_v, needle_f, bases = [], [], []
    ring = []
    for _ in range(30):
        x, y = rng.uniform(18, 27), rng.uniform(8.5, 19)
        if y < 10 and x < 21:
            continue  # the trail out
        ring.append((x, y))
    for x, y in ring:
        h = rng.uniform(8, 14) * GROW
        base = Vector((x, y, ground_height(x, y) - 0.2))
        reb.conifer(rng, base, h, needle_v, needle_f)
        bases.append((base, h))
    reb.mesh_object("Pines", needle_v, needle_f, needles, smooth=False)
    # The pines' footprint is the clearing's edge (room.json "bounds"), not their own.
    reb.trunks("Pine trunks", bark, bases)

    backdrop(random.Random(57))

    # Grass about the clearing.
    gv, gf = [], []
    def patchy(r):
        while True:
            x, y = r.uniform(2.5, 11.5), r.uniform(2.6, 10.3)
            if not (x > 9 and 4.3 < y < 6.4) and noise.noise(Vector((x * 0.35, y * 0.35, 9))) > -0.1:
                return x, y
    reb.grass_tufts(rng, 1800, patchy, ground_height, gv, gf)
    # Tufts made for a 1000-unit metre: stretch them up to her scale.
    for i in range(2, len(gv), 3):
        b = (Vector(gv[i - 2]) + Vector(gv[i - 1])) / 2
        gv[i] = tuple(b + (Vector(gv[i]) - b) * GROW)
    # Stones scattered over the bare patches.
    sv, sf = [], []
    for _ in range(60):
        x, y = rng.uniform(3.0, 11.0), rng.uniform(3.2, 10.0)
        r = rng.uniform(0.05, 0.16) * GROW
        reb.boulder(rng, (x, y, ground_height(x, y)), r, sv, sf, squash=0.6)
    reb.mesh_object("Stones", sv, sf, rock)
    grass_ob = reb.mesh_object("Grass", gv, gf, grass, smooth=False)
    grass_rest = [Vector(p) for p in gv]
    kit.time_light("dawn")
    camera_sky()
    # A soft key on the clearing, from the cameras' side, for the RE look.
    reb.spot("Key", (7.0, 3.5, 9.0), (7.0, 8.0, 0.0), 2500, (1.0, 0.8, 0.65), 110, 1.0, 2.0)
    reb.spot("Back key", (6.0, 11.0, 8.0), (8.0, 4.0, 0.0), 1800, (0.8, 0.85, 1.0), 110, 1.0, 2.0)

    def pose(k):
        t = k / FRAMES
        phase = 2 * math.pi * t
        for idx in range(2, len(grass_rest), 3):
            p = grass_rest[idx]
            w = math.sin(phase + p.x * 0.7 + p.y * 0.4)
            grass_ob.data.vertices[idx].co = (p.x + 0.08 * w, p.y + 0.03 * w, p.z)
        grass_ob.data.update()

    # The kit's worn, bitty surfaces, as every kit room has.

    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))

    reb.export(
        CAMERAS,
        OUT,
        anim={"frames": FRAMES, "ticks": 3, "set": pose},
        extra={
            # Clearing bounds close the cliff and west shoulder. Only the
            # east trail opens them; tagged rock supplies its own collision.
            "bounds": {"x0": 3900, "z0": 3000, "x1": 11000, "z1": 10000},
            # Underfoot (sound/ground.ts): the clearing's earth.
            "ground": "earth",
            "floors": [],
            "exit": {"x0": 11000, "z0": 3800, "x1": 13000, "z1": 6800},
        },
    )


build()
