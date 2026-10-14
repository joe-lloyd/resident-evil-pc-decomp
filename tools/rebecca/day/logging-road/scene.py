"""The logging road to Camp 4, through the spruces, at noon under cloud.

What it tells: a log truck was bringing a load down from the cut to the
camp's sawmill when its driver got sick at the wheel. He stopped where he
was, in the ruts, and got out: the driver's door hangs open, there is
blood on the bench seat and down the step, and his lunch went into the mud
when he fell out after it, the pail open, the thermos rolled away. He
coughed up blood by the front wheel. Then he walked on toward the camp,
dragging one foot: his prints go east in the mud. The battery is dying:
the left blinker still flashes and the wipers twitch now and then on the
dry glass. Back up the road someone from the camp nailed a QUARANTINE
notice to a spruce to turn people away. Someone has torn half of it down.
A player should work out that whatever was in the camp got out of it, and
that the camp is east.

Metres: she walks x 1-19, y 3-13. The road runs west to east through the
middle, its ruts at y 7.2 and 9.2. The truck stands in them facing east:
the trailer's tail and the log ends at x 4.0, the front bumper at x 16.6,
y 7.0-9.4; the driver's door is on the south side at x 13.0-14.3, open.
She gets round it on either verge. The road goes on west to the woods
(the west edge, y 6.4-10) and east to the camp gate (the east edge,
y 6.2-11). The notice is on the west face of a spruce at x 6.0, y 3.6, just off the north verge.

Moving: the blinker, the wipers twitching, the torn half of the notice in
the wind, flies on the seat and on the blood by the wheel, the grass.
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

X0, X1, Y0, Y1 = 1.0, 19.0, 4.4, 11.8
TY = 8.2                 # the road's (and the truck's) centre line
RUTS = (7.2, 9.2)
FX = 16.6                # the front bumper
CAB = (12.8, 14.6)       # the cab's back and front (x)
HW = 1.2                 # half the cab's width
DOOR = (13.0, 14.3)      # the driver's door, south side (x)
TAIL = 4.0               # the log ends at the back
NOTICE_TREE = (6.0, 3.6)
STANDING = [NOTICE_TREE, (11.4, 3.0), (8.6, 13.3), (15.8, 12.8)]


def height(x, y):
    """The road flat, the ruts sunk in it; the forest rolling up on both sides."""
    n = noise.noise(Vector((x * 0.22, y * 0.22, 9.0)))
    if Y0 - 0.5 < y < Y1 + 0.5:
        h = -0.04 + 0.03 * n
        for r in RUTS:
            d = abs(y - r)
            if d < 0.35:
                h -= 0.12 * (1 - (d / 0.35) ** 2)
        return h
    d = (Y0 - 0.5 - y) if y < Y0 else (y - Y1 - 0.5)
    return -0.04 + 0.5 * n + d * 0.22


def settle(ob, at, rot):
    """Bake a joined object's parts where they were built, then place it."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def spruce_crown(rng, base, h, verts, faces, lift):
    """An old spruce's needles from `lift` metres up, so cameras see under it."""
    up = Vector((0, 0, 1))
    radius = h * rng.uniform(0.17, 0.22)
    t0 = lift / h
    for _ in range(int(h * 300)):
        t = t0 + (1 - t0) * rng.uniform(0, 1.0) ** 0.8
        r = radius * (1.0 - t) ** 0.9 * rng.uniform(0.55, 1.05) + 0.05
        a = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(a), math.sin(a), 0))
        p = base + up * (h * t) + out * r * rng.uniform(0.3, 1.0)
        reb.card(verts, faces, p, out, up, rng.uniform(0.1, 0.2), rng.uniform(0.25, 0.5) * (0.6 + 0.4 * r), rng.uniform(0.3, 0.8))


def wheel(name, x, y, r=0.52, width=0.3):
    """A truck wheel: the tyre, its rim, the hub, axis along y."""
    tyre = reb.prim("cyl", name, mat("rubber"), (x, y, r), (2 * r, 2 * r, width), rot=(math.pi / 2, 0, 0), segments=20)
    reb.prim("cyl", f"{name} rim", mat("rust"), (x, y + (width / 2 + 0.005) * (1 if y > TY else -1), r), (r * 1.1, r * 1.1, 0.02), rot=(math.pi / 2, 0, 0), segments=16)
    reb.prim("cyl", f"{name} hub", mat("iron"), (x, y + (width / 2 + 0.03) * (1 if y > TY else -1), r), (0.22, 0.22, 0.06), rot=(math.pi / 2, 0, 0), segments=10)
    return tyre


