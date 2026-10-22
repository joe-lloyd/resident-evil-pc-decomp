"""The gondola's upper station, morning: ARKLAY SKYWAY, the top of the line.

What it tells: the last car came up before dawn with something in it. Its
door was forced from inside and the glass is smeared red. Whatever was in
it was dragged out across the platform: a broken smear, soaked into the
concrete, runs from the car door to the rail on the east side and stops at
what is caught on the rail. A hiker's pack lies split open where it was dropped,
one boot beside it. The drive is dead: under the wheel house the motor and
gearbox stand open with the cog sheared and a spanner dropped in the oil,
an OUT OF SERVICE board hangs by one chain from the queue's rope, and the
operator's booth door stands open. The station looks out over the valley,
where the cable runs down into the mist, over the RE0 overcast and the
ranges (kit.backdrop, kit.overcast_sky).

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

Moving: the board on its chain, the car rocking on the cable, the rope
and its stake over the drop, all of it slight. The grass stands still.

State "gondola-runs" (Hal's key in the booth, day/events.ts): the new cog
in, the bullwheel turning, the drive's lamp lit on the wheel house, and the
car lit inside and rocking on the running cable. It happens out here while
she is in the booth, so it is the room's loop, not a change played once.
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


UP_SEED, UP_LEDGES = 2.0, (1.1, 2.4, 3.9, 5.2, 6.2)


def cliff_up(x):
    """How tall the cliff over the ledge stands at x: rising out of the
    platform's corner to its full height."""
    t = min(1.0, max(0.0, (x - X1 - 0.2) / 3.0))
    return 0.6 + 6.3 * t * t * (3 - 2 * t)


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
            return -min(88.0, e * 2.4 + e * e * 0.4) + 0.4 * n * min(1.0, e)
        # North: hidden behind the cliff (cliff_up) until its top, then the
        # mountain going on up from there.
        e = -d - LEDGE_HALF
        top = cliff_up(x)
        if e < kit.cliff_relief(x, top, UP_SEED, UP_LEDGES) - 0.15:
            return -0.4
        return top - 0.2 + 0.35 * (e - 3.0) + 0.5 * n
    h = 0.3 * n
    if y > Y1 + 0.4:
        e = y - Y1 - 0.4
        h -= min(120.0, e * 2.4 + e * e * 0.4)       # the fall under the platform's rock face
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


