"""The gondola's upper station, morning: ARKLAY SKYWAY, the top of the line.

What it tells: the last car came up before dawn with something in it. Its
door was forced from inside and the glass is smeared red. Whatever was in
it was dragged out across the platform: the smear runs from the car door to
the rail on the east side and stops, and the crows are working at what is
caught on the rail. A hiker's pack lies split open where it was dropped,
one boot beside it. The drive is dead: the gearbox under the wheel house
stands open with its cog sheared and a spanner dropped in the oil, an OUT
OF SERVICE board hangs from one chain, and the operator's booth door stands
open. The station looks out over the valley, where the cable runs down into
the mist.

Metres: the platform is x 2-17, y 2-13 at z 0. North (y 2) the trail comes
in from the gorge at x 3-6. The booth is x 12.5-15.7, y 2.5-5.1, its door
in the south wall at x 14.1-15.0, its big window in the west wall. The car
hangs at the south edge, x 7.0-9.6, y 11.0-12.6, its door facing north. The
wheel house is in the south-west, x 2.5-6.0, y 9.0-12.6. South of y 13 the
mountain drops away. The east path leaves at x 17, y 8-10; the power line
track's gate is in the west edge at y 6-8.

The cliff path: the floor runs on east from the platform's east gap along a
ledge cut in the gorge's side, x 17-20.4, 2.0-2.2 m wide (y 8-10 to x 18.7,
then y 8.6-10.8). Rock rises on its north side; on its south the mountain
drops into the gorge, with a rope rail on iron stakes along the lip. The
operator ran this way. Where the ledge jinks he grabbed the rope, the
third stake pulled out of the rock, and he went over: the empty stake
hole, his boots' scrape to the lip, his cap, and the rope hanging slack
in a loop over the drop with the stake swinging on the end of it. At the
far end, x 19.8-20.4, the path goes on east. The room is shifted 1.4 m
west at export to fit the floor in the game's 0.6-19 m.

Moving: the board on its one chain, the car rocking on the cable, a crow
pecking, grass in the wind, the rope and its stake swinging over the drop.
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

X0, X1, Y0, Y1 = 2.0, 17.0, 2.0, 13.0
BOOTH = (12.5, 15.7, 2.5, 5.1)
BOOTH_DOOR = (14.1, 15.0)
CAR = (7.0, 9.6, 11.0, 12.6)
WHEEL = (2.5, 6.0, 9.0, 12.6)
X_END = 20.4
SHIFT = (-1.4, 0.0)
WALK = [(X1, 8.0, 18.7, 10.0), (18.7, 8.6, X_END, 10.8)]   # x0, y0, x1, y1
LEDGE = [(X1, 9.0), (18.5, 9.0), (18.9, 9.7), (X_END, 9.7), (24.0, 10.3), (30.0, 10.0), (40.0, 9.0)]
LEDGE_HALF = 1.4
NEAR = (12.0, -2.0, 36.0, 22.0)


def ledge_y(x):
    """The middle of the ledge at x."""
    for (xa, ya), (xb, yb) in zip(LEDGE, LEDGE[1:]):
        if x <= xb:
            return ya + (yb - ya) * max(0.0, (x - xa) / (xb - xa))
    return LEDGE[-1][1]


def height(x, y):
    """The platform flat; the mountain rising north and west, falling away south;
    east, the ledge along the gorge: rock rising north of it, the drop south."""
    if X0 - 0.3 < x < X1 + 0.3 and Y0 - 0.3 < y < Y1 + 0.4:
        return -0.4
    n = noise.noise(Vector((x * 0.2, y * 0.2, 1)))
    if x >= X1 + 0.3:
        d = y - ledge_y(x)
        if abs(d) <= LEDGE_HALF:
            return 0.02 * n
        if d > 0:
            e = d - LEDGE_HALF
            return -min(88.0, e * 3.2 + e * e * 0.5) + 0.4 * n * min(1.0, e)
        e = -d - LEDGE_HALF
        grow = min(1.0, (x - X1 - 0.3) / 3.0)
        return grow * min(6.5, e * 2.6) + 0.5 * n * min(1.0, e / 2.0)
    h = 0.3 * n
    if y > Y1 + 0.4:
        h -= (y - Y1 - 0.4) * 1.6
    if y < Y0 - 0.3:
        h += (Y0 - 0.3 - y) * 0.5
    if x < X0 - 0.3:
        h += (X0 - 0.3 - x) * 0.3
    if x > X1 + 0.3:
        h -= (x - X1 - 0.3) * 0.15
    return h


def steep(base, name):
    """`base` on the level, bare dark rock where the ground falls steeply:
    the gorge's side, the cliff over the ledge."""
    m = base.copy()
    m.name = name
    nodes, links = m.node_tree.nodes, m.node_tree.links
    out = nodes["Material Output"]
    surf = out.inputs["Surface"].links[0].from_socket
    rock = nodes.new("ShaderNodeBsdfPrincipled")
    rock.inputs["Roughness"].default_value = 0.9
    streaks = reb.noise_tex(nodes, links, 2.0, 6, 0.7)
    tone = reb.ramp(nodes, links, streaks.outputs["Fac"], [(0.3, (0.025, 0.026, 0.024)), (0.55, (0.07, 0.07, 0.065)), (0.75, (0.13, 0.125, 0.115))])
    links.new(tone.outputs["Color"], rock.inputs["Base Color"])
    geo = nodes.new("ShaderNodeNewGeometry")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geo.outputs["Normal"], sep.inputs[0])
    n = reb.noise_tex(nodes, links, 0.6, 4, 0.6)
    wob = nodes.new("ShaderNodeMath")
    wob.operation = "MULTIPLY_ADD"
    wob.inputs[1].default_value = 0.25
    links.new(n.outputs["Fac"], wob.inputs[0])
    links.new(sep.outputs["Z"], wob.inputs[2])
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.75
    mr.inputs["From Max"].default_value = 0.95
    links.new(wob.outputs[0], mr.inputs["Value"])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(mr.outputs["Result"], mix.inputs["Fac"])
    links.new(rock.outputs[0], mix.inputs[1])
    links.new(surf, mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def cliff_path(rng):
    """The ledge east: the rope rail on its stakes along the lip, the stake
    pulled out and the rope hanging in a loop over the drop, his cap and
    the scrape to the edge. Returns the hanging rope and its pivot."""
    rope_m = reb.mat_plain("Rope", (0.48, 0.4, 0.25), 0.9)
    lip = lambda x: ledge_y(x) + LEDGE_HALF - 0.15
    stakes = [17.6, 18.9, 20.3, 21.7, 23.1, 24.5, 25.9, 27.3, 28.7]
    pulled = 20.3
    tops = {}
    for x in stakes:
        y = lip(x)
        top = Vector((x + 0.05, y + 0.12, 0.95))
        tops[x] = top
        if x != pulled:
            kit.rod("Rail stake", mat("rust"), (x, y, height(x, y) - 0.2), tuple(top), 0.025, 6)
            kit.rod("Stake eye", mat("rust"), tuple(top), tuple(top + Vector((0, 0, 0.08))), 0.04, 6)
    good = [x for x in stakes if x != pulled]
    for a, b in zip(good, good[1:]):
        if a < pulled < b:
            continue
        pa, pb = tops[a], tops[b]
        for k in range(6):
            t0, t1 = k / 6, (k + 1) / 6
            q0 = pa.lerp(pb, t0) - Vector((0, 0, 0.12 * math.sin(math.pi * t0)))
            q1 = pa.lerp(pb, t1) - Vector((0, 0, 0.12 * math.sin(math.pi * t1)))
            kit.rod("Rope rail", rope_m, tuple(q0), tuple(q1), 0.02, 5)
    # The loop over the drop, the stake on the end of it: one swinging piece.
    a, b = tops[18.9], tops[21.7]
    mid = (a + b) / 2
    pivot = reb.prim("sphere", "Rope pivot", None, tuple(mid), (0.02, 0.02, 0.02))
    pivot.hide_render = True
    bottom = Vector((pulled, lip(pulled) + 1.1, -1.9))
    pts = []
    for k in range(11):
        t = k / 10
        p = a.lerp(b, t)
        sag = math.sin(math.pi * t)
        pts.append(Vector((p.x, p.y + (bottom.y - mid.y) * sag ** 0.8, p.z - (mid.z - bottom.z) * sag ** 0.7)))
    loop = [kit.rod("Hanging rope", rope_m, tuple(p - mid), tuple(q - mid), 0.026, 6) for p, q in zip(pts, pts[1:])]
    lo = min(pts, key=lambda v: v.z)
    loop.append(kit.rod("Pulled stake", mat("rust"), tuple(lo - mid + Vector((0, 0, 0.05))), tuple(lo - mid + Vector((0.25, 0.1, -0.85))), 0.025, 6))
    loop.append(kit.rod("Pulled stake eye", mat("rust"), tuple(lo - mid), tuple(lo - mid + Vector((0, 0, 0.08))), 0.04, 6))
    rope = kit.join("Hanging rope", loop, origin=(0, 0, 0))
    rope.parent = pivot
    # The hole the stake came out of, his scrape to the lip, his cap.
    y = lip(pulled)
    kit.splat("Stake hole", mat("black"), (pulled, y, height(pulled, y) + 0.003), 0.05, seed=3)
    kit.splat("Broken rock at the hole", reb.mat_plain("Fresh rock", (0.3, 0.29, 0.26), 0.9), (pulled + 0.1, y + 0.05, height(pulled, y) + 0.002), 0.16, seed=4, stretch=(1.4, 0.7))
    for k in range(3):
        x0 = pulled - 1.4 + k * 0.25
        kit.drag_trail(f"Scrape {k}", reb.mat_plain("Scraped dirt", (0.2, 0.15, 0.1), 0.95), [(x0, ledge_y(x0) - 0.2), (x0 + 0.7, ledge_y(x0) + 0.5), (x0 + 1.2, lip(x0 + 1.2) + 0.1)], width=0.1, seed=20 + k, height=height)
    cap = reb.mat_plain("Cap navy", (0.04, 0.05, 0.1), 0.8)
    cx, cy = pulled - 0.6, ledge_y(pulled) + 0.4
    reb.prim("sphere", "Operator's cap", cap, (cx, cy, height(cx, cy) + 0.04), (0.22, 0.2, 0.12), rot=(0, 0, 0.7), segments=12)
    reb.prim("cube", "Cap peak", cap, (cx + 0.12, cy + 0.1, height(cx, cy) + 0.012), (0.14, 0.16, 0.012), rot=(0, 0, 0.7))
    kit.splat("Blood on the lip", mat("blood"), (pulled + 0.3, lip(pulled) + 0.05, height(pulled + 0.3, lip(pulled)) + 0.004), 0.1, seed=6, stretch=(1.6, 0.6))
    # Rock fallen on the ledge from the cliff; the cliff's foot.
    rv, rf = [], []
    for _ in range(26):
        x = rng.uniform(17.4, 32.0)
        if 20.8 < x < 25.0:
            continue
        y = ledge_y(x) - LEDGE_HALF - rng.uniform(-0.2, 0.6)
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.2, 0.7), rv, rf)
    for (x, y, r) in ((17.9, 7.2, 0.6), (18.4, 7.6, 0.45)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Rock at the cliff's foot", rv, rf, mat("rock"))
    return rope, pivot


def build():
    rng = random.Random(77)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X_END, Y1), shift=SHIFT)
    room.ground("concrete")  # the slab
    room.floor((17.0, 8.0, X_END, 10.8), "earth")  # the ledge east
    room.camera((3.2, 0.8, 3.8), (10.5, 10.0, 0.2), 200, "from the trail's mouth: the platform, the car at the edge, the smear to the rail")
    room.camera((16.6, 12.6, 3.2), (8.0, 4.5, 0.8), 200, "from the south-east corner by the drop: the booth, the pack, the trail in")
    room.camera((13.2, 6.2, 3.0), (6.0, 12.4, 0.6), 200, "from in front of the booth: the car, the wheel house, the valley beyond")
    room.camera((2.5, 4.0, 3.4), (12.5, 9.5, 0.6), 200, "from the line track's gate: the length of the platform to the east path")
    room.camera((15.4, 12.6, 3.6), (21.4, 9.0, 0.2), 200, "from the platform's south-east corner: the ledge east along the gorge, the rope hanging over the drop")
    room.camera((23.2, 9.4, 3.0), (17.0, 9.8, -0.3), 200, "from along the ledge east: back to the platform, the slack rope over the drop, the cliff over it")

    concrete = kit.dirtied(mat("concrete"), 0.7, scale=1.2)
    paint = mat("green paint")
    car_red = reb.mat_surface("Car paint", [(0.0, (0.22, 0.03, 0.02)), (0.8, (0.35, 0.05, 0.03)), (1.0, (0.18, 0.1, 0.06))], scale=4, rough=0.45, bump=0.1)
    oil = reb.mat_plain("Oil", (0.02, 0.018, 0.015), 0.15)
    panel = kit.boards("Booth boards", (0.2, 0.22, 0.17), width=0.16, grime=0.7)

    # ---- Ground: the slab, the mountain round it, cracks with grass in them.
    side = steep(mat("grass"), "Grass, steep")
    nx0, ny0, nx1, ny1 = NEAR
    reb.terrain("Mountainside near", side, (nx0, nx1), (ny0, ny1), height, step=0.25)
    reb.terrain("Mountainside", side, (-14, 50), (-12, 40), lambda x, y: height(x, y) - (3.0 if nx0 + 1 < x < nx1 - 1 and ny0 + 1 < y < ny1 - 1 else 0.0), step=0.6)
    # The gorge's far side: its floor 90 m down, its wall rising beyond, wooded,
    # so a camera looking down the drop finds rock and trees, not sky.
    def far_side(x, y):
        n = noise.noise(Vector((x * 0.05, y * 0.05, 7.0)))
        return -90.0 + max(0.0, y - 46.0) * 2.4 + 6.0 * n
    reb.terrain("Gorge far side", side, (-30, 80), (36, 110), far_side, step=2.0)
    tv, tf = [], []
    for _ in range(260):
        x, y = rng.uniform(-30, 80), rng.uniform(40, 105)
        reb.conifer(rng, Vector((x, y, far_side(x, y))), rng.uniform(14, 24), tv, tf)
    reb.mesh_object("Gorge spruce", tv, tf, mat("needles"))
    # Granite standing out of the cliff over the ledge and under its lip.
    cv, cf = [], []
    for x in (19.5, 22.5, 25.5, 28.5, 32.0, 36.0):
        y = ledge_y(x)
        kit.crag(rng, cv, cf, (x, y - LEDGE_HALF - 2.2, 2.0), (1.4, 1.2, 2.8), floor=-0.8)
        kit.crag(rng, cv, cf, (x + 1.2, y + LEDGE_HALF + 2.0, -5.8), (1.6, 1.3, 3.2), floor=-0.9)
    reb.mesh_object("Gorge crags", cv, cf, steep(mat("rock"), "Granite, steep"), smooth=False)
    reb.prim("cube", "Slab edge east", mat("concrete"), (X1 + 0.32, (10.4 + Y1 + 0.5) / 2, -1.2), (0.3, Y1 + 0.5 - 10.4, 2.4))
    reb.prim("cube", "Platform slab", concrete, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.15), (X1 - X0 + 0.6, Y1 - Y0 + 0.8, 0.3))
    reb.prim("cube", "Slab edge", mat("concrete"), ((X0 + X1) / 2, Y1 + 0.42, -1.2), (X1 - X0 + 0.6, 0.3, 2.4))
    kit.cracks("Cracks", mat("black"), (X0, Y0, X1, Y1), count=16, seed=1)
    kit.path_strip("Trail in", mat("dirt"), [(4.5, -6.0), (4.5, -2.0), (4.6, 1.5), (4.7, 2.4)], height, width=0.9)

    # ---- The edge: a rail along the drop, the queue rails, the sign.
    for x in [X0 + 0.2 + i * 1.5 for i in range(11)]:
        if CAR[0] - 0.2 < x < CAR[1] + 0.2:
            continue
        kit.rod("Rail post", mat("rust"), (x, Y1 + 0.15, 0), (x, Y1 + 0.15, 1.1), 0.03)
    kit.rod("Rail", mat("rust"), (X0, Y1 + 0.15, 1.1), (CAR[0] - 0.1, Y1 + 0.15, 1.1), 0.025)
    kit.rod("Rail", mat("rust"), (CAR[1] + 0.1, Y1 + 0.15, 1.1), (X1, Y1 + 0.15, 1.1), 0.025)
    kit.rod("Rail", mat("rust"), (X1 + 0.1, Y0, 1.1), (X1 + 0.1, 8.0, 1.1), 0.025)
    kit.rod("Rail", mat("rust"), (X1 + 0.1, 10.0, 1.1), (X1 + 0.1, Y1 + 0.15, 1.1), 0.025)
    for y in [Y0 + 0.5 + i * 1.4 for i in range(9)]:
        if 8.0 < y < 10.0:
            continue
        kit.rod("Rail post", mat("rust"), (X1 + 0.1, y, 0), (X1 + 0.1, y, 1.1), 0.03)
    # Queue rails: posts and sagging chains toward the car.
    for x in (7.0, 9.6):
        for y in (6.5, 8.5, 10.4):
            kit.rod("Queue post", mat("steel"), (x, y, 0), (x, y, 0.95), 0.03)
    for x in (7.0, 9.6):
        for y0, y1 in ((6.5, 8.5), (8.5, 10.4)):
            for k in range(8):
                t0, t1 = k / 8, (k + 1) / 8
                z0 = 0.9 - 0.25 * math.sin(math.pi * t0)
                z1 = 0.9 - 0.25 * math.sin(math.pi * t1)
                kit.rod("Queue chain", mat("iron"), (x, y0 + (y1 - y0) * t0, z0), (x, y0 + (y1 - y0) * t1, z1), 0.008, 4)
    # The station's sign on two posts at the trail's mouth.
    for x in (8.6, 11.4):
        kit.rod("Sign post", mat("dark wood"), (x, 2.4, 0), (x, 2.4, 2.6), 0.06)
    reb.prim("cube", "Station sign", reb.mat_plain("Sign green", (0.06, 0.16, 0.1), 0.6), (10.0, 2.4, 2.25), (3.0, 0.06, 0.6))
    kit.text("Sign words", "ARKLAY SKYWAY", mat("white paint"), (10.0, 2.46, 2.35), size=0.24, rot=(math.pi / 2, 0, math.pi))
    kit.text("Sign words 2", "UPPER STATION  ELEV 1840", mat("white paint"), (10.0, 2.46, 2.1), size=0.12, rot=(math.pi / 2, 0, math.pi))

    # ---- The booth, outside: green boards, the window west, the door south standing open.
    bx0, bx1, by0, by1 = BOOTH
    for ob in kit.walls(bx0 + 0.12, by0 + 0.12, bx1 - 0.12, by1 - 0.12, 2.4, panel, openings=[
        ("s", BOOTH_DOOR[0], BOOTH_DOOR[1], 0.0, 2.05),
        ("w", by0 + 0.45, by1 - 0.35, 1.0, 1.95),
    ], name="Booth wall"):
        reb.wall(ob)
    reb.prim("cube", "Booth roof", mat("tin"), ((bx0 + bx1) / 2, (by0 + by1) / 2, 2.55), (bx1 - bx0 + 0.6, by1 - by0 + 0.6, 0.08), rot=(0.08, 0, 0))
    reb.prim("cube", "Booth floor", mat("black"), ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.005), (bx1 - bx0 - 0.3, by1 - by0 - 0.3, 0.01))
    reb.prim("cube", "Booth door", paint, (BOOTH_DOOR[1] + 0.45, by1 + 0.04, 1.02), (0.9, 0.05, 2.04))
    reb.prim("cube", "Booth window glass", reb.mat_glass("Grimy glass", (0.5, 0.55, 0.5)), (bx0 + 0.1, (by0 + by1) / 2 + 0.05, 1.48), (0.01, by1 - by0 - 0.8, 0.95))
    reb.prim("cube", "Booth inside", reb.mat_plain("Booth dark", (0.02, 0.025, 0.02), 0.9), ((bx0 + bx1) / 2, (by0 + by1) / 2, 1.2), (bx1 - bx0 - 0.5, by1 - by0 - 0.5, 2.3))
    kit.splat("Handprint on the booth", mat("blood"), (BOOTH_DOOR[0] - 0.08, by1 + 0.0, 1.22), 0.06, rot=(math.pi / 2, 0, 0), seed=3)
    glow = reb.point("Strip light in the booth", ((bx0 + bx1) / 2, (by0 + by1) / 2, 2.1), 12, (0.75, 0.95, 0.85), 0.3)

    # ---- The wheel house: steel posts, a tin roof, the bullwheel, the gearbox open.
    wx0, wx1, wy0, wy1 = WHEEL
    for x in (wx0, wx1):
        for y in (wy0, wy1):
            reb.wall(kit.rod("Wheel house post", mat("rust"), (x, y, 0), (x, y, 4.2), 0.09))
    reb.prim("cube", "Wheel house roof", mat("tin"), ((wx0 + wx1) / 2, (wy0 + wy1) / 2, 4.3), (wx1 - wx0 + 0.8, wy1 - wy0 + 0.8, 0.08), rot=(0.05, 0, 0))
    wheel = reb.prim("cyl", "Bullwheel rim", mat("rust"), ((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 3.1), (3.2, 3.2, 0.18), segments=40)
    reb.prim("cyl", "Bullwheel hub", mat("iron"), ((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 3.1), (0.5, 0.5, 0.4), segments=20)
    for i in range(6):
        a = math.pi * i / 3
        c = Vector(((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 3.1))
        kit.rod("Spoke", mat("rust"), c, c + Vector((math.cos(a) * 1.55, math.sin(a) * 1.55, 0)), 0.05)
    kit.rod("Bullwheel shaft", mat("iron"), ((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 3.1), ((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 1.0), 0.12)
    gear = reb.prim("cube", "Gearbox", mat("green paint"), ((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 0.55), (1.6, 1.2, 1.1), bevel=0.04)
    reb.mask(reb.wall(gear))
    reb.prim("cube", "Gearbox cover", mat("green paint"), ((wx0 + wx1) / 2 + 1.2, (wy0 + wy1) / 2 - 0.2, 0.05), (1.2, 0.9, 0.05), rot=(0, 0, 0.4))
    cog = reb.prim("cyl", "Sheared cog", mat("steel"), ((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 1.15), (0.7, 0.7, 0.12), segments=24)
    for i in range(18):
        if 5 <= i <= 8:
            continue
        a = 2 * math.pi * i / 18
        c = Vector(((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 1.15))
        reb.prim("cube", "Cog tooth", mat("steel"), c + Vector((math.cos(a) * 0.38, math.sin(a) * 0.38, 0)), (0.08, 0.05, 0.12), rot=(0, 0, a))
    for i in range(3):
        reb.prim("cube", "Broken tooth", mat("steel"), ((wx0 + wx1) / 2 + 0.9 + i * 0.2, (wy0 + wy1) / 2 + 0.9, 0.02), (0.08, 0.05, 0.03), rot=(0, 0, rng.uniform(0, 3)))
    kit.splat("Oil under the gearbox", oil, ((wx0 + wx1) / 2 + 0.6, (wy0 + wy1) / 2 + 0.3, 0.0), 0.7, seed=4, stretch=(1.4, 1.0))
    reb.prim("cube", "Dropped spanner", mat("steel"), ((wx0 + wx1) / 2 + 0.8, (wy0 + wy1) / 2 + 0.1, 0.01), (0.35, 0.04, 0.015), rot=(0, 0, 0.6))
    kit.drum("Grease drum", mat("rust"), (wx0 + 0.5, wy0 + 0.5, 0.0))
    kit.drum("Drum on its side", mat("rust"), (wx0 + 0.7, wy0 + 1.5, 0.0), tipped=True, rot=0.4)
    # The haul cables: from the wheel out over the car and down the mountain.
    hub = Vector(((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 3.1))
    grip_at = Vector(((CAR[0] + CAR[1]) / 2, (CAR[2] + CAR[3]) / 2, 3.45))
    far = Vector((9.0, 120.0, -70.0))
    kit.rod("Haul cable, up", mat("iron"), hub + Vector((1.55, 0, 0)), grip_at, 0.022, 6)
    kit.rod("Haul cable, on down", mat("iron"), grip_at, far, 0.022, 6)
    kit.rod("Haul cable, return", mat("iron"), hub - Vector((1.55, 0, 0)), far - Vector((4.0, 0, 0)), 0.022, 6)
    # A pylon below in the valley, the cable running to it.
    for dx in (-1.2, 1.2):
        kit.rod("Pylon leg", mat("iron"), (9.0 + dx, 60.0, -52.0), (9.0, 60.0, -30.0), 0.25)
    reb.prim("cube", "Pylon arm", mat("iron"), (9.0, 60.0, -30.0), (5.0, 0.4, 0.4))

    # ---- The car: red, its door forced, glass smeared from inside.
    cx0, cx1, cy0, cy1 = CAR
    car = reb.prim("cube", "Gondola car", car_red, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 1.25), (cx1 - cx0, cy1 - cy0, 2.1), bevel=0.25)
    reb.prim("cube", "Car windows", reb.mat_glass("Car glass", (0.4, 0.45, 0.45)), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 1.65), (cx1 - cx0 + 0.02, cy1 - cy0 + 0.02, 0.75))
    reb.prim("cube", "Car inside", reb.mat_plain("Car dark", (0.02, 0.012, 0.01), 0.9), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 1.25), (cx1 - cx0 - 0.15, cy1 - cy0 - 0.15, 1.9))
    reb.prim("cube", "Car door, forced", car_red, ((cx0 + cx1) / 2 + 0.75, cy0 - 0.12, 1.05), (1.0, 0.06, 1.8), rot=(0, 0, -0.12))
    reb.prim("cube", "Car doorway", reb.mat_plain("Car dark", (0.02, 0.012, 0.01), 0.9), ((cx0 + cx1) / 2 - 0.2, cy0 - 0.01, 1.0), (1.0, 0.02, 1.8))
    for i in range(4):
        kit.splat(f"Smear on the glass {i}", mat("blood"), (cx0 + 0.4 + i * 0.55, cy0 - 0.012, 1.6 + rng.uniform(-0.2, 0.2)), 0.16, rot=(math.pi / 2, 0, 0), seed=60 + i, stretch=(0.6, 1.4))
    kit.text("Car number", "4", mat("white paint"), (cx1 - 0.35, cy0 - 0.012, 0.75), size=0.3, rot=(math.pi / 2, 0, math.pi))
    hanger = kit.rod("Car hanger", mat("iron"), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 2.3), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 3.4), 0.06)
    grip = reb.prim("cube", "Car grip", mat("iron"), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 3.45), (0.5, 0.3, 0.25))
    car_parts = [car] + [o for o in __import__("bpy").data.objects if o.name.startswith(("Car windows", "Car inside", "Car door", "Car doorway", "Smear on the glass", "Car number", "Car hanger", "Car grip"))]
    pivot = reb.prim("sphere", "Car pivot", mat("iron"), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 3.45), (0.05, 0.05, 0.05))
    for p in car_parts:
        p.parent = pivot
        p.matrix_parent_inverse = pivot.matrix_world.inverted()
    reb.wall(reb.prim("cube", "Car footprint", None, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.5), (cx1 - cx0, cy1 - cy0, 1.0))).hide_render = True

    # ---- What was dragged from it: the smear to the east rail, the crows at the end.
    kit.drag_trail("Drag smear", mat("old blood"), [(8.0, 10.9), (9.5, 10.0), (11.5, 9.6), (13.5, 9.9), (15.5, 10.6), (16.8, 11.2)], width=0.45, seed=7, z=0.0)
    kit.drag_trail("Fresh smear", mat("blood"), [(8.1, 10.8), (9.4, 10.1), (11.0, 9.7)], width=0.25, seed=8, z=0.002)
    kit.splat("Pool at the rail", mat("blood"), (16.7, 11.3, 0.0), 0.5, seed=9, stretch=(1.2, 1.6))
    reb.cloth("Rag of shirt on the rail", mat("flannel"), (17.12, 11.2, 0.75), (0.05, 0.45), rot=(0, math.pi / 2, 0), cuts=8, lumps=0.05, seed=2)
    crows = []
    for i, (x, y, z, hd) in enumerate(((16.75, 11.4, 0.0, 2.6), (17.1, 10.8, 1.12, 3.4), (16.3, 11.0, 0.0, 0.8))):
        b, w = kit.crow(f"Crow {i}", (x, y, z), heading=hd)
        crows.append(b)
    kit.crow("Crow on the sign", (9.2, 2.4, 2.56), heading=1.6)
    kit.crow("Crow on the roof", (13.6, 3.6, 2.66), heading=4.0)
    # The hiker's pack, split, and a boot.
    reb.prim("cube", "Backpack", reb.mat_plain("Pack orange", (0.45, 0.12, 0.03), 0.7), (11.2, 7.3, 0.18), (0.55, 0.32, 0.36), rot=(0, 0.3, 0.7), bevel=0.06)
    reb.cloth("Spilled clothes", mat("denim"), (11.7, 7.0, 0.02), (0.6, 0.4), rot=(0, 0, 0.4), lumps=0.04, seed=3)
    reb.prim("cyl", "Water bottle", mat("steel"), (12.1, 7.5, 0.04), (0.08, 0.08, 0.24), rot=(math.pi / 2, 0, 1.0))
    reb.prim("cube", "Lone boot", mat("rubber"), (10.4, 8.6, 0.07), (0.3, 0.12, 0.14), rot=(0, 0, 2.1), bevel=0.03)
    kit.papers("Trail map", (11.0, 6.6, 0.0), spread=0.3, count=2, seed=1)

    # ---- OUT OF SERVICE, hanging from one chain at the queue's head.
    board = reb.prim("cube", "Service board", reb.mat_plain("Board white", (0.5, 0.48, 0.42), 0.8), (0, -0.25, -0.3), (0.9, 0.03, 0.45))
    kit.text("Board words", "OUT OF", mat("red paint"), (0, -0.27, -0.2), size=0.14, rot=(math.pi / 2, 0, math.pi))
    kit.text("Board words 2", "SERVICE", mat("red paint"), (0, -0.27, -0.38), size=0.14, rot=(math.pi / 2, 0, math.pi))
    hook = reb.prim("sphere", "Board hook", mat("iron"), (8.3, 6.5, 2.1), (0.04, 0.04, 0.04))
    kit.rod("Board beam", mat("rust"), (6.6, 6.5, 2.1), (10.0, 6.5, 2.1), 0.04)
    for p in [o for o in __import__("bpy").data.objects if o.name.startswith(("Service board", "Board words"))]:
        p.parent = hook
    kit.rod("Board chain", mat("iron"), (7.9, 6.5, 2.1), (7.9, 6.25, 1.6), 0.008, 4)
    hook.rotation_euler = (0, 0.5, 0)

    # ---- The ways out: the line track's gate west, the quarry trail east.
    for y in (6.0, 8.0):
        reb.wall(kit.rod("Gate post", mat("rust"), (X0 - 0.1, y, 0), (X0 - 0.1, y, 2.0), 0.05))
    gate = reb.prim("cube", "Line gate", reb.mat_surface("Chain link", [(0.0, (0.18, 0.18, 0.17)), (1.0, (0.3, 0.3, 0.28))], scale=60, rough=0.5, bump=0.8), (X0 + 0.55, 6.15, 0.95), (1.2, 0.03, 1.8), rot=(0, 0, 1.1))
    reb.prim("cube", "Gate sign", mat("white paint"), (X0 - 0.12, 8.3, 1.4), (0.03, 0.5, 0.35))
    kit.text("Gate sign words", "LINE TRACK", mat("red paint"), (X0 - 0.09, 8.3, 1.46), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.text("Gate sign words 2", "STAFF ONLY", mat("red paint"), (X0 - 0.09, 8.3, 1.36), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.path_strip("Line track", mat("dirt"), [(X0 + 0.5, 7.0), (-2.0, 7.2), (-8.0, 8.0)], height, width=0.7)
    kit.rod("Trail sign post", mat("dark wood"), (X1 + 0.3, 10.4, 0), (X1 + 0.3, 10.4, 1.7), 0.05)
    reb.prim("cube", "Trail sign", mat("dark wood"), (X1 + 0.3, 10.1, 1.5), (0.04, 0.8, 0.2))
    kit.text("Trail sign words", "QUARRY TRAIL >", mat("white paint"), (X1 + 0.27, 10.1, 1.5), size=0.09, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.path_strip("East trail", mat("dirt"), [(X1 - 0.5, 9.0)] + [(x, ledge_y(x)) for x in (18.4, 19.0, 20.4, 24.0, 30.0, 40.0)], height, width=0.6)
    # A bench by the booth, the bin kicked over, rubbish blown about, rain in the hollows.
    reb.wall(kit.table("Bench", reb.mat_wood("Bench slats", (0.2, 0.14, 0.08)), (11.6, 3.2, 0.0), size=(1.8, 0.45, 0.45)))
    reb.prim("cyl", "Bin", mat("green paint"), (10.3, 4.2, 0.25), (0.45, 0.45, 0.7), rot=(math.pi / 2, 0, 2.4), segments=16)
    kit.papers("Rubbish", (10.8, 4.8, 0.0), spread=1.2, count=10, seed=9)
    for i in range(5):
        kit.splat(f"Damp patch {i}", reb.mat_plain("Damp concrete", (0.09, 0.09, 0.085), 0.25), (rng.uniform(4, 15), rng.uniform(4, 11), 0.0), rng.uniform(0.3, 0.7), seed=70 + i, stretch=(1.4, 0.8))
    leaves_m = mat("dead needles")
    lv, lf = [], []
    for _ in range(600):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        if (x - X0) < 3 or (Y1 - y) < 2 or rng.random() < 0.3:
            reb.card(lv, lf, Vector((x, y, 0.004)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.06, 0.12, 0.0)
    reb.mesh_object("Needles on the slab", lv, lf, leaves_m)

    # ---- The mountain round it: spruces up the slope, grass in the cracks and the verge.
    def keep_out(x, y):
        return (X0 - 1.5 < x < X1 + 1.5 and Y0 - 1.5 < y < Y1 + 1.0) or y > Y1 + 1.0 or (x > X1 - 0.5 and y > ledge_y(x) - LEDGE_HALF - 1.2) or (3.0 < x < 6.5 and y < Y0) or (x < X0 and 6.0 < y < 8.6) or (x > X1 and 8.0 < y < 11.0) or any((x - cx) ** 2 + (y - cy) ** 2 < 9 for cx, cy in ((3.2, 0.8), (16.6, 12.6), (13.2, 6.2), (2.5, 4.0)))
    kit.forest(rng, height, keep_out, (-14, -12, 44, 16), count=75, ferns=20, needles=600)

    def verge(r):
        while True:
            x, y = r.uniform(X0 - 3, X1 + 3), r.uniform(Y0 - 3, Y1 + 0.5)
            if not (X0 + 0.2 < x < X1 - 0.2 and Y0 + 0.2 < y < Y1 - 0.2) and not (x > X1 + 0.3 and y > ledge_y(x) + LEDGE_HALF):
                return x, y
    grass = kit.meadow(rng, 1600, verge, height)
    cracks = kit.meadow(rng, 140, lambda r: (r.uniform(X0 + 1, X1 - 1), r.uniform(Y0 + 1, Y1 - 1)), height, mat("dead grass"))
    rv, rf = [], []
    for (x, y, r) in ((0.5, 6.0, 0.9), (18.6, 4.5, 0.8), (1.2, 12.2, 0.7), (18.4, 12.6, 0.6)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Rocks", rv, rf, mat("rock"))

    # ---- Light: the morning sun low in the east, the valley in mist below.
    kit.time_light("morning", sun_heading=110, sun_energy=5.0)
    kit.vista(rng, (9.0, Y1), (0.0, 1.0), below=-90.0)
    rope, rope_pivot = cliff_path(rng)

    anim = kit.Anim(16)
    anim.swing(hook, axis=0, degrees=7)
    anim.custom(lambda k: setattr(pivot, "rotation_euler", (math.radians(1.2) * math.sin(anim.phase(k)), 0, 0)))
    anim.bob(crows[0], height=0.05, speed=2)
    anim.sway(grass, amount=0.06)
    anim.flicker(glow, None, depth=0.35, dropouts=2)
    anim.swing(rope_pivot, axis=0, degrees=9)

    # ---- What the game needs.
    room.door("bridge", (3.0, Y0, 6.0, Y0 + 0.6), arrive=(4.6, 3.4), face=(0, 1))
    room.door("booth", (BOOTH_DOOR[0], by1, BOOTH_DOOR[1], by1 + 0.5), arrive=(14.55, 6.3), face=(0, 1))
    room.door("east-path", (X_END - 0.6, WALK[1][1], X_END, WALK[1][3]), arrive=(18.9, 9.7), face=(-1, 0))
    for (ax0, ay0, ax1, ay1) in WALK:
        room.void((ax0, Y0, ax1, ay0))      # the rock north of the ledge
        room.void((ax0, ay1, ax1, Y1))      # the drop into the gorge
    room.door("line-track", (X0, 6.0, X0 + 0.6, 8.0), arrive=(3.4, 7.0), face=(1, 0))
    room.door("car", (cx0 + 0.6, cy0 - 0.6, cx0 + 1.6, cy0), arrive=(8.3, 9.9), face=(0, -1), walk=False, touch=False)
    room.check((15.8, 10.6, X1, 12.0), "The smear ends at the rail. The crows are at something caught on it.\nA strip of plaid shirt.")
    room.check((cx0, cy0 - 0.7, cx1, cy0), "Car 4. The door has been forced from inside. The glass is smeared red.")
    room.spot("fit-cog", (wx0 + 0.6, wy0 + 0.4, wx1 - 0.4, wy1 - 1.2))  # day/events.ts says what she sees and does here
    room.check((10.6, 6.7, 12.4, 7.9), "A hiker's pack, split open. Clothes, a water bottle, a trail map.")
    room.check((8.5, Y0, 11.5, 3.2), "ARKLAY SKYWAY. UPPER STATION. ELEV 1840.")
    room.check((7.2, 5.8, 9.4, 6.8), "OUT OF SERVICE.")
    room.check((19.4, WALK[1][3] - 0.6, X_END - 0.6, WALK[1][3]), "A stake's been pulled out of the rock. The rope hangs down over the edge.\nHis cap. Scrape marks, right to the lip.")
    room.entry = "A gondola station. Down the mountain, into the valley.\nIf it ran."
    room.export(anim)


build()
