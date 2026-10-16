"""The forestry road west of Ranger Station 3, afternoon.

What it tells: this is Forest Road 7, the road the rangers drive up to the
station. The steel gate across it was chained and locked at six last night;
the ranger's own check sheet says so, on the clipboard he dropped in the
gravel by the gatepost, its pages blowing into the ditch. The chain is
still round the gate's end and the latch post, padlocked: she cuts it with
the bolt cutters (day/events.ts has no event for it: the gate is a lock,
scripts.ts). On his way up the ranger's truck skidded and hit something
short of the gate: blood and a tuft of grey fur on the gravel, a broken
headlamp's glass. Dog prints in the mud of the ditch, big ones, come down
out of the trees and cross the road. The forest sign is shot full of holes,
and someone has pasted a notice on the gatepost (the county closing the
Arklay area after the hiker killings) that the wind has half torn away.
Crows sit on the sign.

Metres: the floor is x 8.3-19, y 3.5-10.5, east of the gate. The gravel
road runs east-west, y 5-9, with grass verges and ditches either side; the
forest climbs to the north and falls away to the south. The gate is at x 8:
its latch post on the north verge at y 4.3, its hinge post on the south
verge at y 9.7, the gate shut across the road, chained to the latch post.
The forest sign stands on the north verge at x 10-12, facing east. East
(x 19) the road runs on to the ranger station's yard; west, through the
gate, on to the washout: the way is the gate itself.

State "cut-chain" (the lock's flag): the chain drops off the latch post and
the gate swings open west against the south verge, played as it happens.

Moving: the torn notice flapping on the gatepost, dust in the low sun, the
grass, a crow on the sign.
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

X0, X1, Y0, Y1 = 8.3, 19.0, 3.5, 10.5
WEST = 1.0                    # the road and its verges go on past the gate as far as this, and the scenery past that
ROAD = (5.0, 9.0)
GATE_X = 8.0
LATCH = (GATE_X, 4.3)
HINGE = (GATE_X, 9.7)
SIGN = (11.0, 3.3)
CAMS = [(18.6, 9.6, 3.4), (1.6, 4.0, 3.3), (10.2, 3.9, 3.0), (14.2, 10.3, 2.9), (10.4, 10.2, 2.4)]


def height(x, y):
    """The road flat, ditches along it, the slope up north and down south."""
    h = 0.0
    if Y0 - 0.2 < y < Y1 + 0.2:
        # The ditches just off the floor's edges.
        for e in (Y0 - 0.6, Y1 + 0.6):
            d = abs(y - e)
            if d < 0.6:
                h -= 0.35 * (1 - d / 0.6)
        return h
    h = 0.4 * noise.noise(Vector((x * 0.12, y * 0.12, 4)))
    if y < Y0 - 0.2:
        h += (Y0 - 0.2 - y) * 0.55
        for e in (Y0 - 0.6,):
            d = abs(y - e)
            if d < 0.6:
                h -= 0.35 * (1 - d / 0.6)
    if y > Y1 + 0.2:
        h -= (y - Y1 - 0.2) * 0.45
        d = abs(y - (Y1 + 0.6))
        if d < 0.6:
            h -= 0.35 * (1 - d / 0.6)
    return h


def low_sun(heading, elevation, energy, rgb=(1.0, 0.7, 0.42)):
    """The afternoon sun low in the south-west: long shadows, warm light."""
    sun = kit.time_light("afternoon", sun_heading=heading, sun_energy=energy,
                         mist=((10, 7, 3), (70, 50, 12), 0.005))
    sun.rotation_euler[0] = math.radians(90 - elevation)
    sun.data.color = rgb
    bpy.context.view_layer.update()
    kit._sky((0.86, 0.64, 0.44), (0.3, 0.38, 0.56), 0.8, sun)
    return sun


def dust(rng, area, count, z=(0.4, 2.8), name="Dust"):
    """Motes hanging in the sun: tiny specks in one mesh, which drift. None
    within 4 m of a camera, where they would turn into blobs."""
    m = reb.mat_emit(f"{name} motes", (1.0, 0.82, 0.55), 0.8)
    v, f = [], []
    for _ in range(count * 3):
        if len(f) >= count * 4:
            break
        c = Vector((rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3]), rng.uniform(*z)))
        if any((c - Vector(e)).length < 4.0 for e in CAMS):
            continue
        s = rng.uniform(0.004, 0.007)
        k = len(v)
        v += [tuple(c + Vector((s, 0, 0))), tuple(c + Vector((-s, s, 0))), tuple(c + Vector((-s, -s, 0))), tuple(c + Vector((0, 0, s * 1.5)))]
        f += [(k, k + 1, k + 2), (k, k + 1, k + 3), (k + 1, k + 2, k + 3), (k, k + 2, k + 3)]
    return reb.mesh_object(name, v, f, m, smooth=False)


def chain(name, m, a, b, sag=0.15, links=12, r=0.012, size=1.0):
    """A chain of links hanging from a to b with a little sag: one object.
    `size` scales the links."""
    a, b = Vector(a), Vector(b)
    parts = []
    for i in range(links):
        t = (i + 0.5) / links
        p = a.lerp(b, t) - Vector((0, 0, sag * math.sin(math.pi * t)))
        d = (b - a).normalized()
        ob = reb.prim("cube", "link", m, p, tuple(size * v for v in ((0.05, 0.012, 0.03) if i % 2 else (0.05, 0.03, 0.012))), rot=(0, 0, math.atan2(d.y, d.x)))
        parts.append(ob)
    return kit.join(name, parts)


def build():
    rng = random.Random(7)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("gravel")  # the road
    room.floor((X0, Y0, X1, ROAD[0]), "earth")  # the verges
    room.floor((X0, ROAD[1], X1, Y1), "earth")
    room.camera(CAMS[0], (8.5, 6.4, 0.6), 200, "from the east end, the way she comes: the road west, the sign, the chained gate")
    room.camera(CAMS[1], (11.0, 8.2, 0.5), 200, "from beyond the gate in the west: the gate's back, the torn notice, the road east")
    room.camera(CAMS[2], (6.5, 8.2, 0.2), 205, "from the north verge by the sign: the latch post, the chain, the clipboard")
    room.camera(CAMS[3], (8.0, 4.6, 0.6), 200, "from the south verge east of the gate: the sign with its crows, the latch post")
    room.camera(CAMS[4], (7.6, 4.6, 0.6), 200, "from the south verge by the hinge post: along the gate to its chain on the latch post, the road on west through the bars")

    gravel = reb.mat_surface("Road gravel", [(0.0, (0.1, 0.085, 0.065)), (0.45, (0.2, 0.18, 0.15)), (0.75, (0.27, 0.24, 0.2)), (1.0, (0.17, 0.13, 0.09))], scale=14, bump=1.0)
    gravel = kit.dirtied(gravel, 0.6, scale=0.5)
    rut = reb.mat_surface("Ruts", [(0.0, (0.07, 0.055, 0.04)), (1.0, (0.14, 0.11, 0.08))], scale=10, rough=0.7, bump=0.6)
    yellow = reb.mat_surface("Gate yellow", [(0.0, (0.3, 0.2, 0.02)), (0.7, (0.5, 0.34, 0.03)), (1.0, (0.25, 0.1, 0.03))], scale=6, rough=0.55, bump=0.15)
    sign_brown = reb.mat_surface("Sign brown", [(0.0, (0.1, 0.055, 0.025)), (1.0, (0.17, 0.095, 0.045))], scale=4, rough=0.7, bump=0.2)
    letters = reb.mat_plain("Sign letters", (0.7, 0.6, 0.35), 0.6)
    fur = reb.mat_surface("Grey fur", [(0.0, (0.08, 0.07, 0.06)), (1.0, (0.22, 0.2, 0.18))], scale=40, bump=0.4)
    dried = reb.mat_surface("Dried blood", [(0.0, (0.035, 0.006, 0.004)), (1.0, (0.09, 0.02, 0.012))], scale=12, rough=0.9, bump=0.3)
    tyre = reb.mat_surface("Tyre tracks", [(0.0, (0.03, 0.022, 0.015)), (1.0, (0.07, 0.05, 0.035))], scale=30, rough=0.6, bump=0.8)
    notice_m = reb.mat_plain("Notice", (0.6, 0.58, 0.48), 0.9)

    # ---- Ground: the gravel road, its verges and ditches, the forest slope.
    reb.terrain("Ground", mat("grass"), (-22, 42), (-16, 32), height, step=0.5)
    v, f = [], []
    for i in range(int((X1 - WEST + 30) / 0.5)):
        xa, xb = WEST - 15 + i * 0.5, WEST - 15 + (i + 1) * 0.5
        w0 = 0.15 * noise.noise(Vector((xa * 0.3, 2, 0)))
        w1 = 0.15 * noise.noise(Vector((xb * 0.3, 2, 0)))
        k = len(v)
        v += [(xa, ROAD[0] - w0, height(xa, ROAD[0]) + 0.012), (xb, ROAD[0] - w1, height(xb, ROAD[0]) + 0.012),
              (xb, ROAD[1] + w1, height(xb, ROAD[1]) + 0.012), (xa, ROAD[1] + w0, height(xa, ROAD[1]) + 0.012)]
        f.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Gravel road", v, f, gravel)
    # The old ruts, through the gate and on.
    for y in (6.1, 7.9):
        kit.path_strip("Old rut", rut, [(WEST - 15, y), (X1 + 15, y)], height, width=0.22, wobble=0.25, lift=0.02)
    # Where the ranger's truck skidded on its way up: a black arc, then the
    # blood and fur of whatever it hit, dragged off into the ditch.
    kit.path_strip("Skid", reb.mat_plain("Skid", (0.015, 0.013, 0.012), 0.7), [(13.6, 5.8), (12.6, 6.2), (11.7, 6.9)], height, width=0.08, wobble=0.1, lift=0.035)
    kit.path_strip("Skid", reb.mat_plain("Skid", (0.015, 0.013, 0.012), 0.7), [(13.6, 7.4), (12.6, 7.8), (11.7, 8.5)], height, width=0.08, wobble=0.1, lift=0.035)
    kit.drag_trail("Blood on the road", dried, [(10.8, 7.6), (10.2, 8.2), (9.8, 9.0), (9.4, 10.2)], width=0.35, seed=4, z=0.04)
    kit.splat("Blood where it hit", dried, (11.0, 7.4, 0.04), 0.3, seed=6, stretch=(1.6, 0.9))
    for i in range(4):
        reb.cloth(f"Tuft of fur {i}", fur, (10.7 + rng.uniform(-0.5, 0.5), 7.5 + rng.uniform(-0.4, 0.4), 0.04), (0.12, 0.08), rot=(0, 0, rng.uniform(0, 3)), cuts=6, lumps=0.03, seed=i)
    kit.shards("Headlamp glass", (11.3, 7.1, 0.03), spread=0.5, count=10, seed=3)
    # Dog prints down out of the trees, over the road, into the trees south.
    for i in range(14):
        t = i / 13
        x = 15.5 - 2.2 * t + 0.25 * math.sin(i * 1.3)
        y = 3.3 + 7.6 * t
        kit.splat(f"Paw print {i}", mat("mud"), (x + (0.1 if i % 2 else -0.1), y, height(x, y) + 0.04), 0.05, seed=80 + i, stretch=(1.0, 1.2), lumps=0.3)
    # Puddles in the low spots of the gravel.
    for i, (x, y, r) in enumerate(((13.0, 6.1, 0.3), (16.5, 7.9, 0.22), (6.0, 7.9, 0.25))):
        kit.splat(f"Puddle {i}", reb.mat_plain("Puddle", (0.05, 0.05, 0.05), 0.08), (x, y, 0.025), r, seed=60 + i, stretch=(1.8, 0.7), lumps=0.3)

    # ---- The gate: two posts, the yellow pipe leaf shut across the road, chained to the latch post.
    for name, (x, y) in (("Latch post", LATCH), ("Hinge post", HINGE)):
        p = kit.rod(name, yellow, (x, y, -0.3), (x, y, 1.25), 0.07, 12)
        reb.wall(p, "circle")
        reb.mask(p)
        reb.prim("cyl", f"{name} cap", yellow, (x, y, 1.27), (0.17, 0.17, 0.04), segments=12)
    leaf_len = HINGE[1] - LATCH[1] - 0.2
    hinge = reb.prim("sphere", "Gate hinge", mat("iron"), (HINGE[0], HINGE[1], 0.95), (0.08, 0.08, 0.08))
    parts = [
        kit.rod("Top rail", yellow, (0, 0, 0.1), (0, -leaf_len, 0.1), 0.045, 10),
        kit.rod("Bottom rail", yellow, (0, 0, -0.55), (0, -leaf_len, -0.55), 0.035, 10),
        kit.rod("Brace", yellow, (0, -0.1, -0.55), (0, -leaf_len * 0.6, 0.1), 0.03, 8),
        kit.rod("Brace", yellow, (0, -leaf_len * 0.6, 0.1), (0, -leaf_len + 0.1, -0.55), 0.03, 8),
    ]
    for t in (0.0, 0.3, 0.6, 1.0):
        parts.append(kit.rod("Upright", yellow, (0, -leaf_len * t, -0.55), (0, -leaf_len * t, 0.1), 0.03, 8))
    leaf = kit.join("Gate leaf", parts)
    leaf.parent = hinge
    plate = reb.prim("cube", "Closed plate", mat("white paint"), (0.05, -leaf_len * 0.45, -0.22), (0.02, 0.9, 0.36))
    plate.parent = hinge
    kit.text("Closed words", "ROAD CLOSED", mat("red paint"), (0.07, -leaf_len * 0.45, -0.22), size=0.13, rot=(math.pi / 2, 0, math.pi / 2)).parent = hinge
    bpy.context.view_layer.update()
    # Its footprint shut across the road. It stays a wall once the gate is
    # open: the way west is the gate's own zone (room.door), which she
    # reaches first.
    lw = reb.prim("cube", "Gate leaf footprint", None, (GATE_X, (LATCH[1] + HINGE[1]) / 2, 0.5), (0.25, HINGE[1] - LATCH[1], 1.0))
    lw.hide_render = True
    reb.wall(lw)
    # The chain round the latch post and the leaf's end, padlocked: heavy,
    # bright steel, so it reads from across the road.
    end = (GATE_X, LATCH[1] + 0.2)
    wrap = [chain(f"Chain round the post {i}", mat("steel"), (LATCH[0] - 0.1, LATCH[1] + 0.02, z), (end[0] + 0.09, end[1] + 0.02, z - 0.04), sag=0.01, links=5, size=1.8) for i, z in enumerate((1.02, 0.9))]
    chain_tail = chain("Chain's tail", mat("steel"), (end[0] + 0.09, end[1], 0.88), (end[0] + 0.12, end[1] + 0.06, 0.5), sag=0.01, links=6, size=1.8)
    padlock = reb.prim("cube", "Padlock", reb.mat_metal("Padlock brass", (0.55, 0.4, 0.15), 0.35), (end[0] + 0.12, end[1] + 0.06, 0.42), (0.11, 0.05, 0.13), bevel=0.015)
    chain_parts = wrap + [chain_tail, padlock]
    rests = [(ob.location.copy(), ob.rotation_euler.copy()) for ob in chain_parts]

    def cut_chain(t):
        """t 0: chained shut; to 0.3 the cut chain slides off the post and
        drops in the grass; then the gate swings open west to the verge."""
        t = float(t)
        fall = min(1.0, t / 0.3)
        for k, (ob, (loc, rot)) in enumerate(zip(chain_parts, rests)):
            drop = fall * fall
            ob.location = loc + Vector((0.12 * drop * (1 + 0.3 * k), 0.15 * drop, -(loc.z - 0.04) * drop))
            ob.rotation_euler = (rot.x + 1.3 * drop * (1 if k % 2 else -1), rot.y + 0.4 * drop, rot.z + 0.6 * drop * k)
        swing = max(0.0, (t - 0.3) / 0.7)
        swing = swing * swing * (3 - 2 * swing)
        hinge.rotation_euler = (0, 0, math.radians(-96) * swing)
    room.state("cut-chain", cut_chain, motion=(12, 4))
    # The torn notice on the latch post: one corner still stapled, the rest flapping.
    pin = reb.prim("sphere", "Notice staple", mat("steel"), (LATCH[0] + 0.075, LATCH[1], 1.12), (0.015, 0.015, 0.015))
    flap = reb.prim("cube", "Torn notice", notice_m, (0.02, 0.0, -0.16), (0.004, 0.22, 0.3))
    flap.parent = pin
    kit.text("Notice words", "NOTICE", mat("black"), (0.025, 0.0, -0.05), size=0.05, rot=(math.pi / 2, 0, math.pi / 2)).parent = pin
    for i in range(4):
        reb.prim("cube", f"Notice line {i}", mat("black"), (0.025, 0.0, -0.12 - i * 0.045), (0.002, 0.16, 0.012)).parent = pin
    pin.rotation_euler = (0, 0, 0.3)
    reb.prim("cube", "Notice scrap", notice_m, (LATCH[0] + 0.075, LATCH[1] - 0.04, 0.98), (0.004, 0.08, 0.1), rot=(0.2, 0, 0))
    papers_blown = kit.papers("Torn half in the grass", (LATCH[0] - 1.6, LATCH[1] - 0.2, height(LATCH[0] - 1.6, LATCH[1] - 0.2)), spread=0.2, count=1, seed=8, m=notice_m)
    papers_blown.rotation_euler = (0.2, 0.1, 0.4)
    # Fence wire on from both posts into the trees, so the gate is the only way.
    for (x, y), dy in ((LATCH, -1), (HINGE, 1)):
        for k in range(3):
            ya, yb = y + dy * (0.2 + k * 1.2), y + dy * (1.4 + k * 1.2)
            post = kit.rod("Fence post", mat("dark wood"), (x, yb, height(x, yb) - 0.2), (x, yb, height(x, yb) + 1.1), 0.05)
        for z in (0.45, 0.85):
            kit.rod("Fence wire", mat("iron"), (x, y, z), (x, y + dy * 3.8, height(x, y + dy * 3.8) + z), 0.006, 4)
    reb.wall(reb.prim("cube", "North fence", None, (GATE_X, (Y0 + LATCH[1]) / 2 - 0.5, 0.5), (0.2, LATCH[1] - Y0 + 1.0, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "South fence", None, (GATE_X, (HINGE[1] + Y1) / 2 + 0.5, 0.5), (0.2, Y1 - HINGE[1] + 1.0, 1.0))).hide_render = True

    # ---- The forest sign on the north verge, facing east, shot full of holes.
    sx, sy = SIGN
    for dy in (-0.95, 0.95):
        post = kit.rod("Sign post", mat("dark wood"), (sx, sy + dy, height(sx, sy + dy) - 0.3), (sx, sy + dy, 2.3), 0.07)
        reb.wall(post, "circle")
    board = reb.prim("cube", "Forest sign", sign_brown, (sx + 0.08, sy, 1.75), (0.07, 2.4, 0.95), bevel=0.02)
    reb.mask(board)
    kit.text("Sign words", "ARKLAY", letters, (sx + 0.12, sy, 1.98), size=0.3, rot=(math.pi / 2, 0, math.pi / 2))
    kit.text("Sign words 2", "NATIONAL FOREST", letters, (sx + 0.12, sy, 1.66), size=0.2, rot=(math.pi / 2, 0, math.pi / 2))
    kit.text("Sign words 3", "FOREST ROAD 7", letters, (sx + 0.12, sy, 1.43), size=0.1, rot=(math.pi / 2, 0, math.pi / 2))
    for i in range(9):
        y = sy + rng.uniform(-1.0, 1.0)
        z = 1.75 + rng.uniform(-0.4, 0.4)
        reb.prim("cyl", f"Bullet hole {i}", mat("black"), (sx + 0.12, y, z), (0.03, 0.03, 0.01), rot=(0, math.pi / 2, 0), segments=8)
        reb.prim("cyl", f"Bullet ring {i}", mat("steel"), (sx + 0.118, y, z), (0.05, 0.05, 0.008), rot=(0, math.pi / 2, 0), segments=8)
    # Crows along the top of the sign.
    crows = []
    for i, (dy, hd) in enumerate(((-0.8, 0.3), (-0.1, 3.0), (0.7, 1.4))):
        b, w = kit.crow(f"Crow on the sign {i}", (sx + 0.08, sy + dy, 2.23), heading=hd)
        crows.append(b)
    # A milepost and a stack of cut logs on the south verge, east of the gate.
    kit.rod("Milepost", mat("white paint"), (16.0, 10.2, -0.2), (16.0, 10.2, 1.1), 0.06, 4)
    kit.text("Milepost words", "7", mat("black"), (16.0, 10.14, 0.95), size=0.12, rot=(math.pi / 2, 0, 0))
    logs = []
    for i, (dy, z) in enumerate(((0.0, 0.2), (0.42, 0.2), (0.84, 0.2), (0.21, 0.56), (0.63, 0.56), (0.42, 0.92))):
        logs.append(kit.rod("Log", mat("logs"), (12.2, 10.6 + dy, z - 0.02), (15.4, 10.6 + dy, z - 0.02), 0.2, 12))
    stack = kit.join("Log stack", logs)
    reb.wall(stack)
    reb.prim("cube", "Log ends", mat("pine"), (15.42, 11.02, 0.5), (0.02, 1.2, 0.9))

    # ---- The ranger's clipboard by the latch post, pages blowing off into the ditch; his torch.
    cx, cy = LATCH[0] + 1.0, LATCH[1] + 1.7
    reb.prim("cube", "Clipboard", mat("dark wood"), (cx, cy, height(cx, cy) + 0.02), (0.24, 0.33, 0.012), rot=(0.05, 0, 0.6))
    reb.prim("cube", "Check sheet", mat("paper"), (cx, cy, height(cx, cy) + 0.03), (0.21, 0.28, 0.002), rot=(0.05, 0, 0.6))
    reb.prim("cube", "Clip", mat("steel"), (cx - 0.07, cy - 0.11, height(cx, cy) + 0.035), (0.08, 0.03, 0.012), rot=(0.05, 0, 0.6))
    kit.papers("Pages blowing", (cx - 1.0, cy - 0.9, height(cx - 1.0, cy - 0.9)), spread=1.2, count=5, seed=2)
    reb.prim("cyl", "Torch", mat("black"), (cx + 0.9, Y0 - 0.45, height(cx + 0.9, Y0 - 0.45) + 0.05), (0.06, 0.06, 0.28), rot=(math.pi / 2, 0, 1.2), segments=12)
    reb.prim("cyl", "Torch lens", mat("glass"), (cx + 0.78, Y0 - 0.39, height(cx + 0.78, Y0 - 0.39) + 0.05), (0.07, 0.07, 0.02), rot=(math.pi / 2, 0, 1.2), segments=12)
    reb.prim("cyl", "Ranger's hat", mat("khaki"), (9.6, Y1 - 0.3, height(9.6, Y1 - 0.3) + 0.04), (0.42, 0.42, 0.04), rot=(0.25, 0.1, 0), segments=16)
    reb.prim("cyl", "Hat crown", mat("khaki"), (9.61, Y1 - 0.33, height(9.6, Y1 - 0.3) + 0.11), (0.2, 0.2, 0.12), rot=(0.25, 0.1, 0), segments=12)

    # ---- The forest both sides: spruces up the slope, some dead; grass and ferns on the verges.
    def keep_out(x, y):
        return (WEST - 25 < x < X1 + 25 and Y0 - 1.6 < y < Y1 + 1.4) or any((Vector((x, y)) - Vector(c[:2])).length < 4.0 for c in CAMS)
    kit.forest(rng, height, keep_out, (-20, -14, 40, 30), count=95, spacing=1.7, ferns=40, needles=900, dead=0.1)
    # A few trees right at the verge, so the road runs through forest, not a field.
    near = []
    for x, y in ((2.5, 0.0), (15.0, 1.8), (21.5, 12.5), (10.0, 12.0), (0.5, 12.2), (6.0, 1.9)):
        near.append((Vector((x, y, height(x, y) - 0.2)), rng.uniform(13, 17)))
    nv, nf = [], []
    for base, hh in near:
        reb.conifer(rng, base, hh, nv, nf)
    reb.mesh_object("Verge spruces", nv, nf, mat("needles"))
    reb.trunks("Verge trunks", mat("bark"), near)

    def verge(r):
        while True:
            x, y = r.uniform(WEST - 10, X1 + 10), r.uniform(Y0 - 3, Y1 + 3)
            if not (ROAD[0] + 0.1 < y < ROAD[1] - 0.1):
                return x, y
    grass = kit.meadow(rng, 2200, verge, height)
    kit.meadow(rng, 160, lambda r: (r.uniform(WEST - 5, X1 + 5), r.choice((7.0, 6.95, 7.05)) + r.uniform(-0.25, 0.25)), height, mat("dead grass"))
    rv, rf = [], []
    for (x, y, r) in ((1.5, 2.0, 0.7), (17.8, 2.3, 0.9), (12.0, 12.6, 0.6), (-2.0, 11.5, 1.0), (9.3, 2.6, 0.5)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Rocks", rv, rf, mat("rock"))

    # ---- Light: the low sun through the trees from the south-west, dust hanging in it.
    low_sun(232, 21, 6.0)
    motes = dust(rng, (WEST, Y0, X1, Y1), 90)
    motes2 = dust(rng, (WEST, Y0, X1, Y1), 70, name="Dust, far")

    anim = kit.Anim(16)
    anim.custom(lambda k: setattr(pin, "rotation_euler", (0.25 * math.sin(anim.phase(k, 2)), 0.1 * math.sin(anim.phase(k)), 0.3 + 0.6 * math.sin(anim.phase(k)) + 0.2 * math.sin(anim.phase(k, 3)))))
    anim.custom(lambda k: setattr(motes, "location", (0.25 * math.sin(anim.phase(k)), 0.1 * math.cos(anim.phase(k)), 0.06 * math.sin(anim.phase(k, 2)))))
    anim.custom(lambda k: setattr(motes2, "location", (-0.2 * math.cos(anim.phase(k)), 0.15 * math.sin(anim.phase(k)), -0.05 * math.cos(anim.phase(k, 2)))))
    anim.sway(grass, amount=0.05)
    anim.bob(crows[1], height=0.04, speed=2)

    # ---- What the game needs.
    room.door("yard", (X1 - 0.6, ROAD[0], X1, ROAD[1]), arrive=(17.4, 7.0), face=(-1, 0))
    # The way west is the gate, locked by its chain until she cuts it (scripts.ts).
    room.door("washout", (X0, ROAD[0], X0 + 0.6, ROAD[1]), arrive=(9.6, 7.0), face=(1, 0))
    room.check((X0, LATCH[1], X0 + 0.9, ROAD[0]), "GATE 7. A steel chain round the gate and its post,\nand a padlock on it.")
    room.check((cx - 0.5, cy - 0.5, cx + 0.5, cy + 0.5), "A ranger's clipboard. The check sheet: GATE 7, CHAINED AND LOCKED, 23 JUL, 18.00.\nHe never came back for it.")
    room.check((X0, Y0, X0 + 0.9, LATCH[1]), "A county notice, torn half away.\n...ARKLAY AREA CLOSED UNTIL FURTHER... ...HIKERS... ...DO NOT APPROACH...")
    room.check((sx, Y0, sx + 0.9, sy + 1.2), "ARKLAY NATIONAL FOREST. FOREST ROAD 7.\nSomeone's used it for target practice.")
    room.check((10.2, 6.8, 11.8, 8.0), "Glass from a headlamp, and blood. Grey fur.\nSomething big ran out in front of a truck here.")
    room.check((12.8, 3.5, 15.6, 10.5), "Paw prints, crossing the road. Big ones.\nThe dogs came down this way.")
    room.check((9.0, Y1 - 0.8, 10.2, Y1), "A ranger's hat, in the ditch.")
    room.entry = "The forestry road. The gate's chained shut."
    room.export(anim)


build()
