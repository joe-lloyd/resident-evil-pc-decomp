"""The summit trail, afternoon: bare granite above the trees, under blowing cloud.

What it tells: the mine lift comes up into a timber head house at the south
end of the ridge, and from there a trail of cairns runs north along the
bare rock to the weather station and on to the radio mast. The observer who
lives up here went out this morning to read his instruments and the crows
came down on him. The louvred instrument screen stands open with its
thermometer smashed, his clipboard dropped on the rock, his cap and broken
glasses beside it. His blood drips away north along the ridge toward the
mast, where the engineers keep their first aid. A deer lies opened on the
rock by the trail and the crows are still at it. They watch her from the
cairns. Nothing lives up here but them now.

Metres: the floor is x 1-19, y 1-15, all bare rock. The ridge runs north
and south and falls away steeply east and west. The weather station hut is
x 1.6-5.6, y 2.4-5.6, its door in the south wall at x 3.2-4.1. The mine
lift's head house is x 13.5-17.5, y 11.0-14.6, its door in the north wall
at x 14.9-15.9, a headframe and sheave above it. The trail leaves north off
the floor's edge at x 8-12 toward the mast, which stands far off along the
ridge.

Moving: cloud wisps drifting over the ridge, the anemometer's cups
spinning, a crow pecking at the deer and another circling overhead, the
clipboard's sheet lifting in the wind, the mast's far red light blinking,
dead grass in the wind.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

X0, Y0, X1, Y1 = 1.0, 1.0, 19.0, 15.0
HUT = (1.6, 5.6, 2.4, 5.6)
HUT_DOOR = (3.2, 4.1)
HEAD = (13.5, 17.5, 11.0, 14.6)
HEAD_DOOR = (14.9, 15.9)
MAST_AT = (10.0, -46.0)


def height(x, y):
    """The summit flat where she walks; the ridge running on north to the
    mast; steep falls east, west and south."""
    n = noise.noise(Vector((x * 0.15, y * 0.15, 3.0)))
    if X0 - 0.4 < x < X1 + 0.4 and Y0 - 0.4 < y < Y1 + 0.4:
        return 0.03 * n - 0.03
    out = max(X0 - 0.4 - x, x - X1 - 0.4, Y0 - 0.4 - y, y - Y1 - 0.4, 0.0)
    h = 0.5 * n * min(1.0, out / 3.0)
    dx = max(X0 - 0.4 - x, x - X1 - 0.4, 0.0)
    if y < Y0:
        # The ridge narrows north toward the mast, its crest about x 10.
        half = max(4.0, 9.0 - (Y0 - y) * 0.12)
        dx = max(abs(x - 10.0) - half, 0.0)
        h += 0.02 * min(Y0 - y, 50.0)
    dy = max(y - Y1 - 0.4, 0.0)
    fall = dx * 0.9 + dx * dx * 0.04 + dy * 0.7 + dy * dy * 0.03
    return h - fall


def struts(name, m, segs, r, sides=4):
    """Many square bars, one mesh: a lattice, a frame, rails."""
    verts, faces = [], []
    for a, b in segs:
        a, b = Vector(a), Vector(b)
        d = b - a
        if d.length < 1e-4:
            continue
        q = d.to_track_quat("Z", "Y")
        k = len(verts)
        for end in (a, b):
            for s in range(sides):
                t = 2 * math.pi * s / sides + math.pi / sides
                verts.append(tuple(end + q @ Vector((math.cos(t) * r, math.sin(t) * r, 0))))
        for s in range(sides):
            faces.append((k + s, k + (s + 1) % sides, k + sides + (s + 1) % sides, k + sides + s))
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def mist_mat(name, rgb, density, scale, lo=0.4, hi=0.72):
    """Cloud on a card: noise thinned to nothing at the card's edges."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    out = nodes["Material Output"]
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, scale, 5, 0.6)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(lo, (0, 0, 0)), (hi, (density,) * 3)])
    tc = nodes.new("ShaderNodeTexCoord")
    sub = nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    links.new(tc.outputs["Generated"], sub.inputs[0])
    mul = nodes.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = (2, 2, 0)
    links.new(sub.outputs[0], mul.inputs[0])
    ln = nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    links.new(mul.outputs[0], ln.inputs[0])
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 1.0
    edge.inputs["From Max"].default_value = 0.4
    links.new(ln.outputs["Value"], edge.inputs["Value"])
    prod = nodes.new("ShaderNodeMath")
    prod.operation = "MULTIPLY"
    links.new(r.outputs["Color"], prod.inputs[0])
    links.new(edge.outputs["Result"], prod.inputs[1])
    links.new(prod.outputs[0], mix.inputs["Fac"])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def cairn(rng, at, high, rv, rf):
    """Flat stones stacked to mark the trail. Returns the top's height."""
    x, y = at
    z = height(x, y) - 0.05
    for i in range(high):
        r = 0.34 - i * 0.04
        reb.boulder(rng, (x + rng.uniform(-0.04, 0.04), y + rng.uniform(-0.04, 0.04), z + r * 0.4), r, rv, rf, squash=0.45)
        z += r * 0.8
    return z