def build():
    rng = random.Random(1974)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((1.4, 4.6, 3.6), (4.6, 11.4, 0.3), 200, "from the north-west corner where the road comes in from the woods: the log ends, the south verge")
    room.camera((1.6, 11.4, 3.6), (12.0, 8.6, 0.4), 200, "from the south-west, up the road: the length of the load, the south verge, the open door far off")
    room.camera((18.4, 11.4, 3.0), (10.0, 6.4, 0.8), 200, "from the south-east ahead of the truck: the grille, the blinker, the open door, the lunch in the mud")
    room.camera((13.4, 4.6, 3.4), (19.2, 9.8, 0.3), 200, "from the north verge, looking east: the cab's far side, the camp sign, the road on to the gate")
    room.camera((2.6, 5.0, 3.6), (14.0, 5.8, 0.3), 200, "from the north-west, along the north verge: the notice on its spruce, the length of the load, the cab")

    paint = reb.mat_surface("Truck paint", [(0.0, (0.28, 0.18, 0.03)), (0.65, (0.4, 0.28, 0.05)), (0.85, (0.3, 0.2, 0.05)), (1.0, (0.18, 0.08, 0.03))], scale=3, rough=0.5, bump=0.15)
    chrome = reb.mat_metal("Dull chrome", (0.5, 0.5, 0.48), 0.25)
    glass = reb.mat_glass("Cab glass", (0.45, 0.5, 0.5))
    dark = reb.mat_plain("Cab dark", (0.015, 0.014, 0.012), 0.9)
    seat_m = reb.mat_surface("Seat vinyl", [(0.0, (0.06, 0.03, 0.02)), (1.0, (0.12, 0.06, 0.035))], scale=10, rough=0.4, bump=0.2)
    road_m = reb.mat_surface("Road mud", [(0.0, (0.05, 0.035, 0.022)), (0.5, (0.1, 0.075, 0.048)), (0.8, (0.14, 0.11, 0.075)), (1.0, (0.09, 0.08, 0.05))], scale=1.6, rough=0.75, bump=0.6)
    rut_m = reb.mat_surface("Wet ruts", [(0.0, (0.015, 0.012, 0.008)), (0.6, (0.04, 0.03, 0.02)), (1.0, (0.08, 0.06, 0.04))], scale=4, rough=0.25, bump=0.5)
    floor_m = reb.mat_surface("Forest floor", [(0.0, (0.05, 0.035, 0.02)), (0.4, (0.11, 0.075, 0.045)), (0.65, (0.15, 0.1, 0.06)), (0.85, (0.07, 0.08, 0.035)), (1.0, (0.05, 0.075, 0.025))], scale=1.2, bump=0.5)
    puddle = reb.mat_plain("Puddle", (0.01, 0.012, 0.012), 0.04)

    # ---- Ground: the forest floor, the road bed, the ruts with water in them.
    reb.terrain("Forest floor", floor_m, (-16, 36), (-14, 30), height, step=0.4)
    reb.terrain("Far forest floor", floor_m, (-60, 80), (-60, 80), lambda x, y: height(x, y) - 0.4, step=4.0)
    kit.path_strip("Road bed", road_m, [(-14.0, TY + 0.3), (0.0, TY + 0.1), (10.0, TY), (20.0, TY - 0.1), (34.0, TY - 0.4)], height, width=1.9, wobble=0.12, lift=0.006)
    for r in RUTS:
        kit.path_strip("Rut", rut_m, [(-14.0, r + 0.3), (0.0, r + 0.1), (10.0, r), (20.0, r - 0.1), (34.0, r - 0.4)], height, width=0.26, wobble=0.15, lift=0.008)
    for i, (x, r, l) in enumerate(((2.4, RUTS[0], 1.6), (6.6, RUTS[1], 2.2), (17.6, RUTS[0], 1.8), (11.0, RUTS[0], 1.2), (18.6, RUTS[1], 1.4))):
        kit.splat(f"Puddle in the rut {i}", puddle, (x, r, height(x, r) + 0.02), 0.22, seed=50 + i, stretch=(l / 0.44, 1.0), lumps=0.15)
    # A ridge of grass between the ruts and along the verges.
    def verge(r_):
        while True:
            x, y = r_.uniform(X0 - 3, X1 + 3), r_.uniform(Y0 - 1, Y1 + 1)
            if abs(y - TY) < 0.35 or 2.2 < abs(y - TY) < 6:
                if not (TAIL - 0.3 < x < FX + 0.3 and abs(y - TY) < 1.4):
                    return x, y
    grass = kit.meadow(rng, 1400, verge, height)

    # ---- The truck: a 1970s conventional, mustard yellow, the hood long, a load of logs.
    # Frame and wheels.
    reb.prim("cube", "Truck frame", mat("iron"), ((5.0 + FX) / 2, TY, 0.85), (FX - 5.0 - 0.2, 0.9, 0.25))
    for x in (15.4,):
        for s in (-1, 1):
            wheel("Front wheel", x, TY + s * 1.05)
    for x in (11.6, 10.3, 5.6, 4.5):
        for s in (-1, 1):
            for d in (0.0, 0.32):
                wheel("Dual wheel", x, TY + s * (0.92 + d), r=0.5, width=0.28)
    # Hood, fenders, grille, lamps, bumper.
    reb.prim("cube", "Hood", paint, ((CAB[1] + FX - 0.25) / 2, TY, 1.6), (FX - 0.25 - CAB[1], 1.35, 1.1), bevel=0.08)
    for s in (-1, 1):
        reb.prim("cube", "Front fender", paint, (15.45, TY + s * 1.0, 1.15), (1.6, 0.42, 0.25), bevel=0.06)
        reb.prim("cube", "Fender skirt", paint, (15.45, TY + s * 1.0, 1.0), (1.6, 0.4, 0.06), rot=(s * 0.4, 0, 0))
    reb.prim("cube", "Grille", chrome, (FX - 0.22, TY, 1.55), (0.06, 1.15, 1.0))
    for k in range(9):
        reb.prim("cube", "Grille bar", dark, (FX - 0.19, TY - 0.5 + k * 0.125, 1.55), (0.02, 0.03, 0.9))
    for s in (-1, 1):
        reb.prim("cyl", "Headlight", reb.mat_glass("Headlamp", (0.7, 0.7, 0.62)), (FX - 0.2, TY + s * 0.82, 1.25), (0.22, 0.22, 0.06), rot=(0, math.pi / 2, 0), segments=14)
    reb.prim("cube", "Bumper", chrome, (FX, TY, 0.85), (0.18, 2.6, 0.26), bevel=0.03)
    kit.text("Hood name", "ARKLAY LUMBER", mat("white paint"), ((CAB[1] + FX) / 2, TY + 0.68, 1.75), size=0.18, rot=(math.pi / 2, 0, math.pi))
    kit.text("Hood name, other side", "ARKLAY LUMBER", mat("white paint"), ((CAB[1] + FX) / 2, TY - 0.68, 1.75), size=0.18)
    # The cab: a box with its windows, its roof lights, the exhaust stack, the mirrors.
    # Walls round the inside x CAB, y TY +- HW, 1.1 to 2.9 up: the door's hole on the south, windows cut.
    cab_walls = kit.walls(CAB[0] + 0.06, TY - HW + 0.06, CAB[1] - 0.06, TY + HW - 0.06, 1.74, paint, openings=[
        ("s", DOOR[0], DOOR[1], 0.05, 1.65),
        ("e", TY - 1.05, TY + 1.05, 1.05, 1.65),
        ("w", TY - 0.7, TY + 0.7, 1.12, 1.57),
        ("n", 13.1, 14.2, 1.0, 1.55),
    ], floor=dark, ceiling=paint, name="Cab wall")
    for ob in cab_walls:
        ob.location.z += 1.12
        reb.mask(ob)
    for s in (-1, 1):
        reb.prim("cube", "Windshield", glass, (CAB[1] + 0.005, TY + s * 0.56, 2.45), (0.02, 1.0, 0.6))
    reb.prim("cube", "Windshield post", paint, (CAB[1] + 0.01, TY, 2.45), (0.03, 0.08, 0.62))
    reb.prim("cube", "Back window", glass, (CAB[0] - 0.005, TY, 2.45), (0.02, 1.4, 0.45))
    reb.prim("cube", "Passenger window", glass, (13.65, TY - HW - 0.005, 2.4), (1.1, 0.02, 0.55))
    amber = reb.mat_emit("Roof lights", (1.0, 0.45, 0.05), 3)
    for k in range(5):
        reb.prim("cube", "Roof light", amber, (CAB[1] - 0.05, TY - 0.6 + k * 0.3, 2.93), (0.06, 0.12, 0.06))
    reb.prim("cyl", "Exhaust stack", chrome, (CAB[0] - 0.12, TY - HW + 0.1, 2.3), (0.14, 0.14, 2.9), segments=12)
    reb.prim("cyl", "Stack cap", mat("rust"), (CAB[0] - 0.12, TY - HW + 0.1, 3.78), (0.16, 0.16, 0.04), rot=(0, 0.5, 0), segments=12)
    for s in (-1, 1):
        kit.rod("Mirror arm", chrome, (CAB[1] - 0.1, TY + s * HW, 2.2), (CAB[1] + 0.1, TY + s * (HW + 0.35), 2.4), 0.015, 6)
        reb.prim("cube", "Mirror", chrome, (CAB[1] + 0.1, TY + s * (HW + 0.38), 2.55), (0.04, 0.18, 0.4))
    # Fuel tank and step under the door, both sides.
    for s in (-1, 1):
        reb.prim("cyl", "Fuel tank", chrome, (12.3, TY + s * 0.95, 0.85), (0.6, 0.6, 1.0), rot=(0, math.pi / 2, 0), segments=16)
        reb.prim("cube", "Step", mat("iron"), (13.65, TY + s * (HW + 0.05), 0.72), (0.5, 0.2, 0.04))
    # Inside: the bench seat, bloody; the wheel; the dash.
    reb.prim("cube", "Bench seat", seat_m, (13.2, TY, 1.55), (0.55, 2.1, 0.18))
    reb.prim("cube", "Seat back", seat_m, (12.92, TY, 1.95), (0.14, 2.1, 0.7), rot=(0, -0.15, 0))
    kit.splat("Blood on the seat", mat("blood"), (13.2, TY + 0.6, 1.645), 0.2, seed=61, stretch=(1.3, 1.0))
    kit.splat("Blood on the seat back", mat("old blood"), (12.995, TY + 0.55, 1.95), 0.16, rot=(0, math.pi / 2 - 0.15, 0), seed=62, stretch=(1.0, 1.6))
    reb.prim("cyl", "Steering wheel", mat("black"), (14.05, TY + 0.6, 2.0), (0.48, 0.48, 0.04), rot=(0, math.pi / 2 + 0.6, 0), segments=16)
    kit.rod("Steering column", mat("black"), (14.05, TY + 0.6, 2.0), (14.4, TY + 0.6, 1.6), 0.03)
    reb.prim("cube", "Dash", dark, (14.45, TY, 2.0), (0.25, 2.2, 0.3))
    dash_m = reb.mat_emit("Dash lamp", (1.0, 0.25, 0.05), 2)
    reb.prim("cube", "Dash warning lamp", dash_m, (14.33, TY + 0.4, 2.12), (0.01, 0.04, 0.03))
    # The driver's door, hanging open on its hinge at the front, his blood on it.
    hinge = reb.prim("cube", "Door hinge", mat("iron"), (DOOR[1], TY + HW + 0.02, 1.95), (0.04, 0.04, 1.4))
    door = reb.prim("cube", "Driver's door", paint, (-(DOOR[1] - DOOR[0]) / 2, 0.035, 0.0), (DOOR[1] - DOOR[0], 0.07, 1.6), bevel=0.03)
    win = reb.prim("cube", "Door window", glass, (-(DOOR[1] - DOOR[0]) / 2 - 0.05, 0.075, 0.45), (DOOR[1] - DOOR[0] - 0.25, 0.02, 0.55))
    scr = kit.scratches("Scratched inside of the door", mat("black"), (-(DOOR[1] - DOOR[0]) / 2, -0.005, 0.25), (0, -1), count=6, length=0.4, seed=63)
    hand = kit.splat("Hand on the door", mat("blood"), (-0.95, -0.006, -0.05), 0.07, rot=(math.pi / 2, 0, 0), seed=64)
    kit.text("Door name", "CAMP 4", mat("white paint"), (-(DOOR[1] - DOOR[0]) / 2, 0.075, -0.25), size=0.16, rot=(math.pi / 2, 0, math.pi))
    for p in (door, win, scr, hand, bpy.data.objects["Door name"]):
        p.parent = hinge
    hinge.rotation_euler = (0, 0, -1.25)
    kit.splat("Smear on the cab", mat("old blood"), (13.0, TY + HW + 0.01, 1.6), 0.12, rot=(math.pi / 2, 0, math.pi), seed=65, stretch=(0.8, 1.8))
    for k in range(4):
        kit.splat(f"Drops down the step {k}", mat("blood"), (13.6 + rng.uniform(-0.2, 0.2), TY + HW + 0.05, 0.745 + 0.0), 0.04, seed=66 + k)
    # The wipers, on pivots at the foot of each pane.
    wipers = []
    for s in (-1, 1):
        pv = reb.prim("sphere", "Wiper pivot", mat("black"), (CAB[1] + 0.03, TY + s * 0.56 - 0.3, 2.18), (0.04, 0.04, 0.04), segments=8)
        blade = reb.prim("cube", "Wiper blade", mat("black"), (0.0, 0.0, 0.25), (0.02, 0.025, 0.5))
        blade.parent = pv
        pv.rotation_euler = (-1.2, 0, 0)
        wipers.append(pv)
    # The left blinker: on the driver's side front fender and the mirror.
    blink_m = reb.mat_emit("Blinker", (1.0, 0.5, 0.05), 40)
    reb.prim("cube", "Blinker lens", blink_m, (FX - 0.25, TY + 1.12, 1.32), (0.12, 0.1, 0.08))
    reb.prim("cube", "Blinker lens, mirror", blink_m, (CAB[1] + 0.12, TY + HW + 0.38, 2.78), (0.05, 0.1, 0.05))
    blink = reb.point("Blinker light", (FX - 0.05, TY + 1.25, 1.35), 30, (1.0, 0.5, 0.08), 0.05)
    # The headache rack behind the cab, the bunks and the logs, chained down.
    rack = reb.mat_metal("Rack steel", (0.08, 0.075, 0.07), 0.5)
    for s in (-1, 1):
        kit.rod("Rack post", rack, (12.5, TY + s * 1.15, 1.0), (12.5, TY + s * 1.15, 3.2), 0.05)
    kit.rod("Rack top", rack, (12.5, TY - 1.15, 3.2), (12.5, TY + 1.15, 3.2), 0.05)
    for z in (1.6, 2.2, 2.7):
        kit.rod("Rack bar", rack, (12.5, TY - 1.15, z), (12.5, TY + 1.15, z), 0.03)
    for bx in (11.0, 5.6):
        reb.prim("cube", "Bunk", rack, (bx, TY, 1.15), (0.25, 2.5, 0.2))
        for s in (-1, 1):
            kit.rod("Bunk stake", rack, (bx, TY + s * 1.2, 1.2), (bx, TY + s * 1.3, 2.7), 0.045)
    reb.prim("cube", "Reach pole", mat("iron"), (7.6, TY, 0.9), (5.0, 0.18, 0.18))
    reb.prim("cube", "Trailer frame", mat("iron"), (5.1, TY, 0.85), (1.8, 0.9, 0.25))
    logs_m = reb.mat_surface("Log bark", [(0.0, (0.05, 0.035, 0.025)), (0.6, (0.12, 0.085, 0.06)), (1.0, (0.18, 0.14, 0.1))], scale=6, bump=0.9)
    end_m = reb.mat_surface("Log ends", [(0.0, (0.28, 0.18, 0.09)), (0.7, (0.42, 0.3, 0.16)), (1.0, (0.2, 0.12, 0.06))], scale=12, bump=0.2)
    rows = [(4, 0.0), (3, 0.5), (2, 0.95)]
    for count, lift in rows:
        for k in range(count):
            y = TY + (k - (count - 1) / 2) * 0.58
            z = 1.53 + lift
            r = rng.uniform(0.26, 0.31)
            x0, x1 = TAIL + rng.uniform(0, 0.4), 12.25 - rng.uniform(0, 0.3)
            kit.rod("Log", logs_m, (x0, y, z), (x1, y, z), r, 12)
            for x in (x0 - 0.005, x1 + 0.005):
                reb.prim("cyl", "Log end", end_m, (x, y, z), (2 * r - 0.03, 2 * r - 0.03, 0.01), rot=(0, math.pi / 2, 0), segments=12)
    for cx in (6.8, 9.9):
        pts = [(cx, TY - 1.25, 1.2), (cx, TY - 1.15, 2.1), (cx, TY - 0.6, 2.75), (cx, TY + 0.6, 2.75), (cx, TY + 1.15, 2.1), (cx, TY + 1.25, 1.2)]
        for a, b in zip(pts, pts[1:]):
            kit.rod("Binder chain", mat("iron"), a, b, 0.018, 5)
    # She can't walk through the truck; the cab and logs can stand in front of her.
    reb.wall(reb.prim("cube", "Truck footprint", None, ((TAIL + FX) / 2, TY, 1.0), (FX - TAIL + 0.1, 2.5, 2.0))).hide_render = True
    for ob in bpy.data.objects:
        if ob.name.startswith(("Log", "Hood", "Bumper", "Front fender", "Fuel tank", "Grille")) and ob.type == "MESH" and not ob.name.startswith("Log end"):
            reb.mask(ob)

    # ---- His lunch in the mud below the door, his blood by the wheel, his prints going east.
    lx, ly = 13.4, TY + 2.0
    pail = reb.mat_plain("Lunch pail", (0.02, 0.025, 0.03), 0.4)
    reb.prim("cube", "Lunch pail", pail, (lx, ly, 0.06), (0.32, 0.2, 0.16), rot=(0.2, 0, 0.5))
    reb.prim("cyl", "Pail lid, open", pail, (lx - 0.1, ly + 0.2, 0.08), (0.32, 0.2, 0.32), rot=(math.pi / 2, 0.3, 0.5 + math.pi / 2), segments=12)
    reb.prim("cyl", "Thermos", reb.mat_stripes("Thermos plaid", [(0.35, 0.05, 0.03), (0.05, 0.08, 0.04)], across=30, axis="Z"), (lx + 0.75, ly + 0.4, 0.06), (0.11, 0.11, 0.34), rot=(math.pi / 2, 0, 0.3), segments=12)
    reb.prim("cyl", "Thermos cup", mat("steel"), (lx + 0.5, ly - 0.25, 0.04), (0.1, 0.1, 0.08), rot=(math.pi / 2, 0, 1.2), segments=10)
    bread = reb.mat_plain("Bread", (0.45, 0.35, 0.2), 0.9)
    for k in range(2):
        reb.prim("cube", "Sandwich", bread, (lx - 0.35 + k * 0.08, ly - 0.15 + k * 0.03, 0.02 + k * 0.02), (0.12, 0.12, 0.025), rot=(0.1 * k, 0, 0.3 + k))
    reb.prim("sphere", "Apple", reb.mat_plain("Apple red", (0.3, 0.03, 0.02), 0.5), (lx + 0.2, ly + 0.55, 0.04), (0.08, 0.08, 0.08), segments=10)
    kit.papers("Wax paper", (lx - 0.2, ly + 0.15, 0.0), spread=0.3, count=2, seed=3, m=reb.mat_plain("Wax paper", (0.55, 0.52, 0.45), 0.4))
    kit.splat("Coughed up by the wheel", mat("blood"), (15.0, TY + 1.7, height(15.0, TY + 1.7) + 0.01), 0.3, seed=71, stretch=(1.4, 0.9))
    kit.splat("Coughed up, older", mat("old blood"), (15.2, TY + 1.9, height(15.0, TY + 1.9) + 0.008), 0.45, seed=72, stretch=(1.3, 1.0))
    kit.splat("His hand in the mud", mat("old blood"), (14.2, TY + 1.5, height(14.2, TY + 1.5) + 0.012), 0.07, seed=73)
    cap = reb.mat_plain("Cap", (0.08, 0.15, 0.08), 0.8)
    reb.prim("sphere", "His cap", cap, (14.6, TY + 2.4, 0.04), (0.2, 0.17, 0.08), segments=12)
    reb.prim("cube", "Cap peak", cap, (14.7, TY + 2.52, 0.01), (0.12, 0.1, 0.01), rot=(0, 0, 0.4))
    # The prints: a boot, and the other foot dragged, east toward the camp.
    pv, pf = [], []
    x, y = 14.4, TY + 1.5
    k = 0
    while x < X1 + 2:
        foot = k % 2
        yy = y + (0.14 if foot else -0.14) + rng.uniform(-0.05, 0.05)
        zz = height(x, yy) + 0.012
        if foot:
            kit._stain(pv, pf, rng, (x, yy, zz), 0.07, 0.0, 0.25, (2.6, 0.8), k, points=10, drops=False)
        else:
            kit._stain(pv, pf, rng, (x, yy, zz), 0.07, 0.1, 0.2, (1.6, 0.8), k, points=10, drops=False)
        x += rng.uniform(0.32, 0.4)
        y += rng.uniform(-0.06, 0.04) - (0.04 if x > 16 else 0.0)
        k += 1
    reb.mesh_object("His prints east", pv, pf, reb.mat_plain("Bootprints", (0.02, 0.014, 0.009), 0.4), smooth=False)
    for k in range(5):
        x = 15.6 + k * 0.7
        kit.splat(f"Drip on the way {k}", mat("old blood"), (x, TY + 1.4 - k * 0.05, height(x, TY + 1.4) + 0.014), 0.05, seed=80 + k)

    # ---- The spruces on the verges, the notice on one of them.
    cv, cf = [], []
    for x, y in STANDING:
        h = rng.uniform(15, 19)
        base = Vector((x, y, height(x, y) - 0.15))
        spruce_crown(rng, base, h, cv, cf, rng.uniform(4.0, 5.2))
        r = h * 0.027
        t = reb.prim("cone", "Spruce", mat("bark"), (x, y, base.z + h * 0.45), (2 * r, 2 * r, h * 0.9), segments=9, top=0.25)
        reb.mask(reb.wall(t, "circle"))
    reb.mesh_object("Spruce crowns", cv, cf, mat("needles"))
    nx, ny = NOTICE_TREE
    face_x = nx - 0.47     # on the west face of the trunk, read by anyone coming from the woods
    notice_m = reb.mat_surface("Notice paper", [(0.0, (0.45, 0.43, 0.36)), (1.0, (0.6, 0.58, 0.5))], scale=12, bump=0.05)
    west = (math.pi / 2, 0, -math.pi / 2)
    reb.prim("cube", "Notice", notice_m, (face_x, ny, 1.65), (0.01, 0.62, 0.48))
    kit.text("Notice head", "QUARANTINE", mat("red paint"), (face_x - 0.008, ny, 1.8), size=0.11, rot=west)
    kit.text("Notice words", "SICKNESS IN CAMP 4", mat("black"), (face_x - 0.008, ny, 1.65), size=0.055, rot=west)
    kit.text("Notice words 2", "NO ENTRY  TURN BACK", mat("black"), (face_x - 0.008, ny, 1.56), size=0.05, rot=west)
    for dy in (-0.28, 0.28):
        reb.prim("cyl", "Nail", mat("iron"), (face_x - 0.01, ny + dy, 1.87), (0.012, 0.012, 0.03), rot=(0, math.pi / 2, 0), segments=6)
    # The torn half hangs from one nail and moves; the rest is in the grass.
    flap_pin = reb.prim("sphere", "Flap pin", mat("iron"), (face_x - 0.015, ny + 0.28, 1.42), (0.015, 0.015, 0.015), segments=6)
    flap = reb.prim("cube", "Torn flap", notice_m, (-0.15, 0.0, -0.18), (0.32, 0.008, 0.38), rot=(0, 0.35, 0))
    flap.parent = flap_pin
    flap_pin.rotation_euler = (0, 0, math.pi / 2)
    kit.papers("Torn notice in the grass", (nx - 0.9, ny + 1.3, height(nx - 0.9, ny + 1.3)), spread=0.4, count=2, seed=9, m=notice_m)

    # ---- A sign for the camp at the east, the forest round it all.
    kit.rod("Camp sign post", mat("dark wood"), (16.6, 5.6, -0.1), (16.6, 5.6, 2.0), 0.06)
    reb.prim("cube", "Camp sign", mat("planks"), (16.6, 5.64, 1.75), (1.3, 0.05, 0.32))
    kit.text("Camp sign words", "CAMP 4  >", mat("white paint"), (16.6, 5.67, 1.75), size=0.17, rot=(math.pi / 2, 0, math.pi))
    cams = ((1.4, 4.6), (1.6, 11.4), (18.4, 11.4), (13.4, 4.6), (2.6, 5.0))

    def keep_out(x, y):
        if X0 - 1.0 < x < X1 + 1.0 and Y0 - 0.8 < y < Y1 + 0.8:
            return True
        if abs(y - TY) < 1.8:
            return True
        return any((x - cx) ** 2 + (y - cy) ** 2 < 9 for cx, cy in cams)
    kit.forest(rng, height, keep_out, (-16, -14, 36, 30), count=130, spacing=1.7, tall=(13, 22), ferns=180, needles=1200, dead=0.1)
    far_m = reb.mat_surface("Far spruce", [(0.0, (0.015, 0.03, 0.018)), (1.0, (0.04, 0.07, 0.035))], scale=0.6, bump=0.3)
    fv, ff = [], []
    placed = 0
    while placed < 300:
        x, y = rng.uniform(-55, 75), rng.uniform(-55, 75)
        if (-16 < x < 36 and -14 < y < 30) or abs(y - TY) < 2.0:
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
    xv, xf = [], []
    for _ in range(40):
        x, y = rng.uniform(X0, X1), rng.choice((rng.uniform(Y0, TY - 2.2), rng.uniform(TY + 2.4, Y1)))
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.6), xv, xf)
    ferns = reb.mesh_object("Ferns on the verges", xv, xf, mat("ferns"))

    # ---- Light: noon under cloud, the road a pale strip under it, mist down the road.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.0, mist=((10.0, 8.0, 5.0), (80.0, 80.0, 16.0), 0.012),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.1))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(28)

    anim = kit.Anim(16)
    anim.blink(blink, blink_m, on=(0, 4))
    anim.blink(reb.point("Blinker light, mirror", (CAB[1] + 0.2, TY + HW + 0.5, 2.78), 6, (1.0, 0.5, 0.08), 0.03), None, on=(0, 4))
    twitch = [0, 0, 0, 0, 0, 0.55, 0.3, 0, 0, 0, 0, 0, 0.4, 0.15, 0, 0]

    def wipe(k):
        for i, w in enumerate(wipers):
            w.rotation_euler = (-1.2 + twitch[(k + i) % 16], 0, 0)
    anim.custom(wipe)
    anim.swing(flap_pin, axis=1, degrees=14)
    anim.flies((13.2, TY + 0.6, 1.7), count=7, radius=0.3)
    anim.flies((15.1, TY + 1.8, 0.05), count=8, radius=0.4)
    anim.sway(grass, amount=0.06)
    anim.sway(ferns, amount=0.02)

    # ---- What the game needs.
    room.door("woods", (X0, 6.4, X0 + 0.6, 10.0), arrive=(2.6, TY), face=(1, 0))
    room.door("camp-gate", (X1 - 0.6, 6.2, X1, 11.0), arrive=(17.3, 10.6), face=(-1, 0))
    room.check((nx - 1.3, Y0, nx + 0.3, Y0 + 0.8), "QUARANTINE. SICKNESS IN CAMP 4. NO ENTRY. TURN BACK.\nThe bottom half's torn off.")
    room.check((DOOR[0] - 0.3, TY + HW, DOOR[1] + 0.4, TY + HW + 1.0), "The driver's door is wide open. Blood on the seat, and down the step.\nScratches on the inside of the door.")
    room.check((lx - 0.6, ly - 0.5, lx + 1.0, ly + 0.8), "His lunch, in the mud. He never got to eat it.")
    room.check((14.7, TY + 1.4, 15.8, TY + 2.3), "Blood in the mud by the wheel. He was coughing it up.")
    room.check((15.8, TY + 1.0, 17.6, TY + 2.0), "Bootprints, going east. One foot dragging.\nHe walked toward the camp.")
    room.check((FX - 0.1, TY - 1.3, FX + 0.6, TY + 1.3), "The battery's nearly flat. The blinker's still going.\nThe keys are gone from the ignition.")
    room.check((TAIL - 0.8, TY - 1.2, TAIL, TY + 1.2), "A full load of logs, for the mill. It never got there.")
    room.entry = "A logging truck, stopped dead in the ruts."
    room.export(anim)


build()