def gondola(car_red, glass, dark):
    """Car 4: a cabin for six in pressed steel, red below a band of windows
    all round, corner pillars and a domed roof; a rubbing rail round its
    waist; the hanger, an arm that rises off the roof and bends over to the
    grip on the cable. Its door, north, slides and has been forced half
    open from inside. Returns its parts, round the grip."""
    import bpy
    cx0, cx1, cy0, cy1 = CAR
    mx, my = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    w, d = cx1 - cx0, cy1 - cy0
    parts = []
    # The body: a lower shell tapered in to its floor, the window band, the roof.
    lower = reb.prim("cube", "Car body", car_red, (mx, my, 0.82), (w, d, 1.0), bevel=0.18)
    lower.scale = (1.0, 1.0, 1.0)
    taper = lower.modifiers.new("Taper", "SIMPLE_DEFORM")
    taper.deform_method = "TAPER"
    taper.deform_axis = "Z"
    taper.factor = 0.18
    parts.append(lower)
    parts.append(reb.prim("cube", "Car skirt", dark, (mx, my, 0.3), (w - 0.35, d - 0.35, 0.06), bevel=0.03))
    parts.append(reb.prim("cube", "Car rubbing rail", kit.mat("steel"), (mx, my, 1.0), (w + 0.06, d + 0.06, 0.07), bevel=0.03))
    # Windows: dark glass all round, with the pillars and mullions over it.
    parts.append(reb.prim("cube", "Car windows", glass, (mx, my, 1.72), (w - 0.06, d - 0.06, 0.82), bevel=0.12))
    parts.append(reb.prim("cube", "Car inside", reb.mat_plain("Car dark", (0.02, 0.012, 0.01), 0.9), (mx, my, 1.5), (w - 0.2, d - 0.2, 1.4)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(reb.prim("cube", "Car pillar", car_red, (mx + sx * (w / 2 - 0.1), my + sy * (d / 2 - 0.1), 1.72), (0.16, 0.16, 0.86), bevel=0.05))
    for x in (mx - w / 6, mx + w / 6):
        for sy in (-1, 1):
            parts.append(reb.prim("cube", "Car mullion", car_red, (x, my + sy * (d / 2 - 0.02), 1.72), (0.06, 0.05, 0.84)))
    parts.append(reb.prim("cube", "Car mullion", car_red, (mx + w / 2 - 0.02, my, 1.72), (0.05, 0.06, 0.84)))
    parts.append(reb.prim("cube", "Car mullion", car_red, (mx - w / 2 + 0.02, my, 1.72), (0.05, 0.06, 0.84)))
    parts.append(reb.prim("cube", "Car window sill", car_red, (mx, my, 1.3), (w + 0.02, d + 0.02, 0.06), bevel=0.02))
    parts.append(reb.prim("cube", "Car eave", car_red, (mx, my, 2.15), (w + 0.04, d + 0.04, 0.08), bevel=0.03))
    roof = reb.prim("sphere", "Car roof", car_red, (mx, my, 2.17), (w / 2 + 0.02, d / 2 + 0.02, 0.32), segments=24)
    cut = roof.modifiers.new("Flat", "BOOLEAN")
    plane = reb.prim("cube", "Roof cutter", None, (mx, my, 1.67), (w + 1, d + 1, 1.0))
    cut.operation = "DIFFERENCE"
    cut.object = plane
    parts.append(roof)
    parts.append(reb.prim("cyl", "Roof vent", kit.mat("steel"), (mx - 0.5, my, 2.45), (0.3, 0.3, 0.1), segments=16))
    # The door, north: its track over the opening, the door slid half open and bent out at its foot.
    parts.append(reb.prim("cube", "Car doorway", reb.mat_plain("Car dark", (0.02, 0.012, 0.01), 0.9), (mx - 0.35, cy0 - 0.005, 1.15), (0.85, 0.02, 1.75)))
    parts.append(reb.prim("cube", "Door track", kit.mat("steel"), (mx, cy0 - 0.08, 2.08), (w - 0.2, 0.05, 0.05)))
    parts.append(reb.prim("cube", "Car door, forced", car_red, (mx + 0.35, cy0 - 0.09, 1.15), (0.85, 0.05, 1.8), rot=(0.06, 0, -0.05), bevel=0.02))
    parts.append(reb.prim("cube", "Car door glass", glass, (mx + 0.35, cy0 - 0.12, 1.7), (0.65, 0.01, 0.6), rot=(0.06, 0, -0.05)))
    parts.append(reb.prim("cube", "Door handle", kit.mat("steel"), (mx + 0.0, cy0 - 0.13, 1.15), (0.04, 0.03, 0.2)))
    # The hanger: up off the roof, out over the side, and over to the grip.
    gx, gz = mx, 3.45
    arm = [(mx, my, 2.4), (mx, my, 2.65), (mx + 0.55, my, 2.85), (mx + 0.75, my, 3.15), (mx + 0.5, my, 3.4), (gx + 0.12, my, gz - 0.02)]
    parts.append(kit.tube("Car hanger", kit.mat("iron"), arm, 0.06, 10))
    parts.append(reb.prim("cube", "Hanger plate", kit.mat("iron"), (mx, my, 2.43), (0.5, 0.5, 0.05)))
    parts.append(reb.prim("cube", "Car grip", kit.mat("iron"), (gx, my, gz), (0.32, 0.55, 0.26), bevel=0.04))
    for dy in (-0.2, 0.2):
        parts.append(reb.prim("cyl", "Grip wheel", kit.mat("steel"), (gx, my + dy, gz + 0.1), (0.2, 0.2, 0.06), rot=(0, math.pi / 2, 0), segments=14))
    for i in range(4):
        kit.splat(f"Smear on the glass {i}", kit.mat("blood"), (cx0 + 0.45 + i * 0.5, cy0 - 0.035, 1.7 + (i % 2) * 0.2 - 0.1), 0.15, rot=(math.pi / 2, 0, 0), seed=60 + i, stretch=(0.6, 1.5))
        parts.append(bpy.data.objects[f"Smear on the glass {i}"])
    parts.append(kit.text("Car number", "4", kit.mat("white paint"), (cx1 - 0.4, cy0 - 0.03, 0.75), size=0.3, rot=(math.pi / 2, 0, math.pi)))
    plane.hide_render = True
    return parts


def wheel_house_detail(wx0, wx1, wy0, wy1, rng):
    """What drives the line: the motor on its bed beside the gearbox, its
    fins and coupling, the control cabinet with its dead lamps, the frame
    braced across under the roof, the guide sheaves where the cable leaves,
    grease cans, a cable drum, the guard rail round it."""
    cx = (wx0 + wx1) / 2
    cy = (wy0 + wy1) / 2 + 0.6
    green = kit.mat("green paint")
    reb.prim("cube", "Machine bed", kit.mat("concrete"), (cx, cy, 0.08), (2.6, 2.0, 0.16), bevel=0.02)
    motor = reb.prim("cyl", "Drive motor", green, (cx - 1.25, cy + 0.2, 0.55), (0.7, 0.7, 1.1), rot=(0, math.pi / 2, 0), segments=24)
    reb.mask(reb.wall(motor))
    for i in range(9):
        x = cx - 1.7 + i * 0.11
        reb.prim("cyl", "Motor fin", green, (x, cy + 0.2, 0.55), (0.8, 0.8, 0.03), rot=(0, math.pi / 2, 0), segments=24)
    reb.prim("cube", "Motor foot", green, (cx - 1.25, cy + 0.2, 0.2), (0.9, 0.7, 0.12))
    reb.prim("cube", "Motor terminal box", green, (cx - 1.25, cy - 0.2, 0.92), (0.3, 0.2, 0.22), bevel=0.02)
    kit.rod("Motor cable", kit.mat("black"), (cx - 1.25, cy - 0.3, 0.95), (cx - 1.25, wy0 - 0.1, 2.0), 0.03, 6)
    kit.rod("Coupling", kit.mat("steel"), (cx - 0.7, cy + 0.2, 0.55), (cx - 0.78, cy + 0.2, 0.55), 0.16, 16)
    kit.rod("Drive shaft", kit.mat("steel"), (cx - 0.7, cy + 0.2, 0.55), (cx - 0.8, cy + 0.2, 0.55), 0.06, 10)
    for dx in (-0.6, 0.6):
        for dy in (-0.45, 0.45):
            reb.prim("cyl", "Gearbox bolt", kit.mat("iron"), (cx + dx, cy + dy, 1.11), (0.05, 0.05, 0.03), segments=6)
    reb.prim("cube", "Gearbox inspection rim", kit.mat("iron"), (cx, cy, 1.11), (0.9, 0.7, 0.03))
    # The control cabinet on the back post, its lamps dead, a cable down.
    cab = reb.prim("cube", "Control cabinet", kit.mat("green paint"), (wx0 + 0.25, wy1 - 0.6, 1.3), (0.35, 0.8, 1.1), bevel=0.02)
    reb.mask(cab)
    for i, rgb in enumerate(((0.25, 0.04, 0.02), (0.25, 0.2, 0.02), (0.04, 0.2, 0.06))):
        reb.prim("cyl", "Cabinet lamp", reb.mat_plain(f"Dead lamp {i}", rgb, 0.3), (wx0 + 0.43, wy1 - 0.85 + i * 0.25, 1.6), (0.08, 0.08, 0.04), rot=(0, math.pi / 2, 0), segments=10)
    reb.prim("cyl", "Stop button", kit.mat("red paint"), (wx0 + 0.43, wy1 - 0.6, 1.25), (0.12, 0.12, 0.05), rot=(0, math.pi / 2, 0), segments=12)
    reb.prim("cube", "Cabinet handle", kit.mat("steel"), (wx0 + 0.44, wy1 - 0.25, 1.3), (0.03, 0.03, 0.18))
    # The frame: beams across the posts under the roof, braces at the corners.
    for y in (wy0, wy1):
        kit.rod("Frame beam", kit.mat("rust"), (wx0, y, 4.15), (wx1, y, 4.15), 0.07, 6)
    for x in (wx0, wx1):
        kit.rod("Frame beam", kit.mat("rust"), (x, wy0, 4.15), (x, wy1, 4.15), 0.07, 6)
        for y, sgn in ((wy0, 1), (wy1, -1)):
            kit.rod("Corner brace", kit.mat("rust"), (x, y, 3.3), (x, y + sgn * 0.9, 4.15), 0.04, 6)
    kit.rod("Wheel frame leg", kit.mat("rust"), (cx - 0.9, cy, 1.1), (cx, cy, 3.1), 0.07, 8)
    kit.rod("Wheel frame leg", kit.mat("rust"), (cx + 0.9, cy, 1.1), (cx, cy, 3.1), 0.07, 8)
    # Guide sheaves where the cable leaves for the car.
    for dx in (1.55, -1.55):
        reb.prim("cyl", "Guide sheave", kit.mat("steel"), (cx + dx, wy1 + 0.1, 3.2), (0.35, 0.35, 0.08), rot=(math.pi / 2, 0, 0), segments=18)
        kit.rod("Sheave bracket", kit.mat("rust"), (cx + dx, wy1 + 0.1, 3.0), (cx + dx, wy1, 4.15), 0.04, 6)
    # A cable drum on its side and grease cans by the bed.
    reb.prim("cyl", "Cable drum", kit.mat("planks"), (wx1 - 0.4, wy1 - 0.5, 0.45), (0.9, 0.9, 0.5), rot=(math.pi / 2, 0, 0), segments=18)
    reb.prim("cyl", "Cable on the drum", kit.mat("iron"), (wx1 - 0.4, wy1 - 0.5, 0.45), (0.65, 0.65, 0.45), rot=(math.pi / 2, 0, 0), segments=18)
    for i in range(3):
        reb.prim("cyl", "Grease can", reb.mat_plain("Grease can", (0.3, 0.2, 0.04), 0.5), (wx0 + 1.0 + i * 0.3, wy0 + 0.35, 0.18), (0.22, 0.22, 0.34), segments=12)


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
    oil = reb.mat_plain("Oil", (0.025, 0.022, 0.018), 0.55)
    panel = kit.boards("Booth boards", (0.2, 0.22, 0.17), width=0.16, grime=0.7)

    # ---- Ground: the slab, the mountain round it in grassed earth, rock
    # where it is steep; the cliff over the ledge and the drop under it in
    # granite with moss on the ledges.
    side = steep(mat("grassed earth"), "Grassed earth, steep")
    nx0, ny0, nx1, ny1 = NEAR
    reb.terrain("Mountainside near", side, (nx0, nx1), (ny0, ny1), height, step=0.25)
    reb.terrain("Mountainside", side, (-30, 70), (-30, 60), lambda x, y: height(x, y) - (3.0 if nx0 + 1 < x < nx1 - 1 and ny0 + 1 < y < ny1 - 1 else 0.0), step=0.5)
    xs = [17.2 + 0.2 * i for i in range(141)]
    _, up_ledges = kit.cliff("Cliff over the ledge", xs, lambda x: (ledge_y(x) - LEDGE_HALF - 0.05, -0.2), cliff_up, 1, rise=True, m=mat("granite"), ledge_m=mat("moss"), seed=UP_SEED, ledges=UP_LEDGES)
    _, down_ledges = kit.cliff("Drop under the ledge", xs, lambda x: (ledge_y(x) + LEDGE_HALF + 0.05, 0.02), 18.0, 1, m=mat("granite"), ledge_m=mat("moss"), seed=5.0)
    _, under_ledges = kit.cliff("Drop under the platform", [-14.0 + 0.25 * i for i in range(126)], lambda x: (Y1 + 0.58, -1.2), 16.0, 1, m=mat("granite"), ledge_m=mat("moss"), seed=8.0)
    kit.ledge_plants(rng, up_ledges + down_ledges + under_ledges, tufts=2400, ferns=160)
    # Granite standing out of the drop under the ledge.
    cv, cf = [], []
    for x in (22.5, 28.5, 36.0):
        y = ledge_y(x)
        kit.crag(rng, cv, cf, (x + 1.2, y + LEDGE_HALF + 2.4, -7.5), (1.6, 1.3, 3.2), floor=-0.9)
    reb.mesh_object("Gorge crags", cv, cf, mat("granite"), smooth=False)
    reb.prim("cube", "Slab edge east", mat("concrete"), (X1 + 0.32, (10.4 + Y1 + 0.5) / 2, -1.2), (0.3, Y1 + 0.5 - 10.4, 2.4))
    reb.prim("cube", "Platform slab", concrete, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.15), (X1 - X0 + 0.6, Y1 - Y0 + 0.8, 0.3))
    reb.prim("cube", "Slab edge", mat("concrete"), ((X0 + X1) / 2, Y1 + 0.42, -1.2), (X1 - X0 + 0.6, 0.3, 2.4))
    kit.cracks("Cracks", mat("black"), (X0, Y0, X1, Y1), count=16, seed=1)
    # The trail in from the bridge, down the mountain to the slab's edge,
    # its dirt trodden out over the concrete where it meets it.
    on_trail_in = kit.dirt_path("Trail in", [(7.0, -40.0), (6.2, -24.0), (5.0, -12.0), (4.5, -5.0), (4.5, -1.0), (4.6, 1.6), (4.65, 2.5)], height, width=1.4)
    kit.splat("Dirt trodden onto the slab", mat("trodden dirt"), (4.6, 2.5, 0.003), 0.45, lumps=0.6, seed=31, stretch=(1.0, 0.6))

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
    c = Vector(((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 3.1))
    spokes = [kit.rod("Spoke", mat("rust"), c, c + Vector((math.cos(math.pi * i / 3) * 1.55, math.sin(math.pi * i / 3) * 1.55, 0)), 0.05) for i in range(6)]
    # Yellow marks round the rim's edge, so the wheel is seen to turn from
    # the platform, edge on as it is. It turns as one.
    for i in range(12):
        a = math.pi * i / 6
        spokes.append(reb.prim("cube", "Rim mark", mat("yellow paint"), c + Vector((math.cos(a) * 1.61, math.sin(a) * 1.61, 0)), (0.03, 0.42, 0.2), rot=(0, 0, a)))
    turning = kit.join("Bullwheel", [wheel] + spokes, origin=tuple(c))
    # The drive's lamp on the wheel house's post, lit once it runs.
    drive_lamp = reb.prim("cube", "Drive lamp", reb.mat_emit("Drive lamp", (1.0, 0.55, 0.1), 25), (wx1 + 0.1, wy0, 2.6), (0.22, 0.16, 0.26))
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
    # The new cog's teeth where the old one sheared, once she has fitted it.
    new_teeth = []
    for i in range(5, 9):
        a = 2 * math.pi * i / 18
        c = Vector(((wx0 + wx1) / 2, (wy0 + wy1) / 2 + 0.6, 1.15))
        new_teeth.append(reb.prim("cube", "New cog tooth", mat("steel"), c + Vector((math.cos(a) * 0.38, math.sin(a) * 0.38, 0)), (0.08, 0.05, 0.12), rot=(0, 0, a)))
    for i in range(3):
        reb.prim("cube", "Broken tooth", mat("steel"), ((wx0 + wx1) / 2 + 0.9 + i * 0.2, (wy0 + wy1) / 2 + 0.9, 0.02), (0.08, 0.05, 0.03), rot=(0, 0, rng.uniform(0, 3)))
    kit.splat("Oil under the gearbox", oil, ((wx0 + wx1) / 2 + 0.6, (wy0 + wy1) / 2 + 0.3, 0.0), 0.7, seed=4, stretch=(1.4, 1.0))
    reb.prim("cube", "Dropped spanner", mat("steel"), ((wx0 + wx1) / 2 + 0.8, (wy0 + wy1) / 2 + 0.1, 0.01), (0.35, 0.04, 0.015), rot=(0, 0, 0.6))
    kit.drum("Grease drum", mat("rust"), (wx0 + 0.5, wy0 + 0.5, 0.0))
    kit.drum("Drum on its side", mat("rust"), (wx0 + 0.7, wy0 + 1.5, 0.0), tipped=True, rot=0.4)
    wheel_house_detail(wx0, wx1, wy0, wy1, rng)
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
    car_parts = gondola(car_red, reb.mat_plain("Car glass", (0.03, 0.04, 0.045), 0.12), mat("black"))
    pivot = reb.prim("sphere", "Car pivot", mat("iron"), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 3.45), (0.05, 0.05, 0.05))
    for p in car_parts:
        p.parent = pivot
        p.matrix_parent_inverse = pivot.matrix_world.inverted()
    reb.wall(reb.prim("cube", "Car footprint", None, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.5), (cx1 - cx0, cy1 - cy0, 1.0))).hide_render = True

    # ---- What was dragged from it: a smear broken where it was lifted and
    # dropped, soaked into the concrete, to the east rail.
    for i, leg in enumerate(([(8.1, 10.8), (8.9, 10.3), (9.8, 10.0)], [(10.6, 9.75), (11.7, 9.6), (12.4, 9.75)], [(13.6, 10.0), (14.6, 10.3), (15.3, 10.65)], [(15.9, 10.9), (16.6, 11.2)])):
        kit.drag_trail(f"Drag smear {i}", mat("blood"), leg, width=0.42 - 0.04 * i, seed=7 + i, z=0.0)
    for i, (x, y) in enumerate(((10.2, 9.95), (13.0, 9.7), (13.2, 10.05), (15.6, 10.8))):
        kit.splat(f"Drip {i}", mat("blood"), (x, y, 0.002), 0.06, seed=40 + i, points=10)
    kit.splat("Pool at the rail", mat("blood"), (16.7, 11.3, 0.0), 0.32, seed=9, stretch=(1.1, 1.4))
    reb.cloth("Rag of shirt on the rail", mat("flannel"), (17.12, 11.2, 0.75), (0.05, 0.45), rot=(0, math.pi / 2, 0), cuts=8, lumps=0.05, seed=2)
    # The hiker's pack, split, and a boot.
    reb.prim("cube", "Backpack", reb.mat_plain("Pack orange", (0.45, 0.12, 0.03), 0.7), (11.2, 7.3, 0.18), (0.55, 0.32, 0.36), rot=(0, 0.3, 0.7), bevel=0.06)
    reb.cloth("Spilled clothes", mat("denim"), (11.7, 7.0, 0.02), (0.6, 0.4), rot=(0, 0, 0.4), lumps=0.04, seed=3)
    reb.prim("cyl", "Water bottle", mat("steel"), (12.1, 7.5, 0.04), (0.08, 0.08, 0.24), rot=(math.pi / 2, 0, 1.0))
    reb.prim("cube", "Lone boot", mat("rubber"), (10.4, 8.6, 0.07), (0.3, 0.12, 0.14), rot=(0, 0, 2.1), bevel=0.03)
    kit.papers("Trail map", (11.0, 6.6, 0.0), spread=0.3, count=2, seed=1)

    # ---- OUT OF SERVICE, hung across the queue's head on a chain between
    # its two front posts, slipped down at one end.
    kit.rod("Queue head chain", mat("iron"), (7.0, 6.5, 0.92), (8.3, 6.5, 0.72), 0.01, 4)
    kit.rod("Queue head chain", mat("iron"), (8.3, 6.5, 0.72), (9.6, 6.5, 0.92), 0.01, 4)
    board = reb.prim("cube", "Service board", reb.mat_plain("Board white", (0.5, 0.48, 0.42), 0.8), (0, -0.03, -0.26), (0.9, 0.03, 0.42))
    kit.text("Board words", "OUT OF", mat("red paint"), (0, -0.05, -0.17), size=0.14, rot=(math.pi / 2, 0, math.pi))
    kit.text("Board words 2", "SERVICE", mat("red paint"), (0, -0.05, -0.35), size=0.14, rot=(math.pi / 2, 0, math.pi))
    hook = reb.prim("sphere", "Board hook", mat("iron"), (8.3, 6.5, 0.72), (0.03, 0.03, 0.03))
    for p in [o for o in __import__("bpy").data.objects if o.name.startswith(("Service board", "Board words"))]:
        p.parent = hook
    hook.rotation_euler = (0, 0.18, 0)

    # ---- The ways out: the line track's gate west, the quarry trail east.
    for y in (6.0, 8.0):
        reb.wall(kit.rod("Gate post", mat("rust"), (X0 - 0.1, y, 0), (X0 - 0.1, y, 2.0), 0.05))
    gate = reb.prim("cube", "Line gate", reb.mat_surface("Chain link", [(0.0, (0.18, 0.18, 0.17)), (1.0, (0.3, 0.3, 0.28))], scale=60, rough=0.5, bump=0.8), (X0 + 0.55, 6.15, 0.95), (1.2, 0.03, 1.8), rot=(0, 0, 1.1))
    reb.prim("cube", "Gate sign", mat("white paint"), (X0 - 0.12, 8.3, 1.4), (0.03, 0.5, 0.35))
    kit.text("Gate sign words", "LINE TRACK", mat("red paint"), (X0 - 0.09, 8.3, 1.46), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.text("Gate sign words 2", "STAFF ONLY", mat("red paint"), (X0 - 0.09, 8.3, 1.36), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    on_line = kit.dirt_path("Line track", [(X0 - 0.1, 7.0), (-2.0, 7.2), (-8.0, 8.0), (-16.0, 9.5), (-28.0, 10.0)], height, width=1.1, taper=0.4)
    kit.rod("Trail sign post", mat("dark wood"), (X1 + 0.3, 10.4, 0), (X1 + 0.3, 10.4, 1.7), 0.05)
    reb.prim("cube", "Trail sign", mat("dark wood"), (X1 + 0.3, 10.1, 1.5), (0.04, 0.8, 0.2))
    kit.text("Trail sign words", "QUARRY TRAIL >", mat("white paint"), (X1 + 0.27, 10.1, 1.5), size=0.09, rot=(math.pi / 2, 0, -math.pi / 2))
    on_east = kit.dirt_path("East trail", [(X1 + 0.15, 9.0)] + [(x, ledge_y(x)) for x in (18.4, 19.0, 20.4, 24.0, 30.0, 38.0, 46.0, 56.0)], height, width=1.5, taper=0.5)
    kit.splat("Dirt trodden onto the slab east", mat("trodden dirt"), (X1 - 0.05, 9.0, 0.003), 0.38, lumps=0.6, seed=32, stretch=(0.6, 1.2))
    # A bench by the booth, the bin kicked over, rubbish blown about.
    reb.wall(kit.table("Bench", reb.mat_wood("Bench slats", (0.2, 0.14, 0.08)), (11.6, 3.2, 0.0), size=(1.8, 0.45, 0.45)))
    reb.prim("cyl", "Bin", mat("green paint"), (10.3, 4.2, 0.25), (0.45, 0.45, 0.7), rot=(math.pi / 2, 0, 2.4), segments=16)
    kit.papers("Rubbish", (10.8, 4.8, 0.0), spread=1.2, count=10, seed=9)
    leaves_m = mat("dead needles")
    lv, lf = [], []
    for _ in range(600):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        if (x - X0) < 3 or (Y1 - y) < 2 or rng.random() < 0.3:
            reb.card(lv, lf, Vector((x, y, 0.004)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.06, 0.12, 0.0)
    reb.mesh_object("Needles on the slab", lv, lf, leaves_m)

    # ---- The mountain round it: spruces close and dense up the slope and
    # down the fall below the platform, grass over all but the paths.
    def on_path(x, y, margin=0.0):
        return on_trail_in(x, y, margin) or on_east(x, y, margin) or on_line(x, y, margin)

    eyes = [(3.2, 0.8), (16.6, 12.6), (13.2, 6.2), (2.5, 4.0), (15.4, 12.6), (23.2, 9.4)]

    def keep_out(x, y):
        return ((X0 - 1.5 < x < X1 + 1.5 and Y0 - 1.5 < y < Y1 + 1.6)
                or (x > X1 - 0.5 and ledge_y(x) - LEDGE_HALF - 1.4 < y < ledge_y(x) + LEDGE_HALF + 3.0)
                or (y > Y1 + 1.6 and height(x, y) > -6.0)        # the fall below the rail: trees only well down it
                or on_path(x, y, 1.4) or any((x - cx) ** 2 + (y - cy) ** 2 < 16 for cx, cy in eyes))
    kit.forest(rng, height, keep_out, (-30, -30, 60, 16), count=330, spacing=1.6, tall=(14, 22), ferns=80, needles=1500)
    kit.forest(rng, height, keep_out, (-20, 13, 60, 55), count=260, spacing=2.0, tall=(15, 24), ferns=0, needles=0)

    def no_grass(x, y):
        return ((X0 - 0.3 < x < X1 + 0.3 and Y0 - 0.3 < y < Y1 + 0.5) or on_path(x, y)
                or (x > X1 + 0.3 and abs(y - ledge_y(x)) > LEDGE_HALF + 0.05))
    kit.grass_ground(rng, (-8, -8, 30, 16), height, keep_out=no_grass, per_m2=28)
    kit.grass_ground(rng, (-24, -24, 50, 40), height, keep_out=lambda x, y: no_grass(x, y) or (-8 < x < 30 and -8 < y < 16) or height(x, y) < -30, per_m2=5)
    kit.meadow(rng, 140, lambda r: (r.uniform(X0 + 1, X1 - 1), r.uniform(Y0 + 1, Y1 - 1)), height, mat("dead grass"))
    kit.rocks("Rocks", rng, [(0.5, 6.0, 0.9), (1.2, 12.2, 0.7), (18.4, 12.9, 0.6), (-1.5, 2.5, 0.8)], height, mat("granite"))

    # ---- Light: the morning sun low in the east, the valley in mist below.
    kit.time_light("morning", sun_heading=110, sun_energy=5.0)
    kit.overcast_sky(glow=(0.9, 0.4))

    def far_land(x, y, z):
        r = math.hypot(x - 10.0, y - 8.0)
        w = max(0.0, min(1.0, (240.0 - r) / 170.0))
        return z + (height(x, y) - z) * w * w * (3 - 2 * w)
    # The far side of the valley the line runs down into: long rolling
    # ranges, wooded to their crests, nearer and higher than the kit's own,
    # for a station on a summit.
    ranges = [
        {"at": 650, "depth": 380, "rise": 4.5, "roll": 1.6},
        {"at": 1500, "depth": 800, "rise": 4.0, "roll": 1.4},
        {"at": 3200, "depth": 1500, "rise": 4.2, "roll": 1.2},
        {"at": 6500, "depth": 2600, "rise": 4.6, "roll": 1.0},
        {"at": 12000, "depth": 3200, "rise": 5.0, "roll": 0.8},
    ]
    kit.backdrop((10.0, 8.0, 3.0), spread=360, ranges=ranges, below=-190.0, near=50.0, forest_to=2200.0, trees=130000,
                 keep_out=lambda x, y: math.hypot(x - 10.0, y - 8.0) < 50, shape=far_land, mist=22.0, rng=random.Random(5))
    rope, rope_pivot = cliff_path(rng)

    anim = kit.Anim(16)
    anim.swing(hook, axis=0, degrees=2)
    anim.custom(lambda k: setattr(pivot, "rotation_euler", (math.radians(0.6) * math.sin(anim.phase(k)), 0, 0)))
    anim.flicker(glow, None, depth=0.35, dropouts=2)
    anim.swing(rope_pivot, axis=0, degrees=3)

    lit_inside = [ob.active_material for ob in car_parts if ob.name.startswith(("Car inside", "Car doorway"))]

    def running(on):
        """The gondola running (Hal's key, in the booth): the new cog in, the
        drive's lamp and the car's lit."""
        drive_lamp.hide_render = not on
        for ob in new_teeth:
            ob.hide_render = not on
        for m in lit_inside:
            bsdf = m.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.62, 0.3, 1)
            bsdf.inputs["Emission Strength"].default_value = 0.3 if on else 0.0

    def run_loop(k):
        """As it runs: the bullwheel a sixth of a turn round the loop, the car
        rocking on the moving cable."""
        turning.rotation_euler = (0, 0, math.pi / 3 * k / anim.frames)
        pivot.rotation_euler = (math.radians(3.0) * math.sin(anim.phase(k)), math.radians(1.0) * math.sin(anim.phase(k, 2)), 0)
    running(False)
    room.state("gondola-runs", running, loop=run_loop, cameras=[0, 2, 3])

    # ---- What the game needs.
    room.door("bridge", (3.0, Y0, 6.0, Y0 + 0.6), arrive=(4.6, 3.4), face=(0, 1))
    room.door("booth", (BOOTH_DOOR[0], by1, BOOTH_DOOR[1], by1 + 0.5), arrive=(14.55, 6.3), face=(0, 1))
    room.door("east-path", (X_END - 0.6, WALK[1][1], X_END, WALK[1][3]), arrive=(18.9, 9.7), face=(-1, 0))
    for (ax0, ay0, ax1, ay1) in WALK:
        room.void((ax0, Y0, ax1, ay0))      # the rock north of the ledge
        room.void((ax0, ay1, ax1, Y1))      # the drop into the gorge
    room.door("line-track", (X0, 6.0, X0 + 0.6, 8.0), arrive=(3.4, 7.0), face=(1, 0))
    room.door("car", (cx0 + 0.6, cy0 - 0.6, cx0 + 1.6, cy0), arrive=(8.3, 9.9), face=(0, -1), walk=False, touch=False)
    room.check((15.8, 10.6, X1, 12.0), "The smear ends at the rail. Something is caught on it.\nA strip of plaid shirt.")
    room.check((cx0, cy0 - 0.7, cx1, cy0), "Car 4. The door has been forced from inside. The glass is smeared red.")
    room.spot("fit-cog", (wx0 + 0.6, wy0 + 0.4, wx1 - 0.4, wy1 - 1.2))  # day/events.ts says what she sees and does here
    room.check((10.6, 6.7, 12.4, 7.9), "A hiker's pack, split open. Clothes, a water bottle, a trail map.")
    room.check((8.5, Y0, 11.5, 3.2), "ARKLAY SKYWAY. UPPER STATION. ELEV 1840.")
    room.check((7.2, 5.8, 9.4, 6.8), "OUT OF SERVICE.")
    room.check((19.4, WALK[1][3] - 0.6, X_END - 0.6, WALK[1][3]), "A stake's been pulled out of the rock. The rope hangs down over the edge.\nHis cap. Scrape marks, right to the lip.")
    room.export(anim)


build()