def deer(name, at, heading):
    """A dead deer on its side, its belly opened."""
    hide = reb.mat_surface("Deer hide", [(0.0, (0.16, 0.09, 0.05)), (0.7, (0.26, 0.15, 0.08)), (1.0, (0.35, 0.28, 0.2))], scale=6, bump=0.3)
    parts = [
        reb.prim("sphere", "torso", hide, (0, 0, 0.26), (1.2, 0.45, 0.5), segments=18),
        reb.prim("sphere", "neck", hide, (0.68, 0.0, 0.3), (0.5, 0.18, 0.2), rot=(0, -0.3, 0.3), segments=12),
        reb.prim("sphere", "head", hide, (0.98, 0.15, 0.16), (0.36, 0.16, 0.18), rot=(0, 0.2, 0.6), segments=12),
        reb.prim("sphere", "ear", hide, (0.95, 0.27, 0.27), (0.14, 0.04, 0.08), segments=8),
        reb.prim("sphere", "wound", mat("blood"), (0.05, -0.2, 0.22), (0.7, 0.12, 0.3), segments=14),
    ]
    for i in range(5):
        parts.append(reb.prim("cyl", "rib", mat("bone"), (-0.2 + i * 0.1, -0.22, 0.27), (0.02, 0.02, 0.3), rot=(0.2, 0, 0), segments=6))
    for lx, ly, ex, ey in ((0.4, -0.05, 0.85, -0.55), (0.35, 0.05, 0.75, -0.62), (-0.42, -0.05, -0.75, -0.6), (-0.45, 0.05, -0.95, -0.5)):
        parts.append(kit.rod("leg", hide, (lx, ly, 0.2), (ex, ey, 0.06), 0.045, 8))
        parts.append(reb.prim("cube", "hoof", mat("black"), (ex, ey, 0.05), (0.06, 0.05, 0.08)))
    ob = kit.join(name, parts)
    ob.location = (at[0], at[1], height(*at))
    ob.rotation_euler = (0, 0, heading)
    return ob


def build():
    rng = random.Random(2104)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((10.4, 15.9, 3.6), (8.6, 5.0, 0.0), 200, "from the south by the head house: the ridge north, the deer and its crows, the hut, the trail to the mast")
    room.camera((18.7, 1.0, 3.5), (9.0, 11.5, 0.2), 200, "from the north-east: the head house and its headframe, the cairns, the deer")
    room.camera((1.0, 14.8, 3.3), (12.0, 4.0, 0.4), 195, "from the south-west: the instrument screen, the blood north, the mast far off")
    room.camera((12.0, 0.7, 3.6), (7.0, 11.0, 0.0), 200, "from the trail's north end: the hut's door, the screen, the head house far end")

    rock = kit.dirtied(reb.mat_surface("Summit granite", [(0.0, (0.07, 0.07, 0.065)), (0.45, (0.17, 0.165, 0.15)), (0.7, (0.22, 0.2, 0.18)), (1.0, (0.13, 0.12, 0.11))], scale=1.2, bump=0.8), 0.6, scale=0.35)
    lichen = reb.mat_surface("Lichen", [(0.0, (0.1, 0.11, 0.07)), (1.0, (0.17, 0.18, 0.1))], scale=20, bump=0.2)
    boards = kit.boards("Head house boards", (0.2, 0.14, 0.09), width=0.2, grime=0.8)
    hut_boards = kit.boards("Hut boards", (0.28, 0.27, 0.22), width=0.14, grime=0.6)
    timber = mat("dark wood")
    louvre = reb.mat_plain("Screen white", (0.5, 0.5, 0.46), 0.7)

    # ---- The ground: granite, scree, lichen, a few tufts of dead grass in the cracks.
    reb.terrain("Summit rock", rock, (-70, 90), (-80, 70), height, step=0.8)
    kit.cracks("Rock seams", mat("black"), (X0, Y0, X1, Y1), count=26, seed=3, length=2.4)
    for i in range(10):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        kit.splat(f"Lichen {i}", lichen, (x, y, height(x, y)), rng.uniform(0.25, 0.6), seed=100 + i, stretch=(1.4, 0.8), lumps=0.6)
    kit.path_strip("Trail", reb.mat_plain("Worn rock", (0.24, 0.23, 0.21), 0.9), [(15.4, 10.6), (13.0, 9.0), (10.6, 6.0), (10.0, 2.0), (10.0, -14.0), (10.0, -40.0)], height, width=0.55, lift=0.004)
    kit.path_strip("Trail to the hut", reb.mat_plain("Worn rock", (0.24, 0.23, 0.21), 0.9), [(10.4, 6.6), (6.8, 7.0), (3.65, 6.2)], height, width=0.45, lift=0.004)
    rv, rf = [], []
    for _ in range(140):
        x, y = rng.uniform(-40, 60), rng.uniform(-50, 50)
        if X0 - 0.5 < x < X1 + 0.5 and Y0 - 0.5 < y < Y1 + 0.5:
            continue
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.3, 1.6), rv, rf)
    for _ in range(90):
        x, y = rng.uniform(X0 - 3, X1 + 3), rng.uniform(Y0 - 3, Y1 + 3)
        if X0 + 0.3 < x < X1 - 0.3 and Y0 + 0.3 < y < Y1 - 0.3 and rng.random() < 0.85:
            continue
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.1, 0.35), rv, rf)
    # Outcrops on the floor, which she walks round.
    for (x, y, r) in ((6.5, 12.5, 0.9), (12.2, 3.6, 0.7), (17.6, 6.0, 0.8), (2.4, 9.8, 0.6)):
        brv, brf = [], []
        reb.boulder(rng, (x, y, height(x, y) - 0.1), r, brv, brf, squash=0.7)
        reb.wall(reb.mesh_object("Outcrop", brv, brf, rock), "circle")
    tops = []
    for i, (x, y, n) in enumerate(((7.6, 8.4, 5), (11.3, 5.0, 4), (12.6, 9.6, 5), (10.6, 2.1, 6))):
        cv, cf = [], []
        tops.append(cairn(rng, (x, y), n, cv, cf))
        reb.wall(reb.mesh_object(f"Cairn {i}", cv, cf, mat("rock")), "circle")
    scree = []
    for _ in range(400):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        scree.append((x, y))
    sv, sf = [], []
    for x, y in scree:
        reb.box(sv, sf, (x, y, height(x, y) + 0.02), (rng.uniform(0.04, 0.12), rng.uniform(0.04, 0.1), 0.05), rng.uniform(0, 3))
    reb.mesh_object("Scree", sv, sf, mat("gravel"), smooth=False)
    reb.mesh_object("Boulders", rv, rf, mat("rock"))
    grass = kit.meadow(rng, 500, lambda r: (r.uniform(X0 - 6, X1 + 6), r.uniform(Y0 - 6, Y1 + 4)), height, mat("dead grass"))

    # ---- The weather station hut: grey boards, a tin roof, the door south, windows north and east.
    hx0, hx1, hy0, hy1 = HUT
    for ob in kit.walls(hx0 + 0.1, hy0 + 0.1, hx1 - 0.1, hy1 - 0.1, 2.5, hut_boards, openings=[
        ("s", HUT_DOOR[0], HUT_DOOR[1], 0.0, 2.0),
        ("e", 3.3, 4.6, 1.0, 1.8),
        ("n", 2.4, 3.6, 1.05, 1.75),
    ], name="Hut wall"):
        reb.wall(ob)
    reb.prim("cube", "Hut roof", mat("tin"), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 2.62), (hx1 - hx0 + 0.5, hy1 - hy0 + 0.5, 0.08), rot=(-0.1, 0, 0))
    reb.wall(reb.prim("cube", "Hut inside", reb.mat_plain("Hut dark", (0.03, 0.028, 0.025), 0.9), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 1.2), (hx1 - hx0 - 0.5, hy1 - hy0 - 0.5, 2.3)))
    reb.prim("cube", "Hut door", mat("red paint"), (HUT_DOOR[0] - 0.42, hy1 + 0.35, 1.0), (0.05, 0.9, 2.0), rot=(0, 0, 0.35))
    reb.prim("cube", "Hut step", mat("concrete"), ((HUT_DOOR[0] + HUT_DOOR[1]) / 2, hy1 + 0.25, 0.06), (1.2, 0.5, 0.12))
    reb.prim("cube", "East window glass", reb.mat_glass("Hut glass", (0.5, 0.55, 0.55)), (hx1 - 0.05, 3.95, 1.4), (0.01, 1.3, 0.8))
    radio_glow = reb.mat_emit("Radio dial glow", (1.0, 0.55, 0.15), 6)
    reb.prim("cube", "Radio dial seen through the window", radio_glow, (hx1 - 0.6, 4.3, 1.1), (0.02, 0.12, 0.05))
    reb.point("Radio glow in the hut", (hx1 - 0.7, 4.2, 1.2), 3, (1.0, 0.55, 0.2), 0.05)
    reb.prim("cube", "Hut sign", mat("white paint"), ((hx0 + hx1) / 2, hy1 + 0.02, 2.2), (1.8, 0.03, 0.3))
    kit.text("Hut sign words", "ARKLAY SUMMIT WEATHER STN", mat("black"), ((hx0 + hx1) / 2, hy1 + 0.045, 2.2), size=0.11, rot=(math.pi / 2, 0, math.pi))
    kit.splat("Bloody handprint on the door frame", mat("old blood"), (HUT_DOOR[1] + 0.06, hy1 + 0.012, 1.2), 0.06, rot=(math.pi / 2, 0, 0), seed=5)
    kit.rod("Aerial wire", mat("iron"), (hx0 + 0.3, hy0 + 0.3, 2.7), (hx0 + 0.3, hy0 + 0.3, 6.0), 0.02)
    kit.rod("Aerial span", mat("iron"), (hx0 + 0.3, hy0 + 0.3, 5.9), (10.0, -20.0, 8.0), 0.006, 4)
    reb.prim("cyl", "Gas bottle", mat("red paint"), (hx0 - 0.25, 4.8, 0.5), (0.35, 0.35, 1.0), segments=14)
    # The anemometer on its pole by the hut, cups turning.
    kit.rod("Anemometer pole", mat("steel"), (6.4, 2.0, height(6.4, 2.0)), (6.4, 2.0, 5.0), 0.04)
    for z in (1.5, 3.0):
        kit.rod("Pole stay", mat("iron"), (6.4, 2.0, z + 1.0), (6.4 + 1.5 * (1 if z < 2 else -0.6), 2.0 - 1.4, height(6.4, 2.0)), 0.006, 4)
    hub = reb.prim("cyl", "Anemometer hub", mat("steel"), (6.4, 2.0, 5.05), (0.06, 0.06, 0.1), segments=10)
    for i in range(3):
        a = 2 * math.pi * i / 3
        arm = kit.rod("Anemometer arm", mat("steel"), (0, 0, 0), (math.cos(a) * 0.32, math.sin(a) * 0.32, 0), 0.008, 4)
        arm.parent = hub
        cup = reb.prim("sphere", "Anemometer cup", mat("white paint"), (math.cos(a) * 0.32, math.sin(a) * 0.32, 0), (0.12, 0.12, 0.12), rot=(0, 0, a), segments=10)
        cup.parent = hub
    vane = reb.prim("cube", "Wind vane", mat("black"), (6.4, 2.0, 4.6), (0.6, 0.02, 0.15), rot=(0, 0, 0.6))
    vane.location.z = 4.6

    # ---- The instrument screen, open, and what he dropped by it.
    sx, sy = 7.6, 4.2
    for dx in (-0.25, 0.25):
        for dy in (-0.2, 0.2):
            kit.rod("Screen leg", timber, (sx + dx, sy + dy, 0), (sx + dx, sy + dy, 1.1), 0.03)
    reb.wall(reb.prim("cube", "Instrument screen", louvre, (sx, sy, 1.35), (0.65, 0.5, 0.55), bevel=0.01))
    for i in range(6):
        reb.prim("cube", "Louvre", mat("black"), (sx - 0.326, sy, 1.13 + i * 0.08), (0.004, 0.44, 0.012))
    reb.prim("cube", "Screen roof", louvre, (sx, sy, 1.66), (0.75, 0.62, 0.05), rot=(0.12, 0, 0))
    reb.prim("cube", "Screen door, open", louvre, (sx + 0.08, sy + 0.5, 1.35), (0.5, 0.02, 0.5), rot=(0, 0, 1.0))
    kit.rod("Thermometer, broken", mat("glass"), (sx, sy + 0.1, 1.3), (sx + 0.05, sy + 0.12, 1.5), 0.008, 6)
    kit.shards("Thermometer glass", (sx + 0.1, sy + 0.5, 0.0), spread=0.3, count=10, seed=2)
    clip = reb.prim("cube", "Clipboard", timber, (sx + 0.6, sy + 0.8, 0.012), (0.24, 0.32, 0.012), rot=(0, 0, 0.5))
    sheet = reb.prim("cube", "Readings sheet", mat("paper"), (0.0, 0.14, 0.0), (0.21, 0.28, 0.002))
    sheet.location = (sx + 0.6, sy + 0.8 - 0.14, 0.022)
    sheet.rotation_euler = (0.25, 0, 0.5)
    reb.prim("sphere", "Knit cap", reb.mat_plain("Cap wool", (0.08, 0.15, 0.32), 0.95), (sx - 0.5, sy + 1.0, 0.06), (0.22, 0.2, 0.12))
    reb.prim("cube", "Glasses", mat("black"), (sx + 0.15, sy + 1.25, 0.01), (0.13, 0.04, 0.01), rot=(0, 0, 2.2))
    kit.shards("Glasses lens", (sx + 0.18, sy + 1.25, 0.0), spread=0.08, count=4, seed=8)
    for i in range(7):
        a = rng.uniform(0, 6.3)
        reb.prim("cube", f"Feather {i}", mat("feathers"), (sx + rng.uniform(-0.8, 0.9), sy + rng.uniform(0.3, 1.6), 0.006), (0.12, 0.025, 0.003), rot=(0, 0, a))
    kit.splat("Blood at the screen", mat("blood"), (sx + 0.1, sy + 0.9, 0.0), 0.28, seed=11, stretch=(1.3, 1.0))
    # His drops north along the ridge, toward the mast.
    pts = [(sx + 0.3, sy + 0.6), (8.6, 3.0), (9.4, 2.0), (9.9, 0.8)]
    k = 0
    for a, b in zip(pts, pts[1:]):
        for i in range(5):
            t = i / 5
            x = a[0] + (b[0] - a[0]) * t + rng.uniform(-0.12, 0.12)
            y = a[1] + (b[1] - a[1]) * t + rng.uniform(-0.12, 0.12)
            kit.splat(f"Drop {k}", mat("blood"), (x, y, height(x, y)), rng.uniform(0.03, 0.06), seed=30 + k, lumps=0.4)
            k += 1

    # ---- The deer, opened, with the crows at it.
    deer("Dead deer", (11.6, 7.6), 0.4)
    kit.drag_trail("Deer drag", mat("old blood"), [(14.0, 9.4), (13.0, 8.6), (11.9, 7.8)], width=0.35, seed=3, height=height)
    kit.splat("Deer blood", mat("blood"), (11.7, 7.4, height(11.7, 7.4)), 0.55, seed=12, stretch=(1.5, 1.0))
    kit.bones("Picked bones", (12.5, 6.8, height(12.5, 6.8)), spread=0.4, seed=4, skull=False)
    pecker, _ = kit.crow("Crow at the deer", (11.55, 7.0, height(11.55, 7.0)), heading=1.8)
    kit.crow("Crow on the deer", (11.4, 7.7, height(11.4, 7.7) + 0.5), heading=3.6)
    kit.crow("Crow by the deer", (12.4, 8.1, height(12.4, 8.1)), heading=2.6)
    kit.crow("Crow on a cairn", (7.6, 8.4, tops[0] - 0.02), heading=-1.2)
    kit.crow("Crow on the cairn north", (10.6, 2.1, tops[3] - 0.02), heading=1.5)
    kit.crow("Crow on the hut", (4.6, 4.0, 2.72), heading=-0.6)
    flyer, flyer_wings = kit.crow("Crow circling", (9.0, 8.0, 7.5), heading=0.0, perched=False)

    # ---- The mine lift's head house: a timber shed, its headframe and sheave over it.
    ex0, ex1, ey0, ey1 = HEAD
    for ob in kit.walls(ex0 + 0.1, ey0 + 0.1, ex1 - 0.1, ey1 - 0.1, 3.0, boards, openings=[
        ("n", HEAD_DOOR[0], HEAD_DOOR[1], 0.0, 2.2),
        ("w", 12.3, 13.3, 1.3, 2.0),
    ], name="Head house wall"):
        reb.wall(ob)
    reb.prim("cube", "Head house roof", mat("tin"), ((ex0 + ex1) / 2, (ey0 + ey1) / 2, 3.12), (ex1 - ex0 + 0.6, ey1 - ey0 + 0.6, 0.08), rot=(0.08, 0, 0))
    reb.wall(reb.prim("cube", "Head house inside", reb.mat_plain("Head house dark", (0.015, 0.012, 0.01), 0.9), ((ex0 + ex1) / 2, (ey0 + ey1) / 2, 1.4), (ex1 - ex0 - 0.5, ey1 - ey0 - 0.5, 2.8)))
    reb.prim("cube", "Head house door", boards, (HEAD_DOOR[1] + 0.12, ey0 - 0.4, 1.1), (0.05, 0.9, 2.2), rot=(0, 0, -0.4))
    hframe = []
    cx, cy = (ex0 + ex1) / 2, (ey0 + ey1) / 2
    for dx in (-1.4, 1.4):
        for dy in (-1.2, 1.2):
            hframe.append(((cx + dx, cy + dy, 3.1), (cx + dx * 0.25, cy + dy * 0.25, 8.0)))
    for z in (4.6, 6.2):
        f = (z - 3.1) / 4.9
        w, d = 1.4 * (1 - f * 0.75), 1.2 * (1 - f * 0.75)
        for (ax, ay), (bx, by) in (((-w, -d), (w, -d)), ((w, -d), (w, d)), ((w, d), (-w, d)), ((-w, d), (-w, -d))):
            hframe.append(((cx + ax, cy + ay, z), (cx + bx, cy + by, z)))
        hframe.append(((cx - w, cy - d, z), (cx + w, cy + d, z + 1.4)))
    struts("Headframe", timber, hframe, 0.09)
    sheave = reb.prim("cyl", "Sheave wheel", mat("rust"), (cx, cy, 8.4), (1.5, 1.5, 0.12), rot=(math.pi / 2, 0, 0), segments=28)
    reb.prim("cyl", "Sheave hub", mat("iron"), (cx, cy, 8.4), (0.25, 0.25, 0.3), rot=(math.pi / 2, 0, 0), segments=12)
    kit.rod("Hoist rope", mat("iron"), (cx + 0.72, cy, 8.4), (cx + 0.72, cy, 2.9), 0.015, 6)
    kit.rod("Hoist rope back", mat("iron"), (cx - 0.72, cy, 8.4), (cx - 3.0, cy + 6.0, -6.0), 0.015, 6)
    reb.prim("cube", "Lift sign", mat("yellow paint"), (HEAD_DOOR[0] - 0.55, ey0 - 0.01, 1.7), (0.7, 0.03, 0.4))
    kit.text("Lift sign words", "MINE LIFT", mat("black"), (HEAD_DOOR[0] - 0.55, ey0 - 0.03, 1.76), size=0.1)
    kit.text("Lift sign words 2", "NO RIDERS", mat("black"), (HEAD_DOOR[0] - 0.55, ey0 - 0.03, 1.62), size=0.08)
    lift_bulb = reb.point("Bulb in the head house", ((HEAD_DOOR[0] + HEAD_DOOR[1]) / 2, ey0 + 1.2, 2.3), 18, (1.0, 0.75, 0.45), 0.05)
    kit.web("Web in the door", (HEAD_DOOR[0] + 0.02, ey0 - 0.02, 2.18), 0.35, (1, 0))
    kit.drum("Drum by the head house", mat("rust"), (ex0 - 0.5, ey0 + 0.6, 0.0))
    kit.crate("Crate by the head house", mat("planks"), (ex0 - 0.6, ey0 + 1.6, 0.0), rot=0.3)

    # ---- The signpost at the fork: the hut west, the mast north.
    kit.rod("Signpost", timber, (9.6, 7.0, 0), (9.6, 7.0, 2.2), 0.05)
    for i, (words, z, yaw) in enumerate((("SUMMIT  2104 M", 2.05, 0.0), ("< WEATHER STN", 1.8, 0.0), ("MAST  NO ENTRY ^", 1.55, 0.0))):
        reb.prim("cube", f"Sign board {i}", timber, (9.6, 7.0 + 0.06, z), (1.0, 0.03, 0.18), rot=(0, 0, yaw))
        kit.text(f"Sign words {i}", words, mat("white paint"), (9.6, 7.0 + 0.08, z), size=0.075, rot=(math.pi / 2, 0, math.pi))

    # ---- Far along the ridge, the mast with its red light.
    mx, my = MAST_AT
    mz = height(mx, my)
    legs = [(mx - 1.2, my - 1.2), (mx + 1.2, my - 1.2), (mx + 1.2, my + 1.2), (mx - 1.2, my + 1.2)]
    msegs = [((lx, ly, mz), (mx + (lx - mx) * 0.2, my + (ly - my) * 0.2, mz + 34)) for lx, ly in legs]
    for z in range(2, 34, 3):
        f = z / 34
        pts = [(mx + (lx - mx) * (1 - 0.8 * f), my + (ly - my) * (1 - 0.8 * f), mz + z) for lx, ly in legs]
        for i in range(4):
            msegs.append((pts[i], pts[(i + 1) % 4]))
    struts("Far mast", mat("red paint"), msegs, 0.08)
    reb.prim("cube", "Far mast cabin", mat("tin"), (mx + 4, my + 2, mz + 1.2), (3, 2.2, 2.4))
    beacon_m = reb.mat_emit("Far beacon", (1.0, 0.05, 0.02), 40)
    reb.prim("sphere", "Far beacon", beacon_m, (mx, my, mz + 34.5), (0.6, 0.6, 0.6), segments=10)
    beacon = reb.point("Far beacon light", (mx, my, mz + 34.5), 400, (1.0, 0.05, 0.02), 0.3)
    for lx, ly in ((mx - 14, my + 6), (mx + 14, my + 6), (mx, my - 14)):
        kit.rod("Far guy wire", mat("iron"), (lx, ly, height(lx, ly)), (mx, my, mz + 26), 0.03, 4)

    # ---- Cloud: wisps blowing over the ridge, a bank below on both sides.
    cloud = mist_mat("Cloud", (0.8, 0.8, 0.82), 0.75, 0.12)
    thin = mist_mat("Thin cloud", (0.75, 0.76, 0.8), 0.45, 0.25)
    wisps = []
    for i, (x, y, z, w, d, m) in enumerate((
        (-6.0, 8.0, -3.0, 30, 40, cloud), (26.0, 8.0, -4.0, 30, 40, cloud), (10.0, 30.0, -8.0, 50, 20, cloud),
        (10.0, -14.0, 2.5, 30, 14, thin), (10.0, -32.0, 8.0, 36, 14, cloud),
    )):
        ob = reb.prim("plane", f"Cloud wisp {i}", m, (x, y, z), (w, d, 1), rot=(0, 0, rng.uniform(-0.2, 0.2)))
        wisps.append((ob, ob.location.copy(), rng.uniform(0, 6.3), 4.0))
    # Cloud standing off the ridge's flanks, blowing past below the crest.
    for i, (x, y, z, yaw) in enumerate(((-4.0, 4.0, -1.0, math.pi / 2), (-5.0, 13.0, 0.0, math.pi / 2), (24.0, 5.0, -1.5, math.pi / 2), (23.0, 14.0, 0.5, math.pi / 2), (12.0, 21.0, -2.0, 0.0), (2.0, -8.0, 1.0, 0.0))):
        ob = reb.prim("plane", f"Cloud bank {i}", thin, (x, y, z), (16, 7, 1), rot=(math.pi / 2, 0, yaw))
        wisps.append((ob, ob.location.copy(), rng.uniform(0, 6.3), 3.0))
    # The deck overhead, broken: the sun comes through.
    deck = reb.prim("plane", "Cloud deck", mist_mat("Cloud deck", (0.5, 0.5, 0.53), 0.9, 0.03, lo=0.52, hi=0.66), (-6.0, 20.0, 34.0), (320, 320, 1))
    deck.visible_shadow = False
    wisps.append((deck, deck.location.copy(), 0.0, 9.0))

    # ---- Light: the afternoon sun in the south-west, raking across the rock.
    kit.time_light("afternoon", sun_heading=235, sun_energy=4.2, sky=((0.52, 0.5, 0.48), (0.2, 0.25, 0.34), 0.6))
    kit.vista(rng, (10.0, 8.0), (1.0, 0.0), below=-170.0)
    kit.vista(rng, (10.0, 8.0), (-1.0, 0.0), below=-170.0)
    kit.vista(rng, (10.0, 8.0), (0.0, 1.0), below=-170.0)
    kit.vista(rng, (10.0, -40.0), (0.0, -1.0), below=-170.0, ridges=2)

    anim = kit.Anim(16)
    for ob, rest, ph, amp in wisps:
        def drift(k, ob=ob, rest=rest, ph=ph, amp=amp):
            a = anim.phase(k) + ph
            ob.location = rest + Vector((amp * math.sin(a), 0.4 * amp * math.cos(a), 0))
        anim.custom(drift)
    anim.spin(hub, axis=2, turns=1, symmetry=3)
    anim.custom(lambda k: setattr(pecker, "rotation_euler", (0, 0.5 * max(0.0, math.sin(anim.phase(k, 3))), 1.8)))
    anim.flap(flyer_wings, degrees=35)

    def circle(k):
        a = anim.phase(k)
        flyer.location = (9.0 + 4.0 * math.cos(a), 8.0 + 3.0 * math.sin(a), 7.5 + 0.4 * math.sin(2 * a))
        flyer.rotation_euler = (0, 0.25, a + math.pi / 2)
    anim.custom(circle)
    anim.custom(lambda k: setattr(sheet, "rotation_euler", (0.2 + 0.25 * max(0.0, math.sin(anim.phase(k, 2))), 0, 0.5)))
    anim.blink(beacon, beacon_m, on=(0, 6))
    anim.flicker(lift_bulb, None, depth=0.2, dropouts=1)
    anim.sway(grass, amount=0.05)

    # ---- What the game needs.
    room.door("mine-lift", (HEAD_DOOR[0], ey0 - 0.6, HEAD_DOOR[1], ey0), arrive=(15.4, 9.7), face=(0, -1), walk=False)
    room.door("weather", (HUT_DOOR[0], hy1, HUT_DOOR[1], hy1 + 0.6), arrive=(3.65, 7.2), face=(0, 1), walk=False)
    room.door("mast", (8.0, Y0, 12.0, Y0 + 0.6), arrive=(10.0, 2.8), face=(0, 1))
    room.check((10.6, 6.6, 12.8, 8.4), "A deer, torn open. The crows have had its eyes.\nThey don't fly off when I come close.")
    room.check((sx - 0.6, sy + 0.3, sx + 0.9, sy + 1.5), "His clipboard. Wind speed, temperature, cloud, every hour since midnight.\nThe last line just stops.\nHis cap, his glasses. Feathers everywhere.")
    room.check((sx - 0.5, sy - 0.4, sx + 0.5, sy + 0.3), "An instrument screen. The door's open and the thermometer's smashed.")
    room.check((8.4, 1.0, 10.4, 3.4), "Blood, a drop every step. Someone went north along the ridge, toward the mast.")
    room.check((9.1, 7.2, 10.1, 7.8), "SUMMIT 2104 M. WEATHER STATION. MAST, NO ENTRY.")
    room.check((HEAD_DOOR[0] - 1.2, ey0 - 0.6, HEAD_DOOR[0], ey0), "MINE LIFT. NO RIDERS.\nI rode it anyway.")
    room.check((hx1 - 0.8, hy1, hx1, hy1 + 0.6), "ARKLAY SUMMIT WEATHER STATION. There's a light on inside.")
    room.entry = "The top of the mountain. Nothing grows up here.\nJust rock, and crows."
    room.export(anim)


build()
